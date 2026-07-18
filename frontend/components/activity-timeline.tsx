"use client";

import {
  FileText,
  Search,
  Download,
  Sparkles,
  Mail,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ActivityEvent } from "@/lib/types";
import { SkeletonTimeline } from "./skeleton";

interface ActivityTimelineProps {
  events: ActivityEvent[];
  loading?: boolean;
  error?: string | null;
}

const EVENT_CONFIG: Record<
  ActivityEvent["event_type"],
  { label: string; icon: typeof FileText; color: string }
> = {
  resume_analyzed: {
    label: "Resume analyzed",
    icon: FileText,
    color:
      "bg-signal-soft text-signal border-signal/20 dark:bg-signal-soft-dark dark:text-signal-dark",
  },
  search_queries_generated: {
    label: "Search queries generated",
    icon: Search,
    color:
      "bg-blue-50 text-blue-600 border-blue-200/50 dark:bg-blue-900/20 dark:text-blue-300",
  },
  jobs_fetched: {
    label: "Jobs fetched",
    icon: Download,
    color:
      "bg-paper text-muted border-line dark:bg-paper-dark dark:text-muted-dark dark:border-line-dark",
  },
  recommendations_updated: {
    label: "Recommendations updated",
    icon: Sparkles,
    color:
      "bg-signal-soft text-signal border-signal/20 dark:bg-signal-soft-dark dark:text-signal-dark",
  },
  email_sent: {
    label: "Email sent",
    icon: Mail,
    color:
      "bg-blue-50 text-blue-600 border-blue-200/50 dark:bg-blue-900/20 dark:text-blue-300",
  },
};

function formatRelativeTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHrs = Math.floor(diffMins / 60);
    if (diffHrs < 24) return `${diffHrs}h ago`;
    const diffDays = Math.floor(diffHrs / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
  } catch {
    return "";
  }
}

function getEventDetail(event: ActivityEvent): string | null {
  const d = event.detail;
  if (!d) return null;
  if (event.event_type === "jobs_fetched" && "count" in d) {
    return `${d.count} jobs`;
  }
  if (event.event_type === "recommendations_updated" && "count" in d) {
    return `${d.count} new matches`;
  }
  if (event.event_type === "email_sent" && "to" in d) {
    return `to ${d.to}`;
  }
  return null;
}

export function ActivityTimeline({
  events,
  loading,
  error,
}: ActivityTimelineProps) {
  if (loading) return <SkeletonTimeline />;

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-line bg-paper px-4 py-3 dark:border-line-dark dark:bg-paper-dark">
        <AlertCircle className="h-4 w-4 text-danger/60" />
        <p className="text-[12.5px] text-muted dark:text-muted-dark">{error}</p>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-paper px-4 py-8 text-center dark:border-line-dark dark:bg-paper-dark">
        <p className="font-mono text-[10.5px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
          No activity yet
        </p>
        <p className="mt-1.5 text-[12.5px] text-muted dark:text-muted-dark">
          Upload your resume to start the pipeline.
        </p>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-3.5 top-0 bottom-0 w-px bg-line dark:bg-line-dark" />

      <div className="space-y-4">
        {events.map((event, i) => {
          const cfg = EVENT_CONFIG[event.event_type];
          const Icon = cfg?.icon ?? FileText;
          const extra = getEventDetail(event);

          return (
            <div key={i} className="relative flex items-start gap-3 pl-0">
              {/* Icon bubble */}
              <div
                className={cn(
                  "relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border",
                  cfg?.color ??
                    "bg-paper border-line text-muted dark:bg-paper-dark dark:border-line-dark dark:text-muted-dark"
                )}
              >
                <Icon className="h-3 w-3" />
              </div>

              {/* Content */}
              <div className="flex-1 pt-0.5">
                <div className="flex items-baseline justify-between gap-2">
                  <p className="text-[13px] text-ink dark:text-ink-dark">
                    {cfg?.label ?? event.event_type.replace(/_/g, " ")}
                    {extra && (
                      <span className="ml-1.5 text-muted dark:text-muted-dark">
                        · {extra}
                      </span>
                    )}
                  </p>
                  <span className="shrink-0 font-mono text-[11px] text-muted dark:text-muted-dark">
                    {formatRelativeTime(event.created_at)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
