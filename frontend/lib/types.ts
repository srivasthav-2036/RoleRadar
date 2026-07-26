// ─── Shared TypeScript Types for RoleRadar ───────────────────────────────────

export interface User {
  user_id: string;
  email: string;
  name: string | null;
  email_notifications: boolean;
}

// Job card list item (lean, from GET /api/recommendations/)
export interface Recommendation {
  job_id: string;
  title: string;
  company: string;
  location: string | null;
  apply_url: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  experience_required: string | null;
  employment_type: string | null;
  score: number;
  overall_match: string | null; // "Excellent Match" | "Good Match" | "Average Match" | "Weak Match"
  matched_skills: string[];
  missing_skills: string[];
  has_tailored_resume: boolean;
}

// Full detail for the drawer (from GET /api/recommendations/{job_id})
export interface RecommendationDetail {
  job_id: string;
  title: string;
  company: string;
  description: string | null;
  location: string | null;
  apply_url: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  experience_required: string | null;
  education_required: string | null;
  employment_type: string | null;
  score: number;
  has_tailored_resume: boolean;
  // AI match breakdown — read directly from backend, never recomputed
  overall_match: string | null;
  skill_score: number | null;
  project_score: number | null;
  experience_score: number | null;
  education_score: number | null;
  certificate_bonus: number | null;
  experience_match: string | null;
  education_match: string | null;
  project_match: string | null;
  certificate_match: string | null;
  matched_required_skills: string[];
  matched_preferred_skills: string[];
  matched_skills: string[];
  missing_skills: string[];
  recommendation: string | null;
}

export interface ActivityEvent {
  event_type:
    | "resume_analyzed"
    | "search_queries_generated"
    | "jobs_fetched"
    | "recommendations_updated"
    | "email_sent";
  detail: Record<string, unknown> | null;
  created_at: string; // ISO datetime string
}

export interface PipelineRun {
  started_at: string;
  finished_at: string;
  next_scheduled_at: string;
  jobs_fetched: number;
  jobs_parsed: number;
  users_processed: number;
  recommendations_created: number;
  emails_sent: number;
}

export interface DashboardStats {
  new_matches_today: number;
  avg_match_score: number | null;
  resume_strength: number | null;
  applications_this_week: number | null;
  emails_sent: number;
  jobs_fetched_today: number | null;
  last_sync: string | null;
  next_sync: string | null;
}

export interface SkillFrequency {
  skill: string;
  count: number;
}

export interface ResumeData {
  name: string | null;
  resume: {
    summary?: string;
    skills?: Record<string, string[]> | string[];
    experience?: Array<{
      company?: string;
      role?: string;
      duration?: string;
      description?: string;
    }>;
    projects?: Array<{
      title?: string;
      description?: string;
      technologies?: string[];
    }>;
    education?: Array<{
      institution?: string;
      degree?: string;
      year?: string;
    }>;
    certifications?: Array<string | Record<string, string>>;
    achievements?: Array<string | Record<string, string>>;
    languages?: string[];
    preferred_roles?: string[];
    domains?: string[];
  };
  queries: string[];
}
