"use client";

import type { SkillFrequency } from "@/lib/types";
import { SkeletonTimeline } from "./skeleton";

interface ResumeInsightsPanelProps {
  skills: SkillFrequency[];
  loading?: boolean;
}

export function ResumeInsightsPanel({
  skills,
  loading,
}: ResumeInsightsPanelProps) {
  if (loading) {
    return (
      <div className="rounded-xl2 border border-line bg-surface p-5 dark:border-line-dark dark:bg-surface-dark">
        <div className="mb-4 h-3 w-32 animate-pulse rounded bg-line dark:bg-line-dark" />
        <div className="mb-2 h-2.5 w-48 animate-pulse rounded bg-line dark:bg-line-dark" />
        <div className="mt-5">
          <SkeletonTimeline />
        </div>
      </div>
    );
  }

  if (skills.length === 0) {
    return (
      <div className="rounded-xl2 border border-line bg-surface p-5 dark:border-line-dark dark:bg-surface-dark">
        <p className="font-display text-[14.5px] font-medium text-ink dark:text-ink-dark">
          Skill Coverage
        </p>
        <div className="mt-5 rounded-lg border border-line bg-paper py-8 text-center dark:border-line-dark dark:bg-paper-dark">
          <p className="font-mono text-[10.5px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
            No data yet
          </p>
          <p className="mt-1 text-[12.5px] text-muted dark:text-muted-dark">
            Upload your resume to see skill coverage.
          </p>
        </div>
      </div>
    );
  }

  // Normalize: express each skill count as a % of the max count
  const maxCount = Math.max(...skills.map((s) => s.count), 1);
  const displayed = skills.slice(0, 10);

  return (
    <div className="rounded-xl2 border border-line bg-surface p-5 dark:border-line-dark dark:bg-surface-dark">
      <p className="font-display text-[14.5px] font-medium text-ink dark:text-ink-dark">
        Skill Coverage
      </p>
      <p className="mt-1 text-[12.5px] text-muted dark:text-muted-dark">
        How frequently each skill appears across your matched roles.
      </p>

      <div className="mt-5 space-y-4">
        {displayed.map(({ skill, count }) => {
          const pct = Math.round((count / maxCount) * 100);
          return (
            <div key={skill}>
              <div className="mb-1.5 flex items-center justify-between text-[12.5px]">
                <span className="text-ink dark:text-ink-dark">{skill}</span>
                <span className="font-mono text-muted dark:text-muted-dark">
                  {count} match{count !== 1 ? "es" : ""}
                </span>
              </div>
              <div className="h-1 w-full rounded-full bg-line dark:bg-line-dark">
                <div
                  className="h-1 rounded-full bg-signal transition-all duration-700"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
