"use client";

import { useCallback, useEffect, useState } from "react";
import { Clock, AlertCircle } from "lucide-react";
import { dashboardApi, ApiError } from "@/lib/api";
import { ActivityTimeline } from "@/components/activity-timeline";
import { DashboardFooter } from "@/components/dashboard-footer";
import { PipelineStatusBanner } from "@/components/pipeline-status-banner";
import type { ActivityEvent } from "@/lib/types";

export default function ActivityPage() {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchActivity = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { events: data } = await dashboardApi.activity();
      setEvents(data);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : "Failed to load activity."
      );
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchActivity();
  }, [fetchActivity]);

  return (
    <div className="h-screen overflow-y-auto px-6 py-8 md:px-10 md:py-10">
      <div className="mx-auto max-w-2xl">
        <PipelineStatusBanner onComplete={fetchActivity} />
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-line bg-surface dark:border-line-dark dark:bg-surface-dark">
              <Clock className="h-4 w-4 text-muted dark:text-muted-dark" />
            </div>
            <h1 className="font-display text-[1.4rem] font-medium tracking-tight text-ink dark:text-ink-dark">
              Activity
            </h1>
          </div>
          <p className="mt-2 text-[13.5px] text-muted dark:text-muted-dark">
            A full history of your pipeline events — uploads, scans, and email dispatches.
          </p>
        </div>

        {/* Error */}
        {!loading && error && (
          <div className="mb-6 flex items-center gap-2 rounded-xl border border-danger/20 bg-danger/5 px-5 py-4">
            <AlertCircle className="h-5 w-5 shrink-0 text-danger" />
            <div>
              <p className="text-[13.5px] text-danger">{error}</p>
              <button
                onClick={fetchActivity}
                className="mt-1 text-[12.5px] text-danger/70 underline-offset-2 hover:underline"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* Event count badge */}
        {!loading && !error && events.length > 0 && (
          <p className="mb-4 font-mono text-[11.5px] text-muted dark:text-muted-dark">
            {events.length} event{events.length !== 1 ? "s" : ""}
          </p>
        )}

        <div className="rounded-xl border border-line bg-surface p-6 dark:border-line-dark dark:bg-surface-dark">
          <ActivityTimeline events={events} loading={loading} error={error ?? undefined} />
        </div>

        <DashboardFooter />
      </div>
    </div>
  );
}
