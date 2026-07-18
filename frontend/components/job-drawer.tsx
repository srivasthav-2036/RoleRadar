"use client";

import { useEffect, useState } from "react";
import {
  X,
  ExternalLink,
  MapPin,
  Briefcase,
  GraduationCap,
  Loader2,
  CheckCircle2,
  XCircle,
  Minus,
  AlertCircle,
} from "lucide-react";
import { recommendationsApi, ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Recommendation, RecommendationDetail } from "@/lib/types";
import { SkeletonDrawer } from "./skeleton";

interface JobDrawerProps {
  job: Recommendation | null;
  onClose: () => void;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function MatchBadgeLarge({ match }: { match: string | null }) {
  if (!match) return null;
  const cfg: Record<string, { cls: string; icon: typeof CheckCircle2 }> = {
    Excellent: { cls: "border-signal/30 bg-signal-soft text-signal dark:bg-signal-soft-dark", icon: CheckCircle2 },
    Good: { cls: "border-blue-200/50 bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300", icon: CheckCircle2 },
    Fair: { cls: "border-yellow-200/50 bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-300", icon: AlertCircle },
    Poor: { cls: "border-line bg-paper text-muted dark:border-line-dark dark:bg-paper-dark dark:text-muted-dark", icon: XCircle },
  };
  const { cls, icon: Icon } = cfg[match] ?? cfg.Fair;
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[12.5px] font-medium", cls)}>
      <Icon className="h-3.5 w-3.5" />
      {match} Match
    </span>
  );
}

function ScoreBar({ label, score }: { label: string; score: number | null }) {
  const pct = score == null ? null : Math.round(Math.min(100, Math.max(0, score)));
  const color =
    pct == null
      ? "bg-line dark:bg-line-dark"
      : pct >= 80
      ? "bg-signal"
      : pct >= 60
      ? "bg-blue-500"
      : pct >= 40
      ? "bg-yellow-500"
      : "bg-danger";

  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-[12.5px]">
        <span className="text-muted dark:text-muted-dark">{label}</span>
        <span className="font-mono text-ink dark:text-ink-dark">
          {pct == null ? "—" : pct}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-line dark:bg-line-dark">
        <div
          className={cn("h-full rounded-full transition-all duration-700", color)}
          style={{ width: pct == null ? "0%" : `${pct}%` }}
        />
      </div>
    </div>
  );
}

function VerdictBadge({ label, verdict }: { label: string; verdict: string | null }) {
  if (!verdict) return null;
  const lower = verdict.toLowerCase();
  const isPositive = lower.includes("strong") || lower.includes("exact") || lower.includes("match");
  const isPartial = lower.includes("partial") || lower.includes("close");
  const Icon = isPositive ? CheckCircle2 : isPartial ? Minus : XCircle;
  const cls = isPositive
    ? "text-signal bg-signal-soft border-signal/20 dark:bg-signal-soft-dark"
    : isPartial
    ? "text-yellow-700 bg-yellow-50 border-yellow-200/50 dark:text-yellow-300 dark:bg-yellow-900/20"
    : "text-muted bg-paper border-line dark:bg-paper-dark dark:border-line-dark dark:text-muted-dark";

  return (
    <div className={cn("flex items-center gap-2 rounded-lg border px-3 py-2", cls)}>
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <div className="min-w-0">
        <p className="text-[10.5px] font-medium uppercase tracking-[0.1em] opacity-70">{label}</p>
        <p className="text-[12.5px]">{verdict}</p>
      </div>
    </div>
  );
}

function formatSalary(
  min: number | null,
  max: number | null,
  currency: string | null
) {
  if (!min && !max) return null;
  const sym = currency === "INR" ? "₹" : currency === "USD" ? "$" : (currency ?? "");
  const fmt = (n: number) =>
    n >= 100000
      ? `${sym}${(n / 100000).toFixed(n % 100000 === 0 ? 0 : 1)}L`
      : n >= 1000
      ? `${sym}${(n / 1000).toFixed(0)}k`
      : `${sym}${n}`;
  if (min && max) return `${fmt(min)} – ${fmt(max)} / year`;
  if (min) return `From ${fmt(min)} / year`;
  return `Up to ${fmt(max!)} / year`;
}

// ─── Drawer ───────────────────────────────────────────────────────────────────

export function JobDrawer({ job, onClose }: JobDrawerProps) {
  const [detail, setDetail] = useState<RecommendationDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isOpen = job !== null;

  // Fetch full detail when job changes
  useEffect(() => {
    if (!job) {
      setDetail(null);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    recommendationsApi
      .detail(job.job_id)
      .then((d) => {
        setDetail(d);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.detail : "Failed to load details.");
        setLoading(false);
      });
  }, [job]);

  // Close on Escape
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  // Lock body scroll when open
  useEffect(() => {
    document.body.style.overflow = isOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [isOpen]);

  if (!job) return null;

  const salary = detail
    ? formatSalary(detail.salary_min, detail.salary_max, detail.salary_currency)
    : null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-ink/30 backdrop-blur-sm dark:bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Job details: ${job.title}`}
        className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[900px] flex-col bg-surface shadow-[−24px_0_80px_rgba(0,0,0,0.12)] dark:bg-surface-dark"
        style={{ animation: "slideInRight 0.3s cubic-bezier(0.16,1,0.3,1)" }}
      >
        {/* Drawer header */}
        <div className="flex items-center justify-between border-b border-line px-6 py-4 dark:border-line-dark">
          <div className="flex items-center gap-3">
            <div>
              <p className="font-display text-[15px] font-medium text-ink dark:text-ink-dark">
                {job.title}
              </p>
              <p className="text-[13px] text-muted dark:text-muted-dark">{job.company}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {detail?.apply_url && (
              <a
                href={detail.apply_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 rounded-lg bg-ink px-4 py-2 text-[13px] font-medium text-paper transition-colors hover:bg-ink/85 dark:bg-ink-dark dark:text-paper-dark"
              >
                Apply
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
            <button
              onClick={onClose}
              aria-label="Close drawer"
              className="flex h-8 w-8 items-center justify-center rounded-full border border-line text-muted transition-colors hover:border-ink/30 hover:text-ink dark:border-line-dark dark:text-muted-dark dark:hover:text-ink-dark"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Drawer body */}
        <div className="flex-1 overflow-y-auto">
          {loading && (
            <div className="flex h-full items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted dark:text-muted-dark" />
            </div>
          )}

          {error && (
            <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center">
              <AlertCircle className="h-8 w-8 text-danger/60" />
              <p className="text-[14px] text-muted dark:text-muted-dark">{error}</p>
            </div>
          )}

          {!loading && !error && detail && (
            <div className="grid gap-0 lg:grid-cols-[1fr_320px]">
              {/* ── Left: Job info ── */}
              <div className="border-b border-line px-6 py-6 lg:border-b-0 lg:border-r dark:border-line-dark">
                {/* Meta */}
                <div className="flex flex-wrap gap-2">
                  {detail.location && (
                    <span className="flex items-center gap-1.5 rounded border border-line px-2.5 py-1 text-[12.5px] text-muted dark:border-line-dark dark:text-muted-dark">
                      <MapPin className="h-3 w-3" />
                      {detail.location}
                    </span>
                  )}
                  {detail.employment_type && (
                    <span className="flex items-center gap-1.5 rounded border border-line px-2.5 py-1 text-[12.5px] text-muted dark:border-line-dark dark:text-muted-dark">
                      <Briefcase className="h-3 w-3" />
                      {detail.employment_type}
                    </span>
                  )}
                  {detail.education_required && (
                    <span className="flex items-center gap-1.5 rounded border border-line px-2.5 py-1 text-[12.5px] text-muted dark:border-line-dark dark:text-muted-dark">
                      <GraduationCap className="h-3 w-3" />
                      {detail.education_required}
                    </span>
                  )}
                  {detail.experience_required && (
                    <span className="rounded border border-line px-2.5 py-1 text-[12.5px] text-muted dark:border-line-dark dark:text-muted-dark">
                      {detail.experience_required}
                    </span>
                  )}
                </div>

                {/* Salary */}
                {salary && (
                  <div className="mt-4 rounded-lg border border-signal/20 bg-signal-soft px-4 py-3 dark:bg-signal-soft-dark">
                    <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-signal">
                      Compensation
                    </p>
                    <p className="mt-0.5 font-display text-[18px] font-medium text-ink dark:text-ink-dark">
                      {salary}
                    </p>
                  </div>
                )}

                {/* Description */}
                {detail.description ? (
                  <div className="mt-6">
                    <p className="mb-3 font-mono text-[10.5px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
                      About the role
                    </p>
                    <div className="prose-sm text-[13.5px] leading-relaxed text-ink dark:text-ink-dark">
                      {detail.description.split("\n").map((para, i) =>
                        para.trim() ? (
                          <p key={i} className="mb-2">
                            {para}
                          </p>
                        ) : null
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="mt-6 rounded-lg border border-line bg-paper px-4 py-6 text-center dark:border-line-dark dark:bg-paper-dark">
                    <p className="text-[13px] text-muted dark:text-muted-dark">
                      No job description available.
                    </p>
                  </div>
                )}
              </div>

              {/* ── Right: AI Match Breakdown ── */}
              <div className="px-6 py-6">
                <p className="mb-4 font-mono text-[10.5px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
                  AI Match Breakdown
                </p>

                {/* Overall match */}
                <MatchBadgeLarge match={detail.overall_match} />

                {/* Score bars */}
                <div className="mt-5 space-y-3.5">
                  <ScoreBar label="Skill score" score={detail.skill_score} />
                  <ScoreBar label="Experience score" score={detail.experience_score} />
                  <ScoreBar label="Education score" score={detail.education_score} />
                  <ScoreBar label="Project score" score={detail.project_score} />
                  {detail.certificate_bonus !== null &&
                    detail.certificate_bonus !== undefined && (
                      <ScoreBar label="Certificate bonus" score={detail.certificate_bonus} />
                    )}
                </div>

                {/* Verdicts */}
                {(detail.experience_match || detail.education_match ||
                  detail.project_match || detail.certificate_match) && (
                  <div className="mt-5 space-y-2">
                    <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.12em] text-muted dark:text-muted-dark">
                      Verdicts
                    </p>
                    {detail.experience_match && (
                      <VerdictBadge label="Experience" verdict={detail.experience_match} />
                    )}
                    {detail.education_match && (
                      <VerdictBadge label="Education" verdict={detail.education_match} />
                    )}
                    {detail.project_match && (
                      <VerdictBadge label="Projects" verdict={detail.project_match} />
                    )}
                    {detail.certificate_match && (
                      <VerdictBadge label="Certificates" verdict={detail.certificate_match} />
                    )}
                  </div>
                )}

                {/* Matched skills */}
                {detail.matched_skills.length > 0 && (
                  <div className="mt-5">
                    <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.12em] text-muted dark:text-muted-dark">
                      Matched skills
                    </p>
                    {detail.matched_required_skills.length > 0 && (
                      <>
                        <p className="mb-1.5 text-[11px] text-muted dark:text-muted-dark">Required</p>
                        <div className="mb-2 flex flex-wrap gap-1.5">
                          {detail.matched_required_skills.map((s) => (
                            <span
                              key={s}
                              className="rounded-md border border-signal/25 bg-signal-soft px-2 py-[3px] text-[11.5px] text-ink dark:border-signal/20 dark:bg-signal-soft-dark dark:text-ink-dark"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </>
                    )}
                    {detail.matched_preferred_skills.length > 0 && (
                      <>
                        <p className="mb-1.5 text-[11px] text-muted dark:text-muted-dark">Preferred</p>
                        <div className="flex flex-wrap gap-1.5">
                          {detail.matched_preferred_skills.map((s) => (
                            <span
                              key={s}
                              className="rounded-md border border-blue-200/60 bg-blue-50 px-2 py-[3px] text-[11.5px] text-blue-700 dark:border-blue-500/20 dark:bg-blue-900/15 dark:text-blue-300"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                )}

                {/* Missing skills */}
                {detail.missing_skills.length > 0 && (
                  <div className="mt-5">
                    <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.12em] text-muted dark:text-muted-dark">
                      Missing skills
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {detail.missing_skills.map((s) => (
                        <span
                          key={s}
                          className="rounded-md border border-danger/20 bg-danger/5 px-2 py-[3px] text-[11.5px] text-danger"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI Recommendation */}
                {detail.recommendation && (
                  <div className="mt-5 rounded-lg border border-line bg-paper p-4 dark:border-line-dark dark:bg-paper-dark">
                    <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.12em] text-signal">
                      AI Recommendation
                    </p>
                    <p className="text-[13px] leading-relaxed text-ink dark:text-ink-dark">
                      {detail.recommendation}
                    </p>
                  </div>
                )}

                {/* Apply button at bottom of right panel */}
                {detail.apply_url && (
                  <a
                    href={detail.apply_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-6 flex w-full items-center justify-center gap-1.5 rounded-lg bg-ink py-2.5 text-[13px] font-medium text-paper transition-colors hover:bg-ink/85 dark:bg-ink-dark dark:text-paper-dark"
                  >
                    Apply now
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Skeleton while loading */}
          {loading && <SkeletonDrawer />}
        </div>
      </div>

    </>
  );
}
