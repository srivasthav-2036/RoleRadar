"use client";

import { useState } from "react";
import { Bookmark, ExternalLink, MapPin, Briefcase, DollarSign, ChevronRight } from "lucide-react";
import { MatchDial } from "./match-dial";
import { cn } from "@/lib/utils";
import type { Recommendation } from "@/lib/types";

interface JobCardProps {
  job: Recommendation;
  onViewDetails: (job: Recommendation) => void;
}

function MatchBadge({ match }: { match: string | null }) {
  if (!match) return null;
  const variants: Record<string, string> = {
    Excellent:
      "border-signal/30 bg-signal-soft text-signal dark:bg-signal-soft-dark dark:text-signal-dark",
    Good: "border-blue-200/50 bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300",
    Fair: "border-yellow-200/50 bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-300",
    Poor: "border-line bg-paper text-muted dark:border-line-dark dark:bg-paper-dark dark:text-muted-dark",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.1em]",
        variants[match] ?? variants.Fair
      )}
    >
      {match}
    </span>
  );
}

function formatSalary(
  min: number | null,
  max: number | null,
  currency: string | null
): string | null {
  if (!min && !max) return null;
  const sym = currency === "INR" ? "₹" : currency === "USD" ? "$" : (currency ?? "");
  const fmt = (n: number) =>
    n >= 100000
      ? `${sym}${(n / 100000).toFixed(n % 100000 === 0 ? 0 : 1)}L`
      : n >= 1000
      ? `${sym}${(n / 1000).toFixed(0)}k`
      : `${sym}${n}`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  if (min) return `From ${fmt(min)}`;
  return `Up to ${fmt(max!)}`;
}

export function JobCard({ job, onViewDetails }: JobCardProps) {
  const [saved, setSaved] = useState(false);

  const salary = formatSalary(job.salary_min, job.salary_max, job.salary_currency);

  return (
    <div className="group relative flex flex-col rounded-xl2 border border-line bg-surface p-5 transition-shadow hover:shadow-card-hover dark:border-line-dark dark:bg-surface-dark">
      {/* Header: title + score */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="truncate font-display text-[15.5px] font-medium text-ink dark:text-ink-dark">
            {job.title}
          </p>
          <p className="mt-0.5 text-[13px] text-muted dark:text-muted-dark">
            {job.company}
          </p>
        </div>
        <MatchDial score={job.score} size="sm" />
      </div>

      {/* Match label + meta chips */}
      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        <MatchBadge match={job.overall_match} />
        {job.location && (
          <span className="flex items-center gap-1 rounded border border-line px-1.5 py-0.5 text-[11px] text-muted dark:border-line-dark dark:text-muted-dark">
            <MapPin className="h-2.5 w-2.5" />
            {job.location}
          </span>
        )}
        {job.employment_type && (
          <span className="flex items-center gap-1 rounded border border-line px-1.5 py-0.5 text-[11px] text-muted dark:border-line-dark dark:text-muted-dark">
            <Briefcase className="h-2.5 w-2.5" />
            {job.employment_type}
          </span>
        )}
        {salary && (
          <span className="flex items-center gap-1 rounded border border-line px-1.5 py-0.5 text-[11px] text-muted dark:border-line-dark dark:text-muted-dark">
            <DollarSign className="h-2.5 w-2.5" />
            {salary}
          </span>
        )}
        {job.experience_required && (
          <span className="rounded border border-line px-1.5 py-0.5 text-[11px] text-muted dark:border-line-dark dark:text-muted-dark">
            {job.experience_required}
          </span>
        )}
      </div>

      {/* Skills */}
      {(job.matched_skills.length > 0 || job.missing_skills.length > 0) && (
        <div className="mt-3.5 flex flex-wrap gap-1.5">
          {job.matched_skills.map((skill) => (
            <span
              key={skill}
              className="rounded-md border border-signal/25 bg-signal-soft px-2 py-[3px] text-[11.5px] text-ink dark:border-signal/20 dark:bg-signal-soft-dark dark:text-ink-dark"
            >
              {skill}
            </span>
          ))}
          {job.missing_skills.map((skill) => (
            <span
              key={skill}
              className="rounded-md border border-line px-2 py-[3px] text-[11.5px] text-muted line-through decoration-muted/40 dark:border-line-dark dark:text-muted-dark"
            >
              {skill}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="mt-5 flex items-center gap-2">
        {/* Apply */}
        {job.apply_url ? (
          <a
            href={job.apply_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-ink py-2 text-[13px] font-medium text-paper transition-colors hover:bg-ink/85 dark:bg-ink-dark dark:text-paper-dark dark:hover:bg-ink-dark/85"
          >
            Apply
            <ExternalLink className="h-3 w-3" />
          </a>
        ) : (
          <button
            disabled
            className="flex-1 cursor-not-allowed rounded-lg border border-line py-2 text-[13px] font-medium text-muted dark:border-line-dark dark:text-muted-dark"
          >
            Apply
          </button>
        )}

        {/* View Details */}
        <button
          onClick={() => onViewDetails(job)}
          className="flex items-center gap-1 rounded-lg border border-line px-3 py-2 text-[13px] text-muted transition-colors hover:border-ink/30 hover:text-ink dark:border-line-dark dark:text-muted-dark dark:hover:border-ink-dark/30 dark:hover:text-ink-dark"
        >
          Details
          <ChevronRight className="h-3 w-3" />
        </button>

        {/* Save */}
        <button
          onClick={() => setSaved((v) => !v)}
          aria-label={saved ? "Unsave job" : "Save job"}
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-lg border transition-colors",
            saved
              ? "border-signal/30 bg-signal-soft text-signal dark:bg-signal-soft-dark"
              : "border-line text-muted hover:border-ink/30 hover:text-ink dark:border-line-dark dark:text-muted-dark dark:hover:border-ink-dark/30 dark:hover:text-ink-dark"
          )}
        >
          <Bookmark className="h-3.5 w-3.5" strokeWidth={saved ? 2.5 : 1.75} />
        </button>
      </div>
    </div>
  );
}
