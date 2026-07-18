"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Sparkles,
  ExternalLink,
  AlertCircle,
  Loader2,
  Download,
  TriangleAlert,
  FileCheck2,
  X,
} from "lucide-react";
import { tailoringApi, recommendationsApi, ApiError } from "@/lib/api";
import type { Recommendation } from "@/lib/types";
import { MatchDial } from "@/components/match-dial";
import { PipelineStatusBanner } from "@/components/pipeline-status-banner";

// ─── Error message mapper ──────────────────────────────────────────────────────

function mapTailoringError(err: unknown): string {
  if (err instanceof ApiError) {
    const detail = err.detail.toLowerCase();
    if (
      err.status === 429 ||
      detail.includes("quota") ||
      detail.includes("limit") ||
      detail.includes("free tier") ||
      detail.includes("exceeded") ||
      detail.includes("rate")
    ) {
      return "The AI service is temporarily unavailable. It may have reached its free-tier limit. Please contact the owner at roleradar.notifications@gmail.com.";
    }
    if (
      err.status === 503 ||
      err.status === 530 ||
      detail.includes("traffic") ||
      detail.includes("demand") ||
      detail.includes("busy") ||
      detail.includes("overloaded") ||
      detail.includes("unavailable")
    ) {
      return "The AI model is currently experiencing high demand. Please try again in a few minutes.";
    }
    return "Unable to generate your tailored resume. Please contact the owner at roleradar.notifications@gmail.com.";
  }
  return "Unable to generate your tailored resume. Please contact the owner at roleradar.notifications@gmail.com.";
}

// ─── Toast notification ───────────────────────────────────────────────────────

function ErrorToast({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  // Auto-dismiss after 8 seconds
  useEffect(() => {
    const t = setTimeout(onDismiss, 8000);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return (
    <div className="fixed bottom-6 left-1/2 z-[200] w-[92vw] max-w-lg -translate-x-1/2 animate-slide-up">
      <div className="flex items-start gap-3 rounded-xl border border-danger/25 bg-white px-5 py-4 shadow-2xl dark:bg-[#1a1a1a]">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-danger/10">
          <AlertCircle className="h-4 w-4 text-danger" />
        </div>
        <div className="flex-1">
          <p className="text-[13px] font-medium text-ink dark:text-ink-dark">
            Generation Failed
          </p>
          <p className="mt-1 text-[12.5px] leading-relaxed text-muted dark:text-muted-dark">
            {message}
          </p>
        </div>
        <button
          onClick={onDismiss}
          className="shrink-0 rounded-md p-1 text-muted transition-colors hover:text-ink dark:text-muted-dark dark:hover:text-ink-dark"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

// ─── Centered loading modal ────────────────────────────────────────────────────

function GeneratingModal({
  message,
  sub,
  status = "loading",
  url,
  onClose,
}: {
  message: string;
  sub: string;
  status?: "loading" | "blocked";
  url?: string;
  onClose?: () => void;
}) {
  return (
    <div className="fixed inset-0 z-[150] flex items-center justify-center bg-paper/70 backdrop-blur-sm dark:bg-paper-dark/70">
      <div className="flex w-80 flex-col items-center gap-5 rounded-2xl border border-line bg-surface px-8 py-8 shadow-2xl dark:border-line-dark dark:bg-surface-dark">
        {status === "loading" ? (
          <>
            {/* Spinner with pulse ring */}
            <div className="relative flex h-16 w-16 items-center justify-center">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal/15" />
              <div className="relative flex h-12 w-12 items-center justify-center rounded-full border border-signal/20 bg-signal-soft dark:bg-signal-soft-dark">
                <Loader2 className="h-6 w-6 animate-spin text-signal" />
              </div>
            </div>
            <div className="text-center">
              <p className="font-display text-[15px] font-medium text-ink dark:text-ink-dark">
                {message}
              </p>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted dark:text-muted-dark">
                {sub}
              </p>
            </div>
          </>
        ) : (
          <>
            {/* Pop-up Blocked State */}
            <div className="relative flex h-16 w-16 items-center justify-center">
              <div className="relative flex h-12 w-12 items-center justify-center rounded-full border border-amber-300 bg-amber-50 dark:border-amber-700/50 dark:bg-amber-900/10">
                <AlertCircle className="h-6 w-6 text-amber-500" />
              </div>
            </div>
            <div className="text-center">
              <p className="font-display text-[15px] font-medium text-ink dark:text-ink-dark">
                Pop-up Blocked
              </p>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted dark:text-muted-dark">
                Your tailored resume has been generated, but your browser blocked the new tab.
              </p>
            </div>
            <div className="flex w-full flex-col gap-2">
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={onClose}
                className="flex items-center justify-center gap-1.5 rounded-full bg-ink py-2 text-[12.5px] font-medium text-paper transition-colors hover:bg-ink/85 dark:bg-ink-dark dark:text-paper-dark"
              >
                Open Preview
                <ExternalLink className="h-3 w-3" />
              </a>
              <button
                onClick={onClose}
                className="rounded-full border border-line py-2 text-[12.5px] text-muted hover:border-ink/30 hover:text-ink dark:border-line-dark dark:text-muted-dark dark:hover:text-ink-dark"
              >
                Close
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Tailored job row ─────────────────────────────────────────────────────────

function TailoredJobRow({
  job,
  onPreview,
  onDownload,
  previewing,
  downloading,
  disabled,
}: {
  job: Recommendation;
  onPreview: (job: Recommendation) => void;
  onDownload: (job: Recommendation) => void;
  previewing: boolean;
  downloading: boolean;
  disabled: boolean;
}) {
  const busy = previewing || downloading;

  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-line bg-surface p-4 transition-shadow hover:shadow-card dark:border-line-dark dark:bg-surface-dark">
      <div className="flex items-center gap-3 min-w-0">
        <MatchDial score={job.score} size="sm" />
        <div className="min-w-0">
          <p className="truncate font-display text-[14px] font-medium text-ink dark:text-ink-dark">
            {job.title}
          </p>
          <p className="text-[12.5px] text-muted dark:text-muted-dark">
            {job.company}
          </p>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        {/* Preview — opens HTML in new tab */}
        <button
          onClick={() => onPreview(job)}
          disabled={disabled || busy}
          title="Preview tailored resume in new tab"
          className="flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-[12.5px] text-muted transition-colors hover:border-ink/30 hover:text-ink disabled:cursor-not-allowed disabled:opacity-40 dark:border-line-dark dark:text-muted-dark dark:hover:border-ink-dark/30 dark:hover:text-ink-dark"
        >
          {previewing ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <FileCheck2 className="h-3 w-3" />
          )}
          Preview
        </button>

        {/* Download PDF */}
        <button
          onClick={() => onDownload(job)}
          disabled={disabled || busy}
          title="Download tailored resume as PDF"
          className="flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-[12.5px] text-muted transition-colors hover:border-ink/30 hover:text-ink disabled:cursor-not-allowed disabled:opacity-40 dark:border-line-dark dark:text-muted-dark dark:hover:border-ink-dark/30 dark:hover:text-ink-dark"
        >
          {downloading ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Download className="h-3 w-3" />
          )}
          Download
        </button>

        {job.apply_url && (
          <a
            href={job.apply_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg bg-ink px-3 py-1.5 text-[12.5px] font-medium text-paper transition-colors hover:bg-ink/85 dark:bg-ink-dark dark:text-paper-dark"
          >
            Apply
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function TailoredPage() {
  const [jobs, setJobs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Preview state tracking generating vs pop-up blocked
  const [previewState, setPreviewState] = useState<{
    status: "idle" | "generating" | "blocked";
    jobId: string | null;
    url?: string;
  }>({ status: "idle", jobId: null });

  // Which job is actively being downloaded
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  // Toast error
  const [toastError, setToastError] = useState<string | null>(null);

  // Refs to store job data between preview and download calls
  const previewDataRef = useRef<Record<string, Record<string, unknown>>>({});

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { recommendations } = await recommendationsApi.list();
      setJobs(recommendations);
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setJobs([]);
      } else {
        setError(err instanceof ApiError ? err.detail : "Failed to load recommendations.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // ── Build filename from name + company ───────────────────────────────────────
  function buildFilename(
    name: string | undefined | null,
    company: string,
    ext: "pdf" | "html"
  ): string {
    const safe = (s: string) =>
      s.trim().replace(/[^a-zA-Z0-9]/g, "_").replace(/_+/g, "_");
    const namePart = name ? safe(name) : "resume";
    const companyPart = safe(company);
    return `${namePart}_${companyPart}_resume.${ext}`;
  }

  // ── Preview: generate tailored resume → open HTML preview in new tab ────────
  async function handlePreview(job: Recommendation) {
    setPreviewState({ status: "generating", jobId: job.job_id });
    setToastError(null);
    try {
      const token = localStorage.getItem("rr_token");
      const apiBase =
        process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

      // 1. Call the JSON endpoint first to trigger and wait for LLM tailoring
      const res = await fetch(
        `${apiBase}/api/tailoring/preview/${job.job_id}`,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );

      if (!res.ok) {
        let detail = "Failed to generate preview";
        try {
          const data = await res.json();
          if (data.detail) detail = data.detail;
        } catch {}
        throw new ApiError(res.status, detail);
      }

      const { tailored_resume } = await res.json();
      previewDataRef.current[job.job_id] = tailored_resume; // Cache the data locally for PDF download

      // 2. Build the authenticated direct HTML URL
      const previewUrl = `${apiBase}/api/tailoring/preview/${job.job_id}/html?token=${token}`;

      // 3. Attempt to automatically open the preview in a new tab
      const newTab = window.open(previewUrl, "_blank");

      if (!newTab || newTab.closed || typeof newTab.closed === "undefined") {
        // Pop-up was blocked. Transition to blocked state to show inline link.
        setPreviewState({
          status: "blocked",
          jobId: job.job_id,
          url: previewUrl,
        });
      } else {
        // Success
        setPreviewState({ status: "idle", jobId: null });
      }
    } catch (err) {
      setToastError(mapTailoringError(err));
      setPreviewState({ status: "idle", jobId: null });
    }
  }

  // ── Download PDF ─────────────────────────────────────────────────────────────
  async function handleDownload(job: Recommendation) {
    setDownloadingId(job.job_id);
    setToastError(null);
    try {
      // First, get the JSON resume if not already cached
      let resumeData = previewDataRef.current[job.job_id];
      if (!resumeData) {
        const { tailored_resume } = await tailoringApi.preview(job.job_id);
        resumeData = tailored_resume;
        previewDataRef.current[job.job_id] = tailored_resume;
      }

      const blob = await tailoringApi.downloadPdf(resumeData);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = buildFilename(
        (resumeData as { name?: string })?.name,
        job.company,
        "pdf"
      );
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setToastError(mapTailoringError(err));
    } finally {
      setDownloadingId(null);
    }
  }

  const anyBusy = previewState.status !== "idle" || downloadingId !== null;

  return (
    <div className="h-screen overflow-y-auto px-6 py-8 md:px-10 md:py-10">
      <div className="mx-auto max-w-3xl">
        <PipelineStatusBanner onComplete={fetchJobs} />
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-line bg-surface dark:border-line-dark dark:bg-surface-dark">
              <Sparkles className="h-4 w-4 text-signal" />
            </div>
            <h1 className="font-display text-[1.4rem] font-medium tracking-tight text-ink dark:text-ink-dark">
              Your Matches
            </h1>
          </div>
          <p className="mt-2 text-[13.5px] text-muted dark:text-muted-dark">
            Preview or download an AI-tailored version of your resume for any matched role.
          </p>
        </div>

        {/* AI disclaimer banner */}
        <div className="mb-6 flex items-start gap-2.5 rounded-xl border border-amber-200/60 bg-amber-50/60 px-4 py-3 dark:border-amber-500/20 dark:bg-amber-900/10">
          <TriangleAlert className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
          <p className="text-[12.5px] leading-snug text-amber-700 dark:text-amber-300">
            Tailored resumes are generated by AI. Always review carefully before applying.
          </p>
        </div>

        {/* Loading list */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="h-6 w-6 animate-spin text-muted dark:text-muted-dark" />
            <p className="mt-3 text-[13px] text-muted dark:text-muted-dark">
              Loading recommendations…
            </p>
          </div>
        )}

        {/* List-level error */}
        {!loading && error && (
          <div className="flex items-center gap-2 rounded-xl border border-danger/20 bg-danger/5 px-5 py-4">
            <AlertCircle className="h-5 w-5 shrink-0 text-danger" />
            <p className="text-[13.5px] text-danger">{error}</p>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && jobs.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-line bg-paper px-6 py-16 text-center dark:border-line-dark dark:bg-paper-dark">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-line bg-surface dark:border-line-dark dark:bg-surface-dark">
              <Sparkles className="h-5 w-5 text-muted dark:text-muted-dark" />
            </div>
            <p className="font-display text-[16px] font-medium text-ink dark:text-ink-dark">
              No recommendations yet
            </p>
            <p className="mt-1.5 max-w-xs text-[13.5px] leading-relaxed text-muted dark:text-muted-dark">
              Upload your resume to start the pipeline and receive matched jobs.
            </p>
            <a
              href="/dashboard/resume"
              className="mt-5 rounded-full bg-ink px-5 py-2.5 text-[13px] font-medium text-paper transition-colors hover:bg-ink/85 dark:bg-ink-dark dark:text-paper-dark"
            >
              Upload resume
            </a>
          </div>
        )}

        {/* Job list */}
        {!loading && !error && jobs.length > 0 && (
          <div className="space-y-3">
            {jobs.map((job) => (
              <TailoredJobRow
                key={job.job_id}
                job={job}
                onPreview={handlePreview}
                onDownload={handleDownload}
                previewing={previewState.jobId === job.job_id && previewState.status === "generating"}
                downloading={downloadingId === job.job_id}
                disabled={anyBusy && previewState.jobId !== job.job_id && downloadingId !== job.job_id}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── Centered generating modal ──────────────────────────────────────────── */}
      {previewState.status !== "idle" && (
        <GeneratingModal
          message="Generating your tailored resume…"
          sub="This usually takes a few seconds."
          status={previewState.status === "blocked" ? "blocked" : "loading"}
          url={previewState.url}
          onClose={() => setPreviewState({ status: "idle", jobId: null })}
        />
      )}
      {downloadingId && (
        <GeneratingModal
          message="Preparing your PDF…"
          sub="Rendering your resume to a professional layout."
        />
      )}

      {/* ── Toast error ─────────────────────────────────────────────────────────── */}
      {toastError && (
        <ErrorToast message={toastError} onDismiss={() => setToastError(null)} />
      )}

      {/* Slide-up animation */}
      <style>{`
        @keyframes slide-up {
          from { opacity: 0; transform: translate(-50%, 12px); }
          to   { opacity: 1; transform: translate(-50%, 0); }
        }
        .animate-slide-up { animation: slide-up 0.25s ease-out both; }
      `}</style>
    </div>
  );
}
