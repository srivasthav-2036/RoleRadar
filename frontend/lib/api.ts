// ─── Central API Client ───────────────────────────────────────────────────────
// All API calls go through this module.
// Token is read from localStorage (set by AuthContext after login/register).
// On 401, the token is cleared and the user is redirected to /login.

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("rr_token");
}

export function clearToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("rr_token");
    localStorage.removeItem("rr_user");
  }
}

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("rr_token", token);
  }
}

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  authenticated = true
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (authenticated) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401 && authenticated) {
    clearToken();
    if (typeof window !== "undefined") {
      const path = window.location.pathname;
      if (path !== "/login" && path !== "/register" && path !== "/forgot-password") {
        window.location.href = "/login";
      }
    }
    throw new ApiError(401, "Session expired. Please log in again.");
  }

  let data: unknown;
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    data = await res.json();
  } else {
    data = await res.text();
  }

  if (!res.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? String((data as { detail: string }).detail)
        : res.statusText;
    throw new ApiError(res.status, detail);
  }

  return data as T;
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string }>(
      "/api/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) },
      false
    ),

  register: (email: string, password: string) =>
    request<{ access_token: string; token_type: string }>(
      "/api/auth/register",
      { method: "POST", body: JSON.stringify({ email, password }) },
      false
    ),

  sendOtp: (email: string) =>
    request<{ message: string }>(
      "/api/auth/send-otp",
      { method: "POST", body: JSON.stringify({ email }) },
      false
    ),

  resendOtp: (email: string) =>
    request<{ message: string }>(
      "/api/auth/resend-otp",
      { method: "POST", body: JSON.stringify({ email }) },
      false
    ),

  verifyOtp: (email: string, otp: string, password: string) =>
    request<{ access_token: string; token_type: string }>(
      "/api/auth/verify-otp",
      { method: "POST", body: JSON.stringify({ email, otp, password }) },
      false
    ),

  me: () =>
    request<{ user_id: string; email: string; name: string | null; email_notifications: boolean }>(
      "/api/auth/me"
    ),

  setNotifications: (enabled: boolean) =>
    request<{ email_notifications: boolean }>(
      "/api/auth/me/notifications",
      { method: "PATCH", body: JSON.stringify({ enabled }) }
    ),
};

// ─── Recommendations ─────────────────────────────────────────────────────────

export const recommendationsApi = {
  list: () =>
    request<{ count: number; recommendations: import("./types").Recommendation[] }>(
      "/api/recommendations/"
    ),

  detail: (jobId: string) =>
    request<import("./types").RecommendationDetail>(
      `/api/recommendations/${jobId}`
    ),

  refresh: () =>
    request<{ new_count: number; new_recommendations: unknown[] }>(
      "/api/recommendations/refresh",
      { method: "POST" }
    ),
};

// ─── Dashboard ───────────────────────────────────────────────────────────────

export const dashboardApi = {
  stats: () =>
    request<import("./types").DashboardStats>("/api/dashboard/stats"),

  activity: () =>
    request<{ events: import("./types").ActivityEvent[] }>(
      "/api/dashboard/activity"
    ),

  skillFrequency: () =>
    request<{ skills: import("./types").SkillFrequency[] }>(
      "/api/dashboard/skill-frequency"
    ),
};

// ─── Resumes ─────────────────────────────────────────────────────────────────

export const resumesApi = {
  get: () =>
    request<import("./types").ResumeData | null>("/api/resumes/me"),

  upload: async (file: File, onProgress?: (pct: number) => void) => {
    const token = getToken();
    const formData = new FormData();
    formData.append("file", file);

    return new Promise<{
      resume_id: string;
      resume: import("./types").ResumeData["resume"];
      search_queries: string[];
    }>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE}/api/resumes/upload`);
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      };

      xhr.onload = () => {
        if (xhr.status === 401) {
          clearToken();
          window.location.href = "/login";
          reject(new ApiError(401, "Session expired."));
          return;
        }
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          let detail = xhr.statusText;
          try {
            const parsed = JSON.parse(xhr.responseText);
            if (parsed.detail) detail = parsed.detail;
          } catch {}
          reject(new ApiError(xhr.status, detail));
        }
      };

      xhr.onerror = () => reject(new ApiError(0, "Network error"));
      xhr.send(formData);
    });
  },

  delete: () =>
    request<{ deleted: boolean }>("/api/resumes/me", { method: "DELETE" }),

  pipelineStatus: () =>
    request<{ status: "idle" | "running" | "done"; step?: string }>(
      "/api/resumes/pipeline-status"
    ),
};


// ─── Tailoring ───────────────────────────────────────────────────────────────

export const tailoringApi = {
  preview: (jobId: string) =>
    request<{ tailored_resume: Record<string, unknown> }>(
      `/api/tailoring/preview/${jobId}`
    ),

  downloadPdf: async (tailoredResume: Record<string, unknown>): Promise<Blob> => {
    const token = getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/api/tailoring/pdf`, {
      method: "POST",
      headers,
      body: JSON.stringify({ tailored_resume: tailoredResume }),
    });

    if (!res.ok) {
      let detail = "Failed to download PDF";
      try {
        const data = await res.json();
        if (data.detail) detail = data.detail;
      } catch {}
      throw new ApiError(res.status, detail);
    }

    return await res.blob();
  },
};
