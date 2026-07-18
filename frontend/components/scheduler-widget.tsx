"use client";

import { useEffect, useState } from "react";
import { Clock, Zap, Download, Sparkles } from "lucide-react";
import type { DashboardStats } from "@/lib/types";

interface SchedulerWidgetProps {
  stats: DashboardStats | null;
  loading?: boolean;
}

// ─── HH:MM:SS countdown ───────────────────────────────────────────────────────

function formatCountdownHMS(targetISO: string | null): string {
  if (!targetISO) return "—";
  const target = new Date(targetISO).getTime();
  const now = Date.now();
  const diffMs = target - now;

  if (diffMs <= 0) return "Running now";

  const totalSecs = Math.floor(diffMs / 1000);
  const h = Math.floor(totalSecs / 3600);
  const m = Math.floor((totalSecs % 3600) / 60);
  const s = totalSecs % 60;

  // Always show HH:MM:SS
  return [
    String(h).padStart(2, "0"),
    String(m).padStart(2, "0"),
    String(s).padStart(2, "0"),
  ].join(":");
}

// ─── "Today • 05:30 AM" / "Yesterday • 11:30 PM" / "Jul 14 • 03:30 AM" ──────

function calculateLastScanIST(): string {
  const now = new Date();
  
  // 1. Calculate previous scheduled run in UTC (every 4 hours: 0, 4, 8, 12, 16, 20)
  const lastScan = new Date(now);
  const currentUTCHours = now.getUTCHours();
  const lastScanUTCHours = Math.floor(currentUTCHours / 4) * 4;
  lastScan.setUTCHours(lastScanUTCHours, 0, 0, 0);

  // 2. Helper to get date components in Asia/Kolkata
  const getISTComponents = (d: Date) => {
    const formatter = new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Kolkata",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
    return formatter.format(d); // returns "MM/DD/YYYY"
  };

  const getYesterdayISTComponents = () => {
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const formatter = new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Kolkata",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
    return formatter.format(yesterday);
  };

  const nowISTStr = getISTComponents(now);
  const lastScanISTStr = getISTComponents(lastScan);
  const yesterdayISTStr = getYesterdayISTComponents();

  // Get time parts for formatting in Asia/Kolkata
  const timeFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
  const timeStr = timeFormatter.format(lastScan); // e.g. "05:30 AM"

  if (lastScanISTStr === nowISTStr) {
    return `Today • ${timeStr}`;
  } else if (lastScanISTStr === yesterdayISTStr) {
    return `Yesterday • ${timeStr}`;
  } else {
    const dateFormatter = new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Kolkata",
      month: "short",
      day: "numeric",
    });
    const dateStr = dateFormatter.format(lastScan);
    return `${dateStr} • ${timeStr}`;
  }
}

// ─── Widget ───────────────────────────────────────────────────────────────────

export function SchedulerWidget({ stats, loading }: SchedulerWidgetProps) {
  const [countdown, setCountdown] = useState("—");
  const [lastScan, setLastScan] = useState("—");

  useEffect(() => {
    const tick = () => {
      if (stats?.next_sync) {
        setCountdown(formatCountdownHMS(stats.next_sync));
      } else {
        setCountdown("—");
      }
      setLastScan(calculateLastScanIST());
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [stats?.next_sync]);

  return (
    <div className="rounded-xl2 border border-line bg-surface p-5 dark:border-line-dark dark:bg-surface-dark">
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-signal-soft dark:bg-signal-soft-dark">
          <Zap className="h-3 w-3 text-signal" strokeWidth={2.5} />
        </div>
        <p className="font-display text-[14px] font-medium text-ink dark:text-ink-dark">
          Live Scheduler
        </p>
        {/* Pulse indicator */}
        <div className="ml-auto flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal opacity-60" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-signal" />
          </span>
          <span className="font-mono text-[10px] text-signal">active</span>
        </div>
      </div>

      <div className="space-y-2.5">
        {/* Next scan — HH:MM:SS countdown */}
        <div className="rounded-lg border border-signal/20 bg-signal-soft px-4 py-3 dark:bg-signal-soft-dark">
          <div className="flex items-center gap-1.5">
            <Clock className="h-3 w-3 text-signal" />
            <p className="font-mono text-[9.5px] uppercase tracking-[0.15em] text-signal">
              Next scheduled scan
            </p>
          </div>
          {loading ? (
            <div className="mt-1.5 h-8 w-28 animate-pulse rounded bg-signal/10" />
          ) : (
            <p className="mt-1 font-mono text-[26px] font-medium tabular-nums leading-none text-ink dark:text-ink-dark">
              {countdown}
            </p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          {/* Last scan */}
          <div className="rounded-lg border border-line bg-paper px-3 py-2.5 dark:border-line-dark dark:bg-paper-dark">
            <p className="font-mono text-[9.5px] uppercase tracking-[0.12em] text-muted dark:text-muted-dark">
              Last scan
            </p>
            {loading ? (
              <div className="mt-1.5 h-4 w-20 animate-pulse rounded bg-line dark:bg-line-dark" />
            ) : (
              <p className="mt-0.5 text-[12px] font-medium text-ink dark:text-ink-dark leading-snug">
                {lastScan}
              </p>
            )}
          </div>

          {/* Jobs fetched */}
          <div className="rounded-lg border border-line bg-paper px-3 py-2.5 dark:border-line-dark dark:bg-paper-dark">
            <div className="flex items-center gap-1">
              <Download className="h-2.5 w-2.5 text-muted dark:text-muted-dark" />
              <p className="font-mono text-[9.5px] uppercase tracking-[0.12em] text-muted dark:text-muted-dark">
                Jobs fetched
              </p>
            </div>
            {loading ? (
              <div className="mt-1.5 h-4 w-10 animate-pulse rounded bg-line dark:bg-line-dark" />
            ) : (
              <p className="mt-0.5 font-mono text-[13px] font-medium text-ink dark:text-ink-dark">
                {stats?.jobs_fetched_today != null ? stats.jobs_fetched_today.toLocaleString() : "—"}
              </p>
            )}
          </div>
        </div>

        {/* New matches today */}
        <div className="flex items-center gap-2 rounded-lg border border-line bg-paper px-3 py-2.5 dark:border-line-dark dark:bg-paper-dark">
          <Sparkles className="h-3 w-3 text-signal" />
          {loading ? (
            <div className="h-3.5 w-32 animate-pulse rounded bg-line dark:bg-line-dark" />
          ) : (
            <p className="text-[12.5px] text-muted dark:text-muted-dark">
              <span className="font-medium text-ink dark:text-ink-dark">
                {stats?.new_matches_today ?? "—"}
              </span>{" "}
              new match{stats?.new_matches_today !== 1 ? "es" : ""} today
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
