"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Sparkles,
  BarChart2,
  FileText,
  Mail,
  RefreshCw,
  Search,
  SlidersHorizontal,
  AlertCircle,
  X,
  MapPin,
  Briefcase,
  Sunrise,
  Sun,
  MoonStar,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { dashboardApi, recommendationsApi, ApiError } from "@/lib/api";
import { StatCard } from "@/components/stat-card";
import { JobCard } from "@/components/job-card";
import { JobDrawer } from "@/components/job-drawer";
import { ActivityTimeline } from "@/components/activity-timeline";
import { SkillGalaxy } from "@/components/skill-galaxy";
import { SchedulerWidget } from "@/components/scheduler-widget";
import { ResumeInsightsPanel } from "@/components/resume-insights-panel";
import { SkeletonJobCard, SkeletonStatCard } from "@/components/skeleton";
import { DashboardFooter } from "@/components/dashboard-footer";
import { PipelineStatusBanner } from "@/components/pipeline-status-banner";
import { usePipelineStatus } from "@/lib/pipeline-status-context";
import type {
  DashboardStats,
  Recommendation,
  ActivityEvent,
  SkillFrequency,
} from "@/lib/types";

// ─── Greeting helpers (Lucide icons, no emoji) ───────────────────────────────

type GreetingPeriod = "morning" | "afternoon" | "evening" | "night";

function getGreetingPeriod(h: number): GreetingPeriod {
  if (h < 12) return "morning";
  if (h < 17) return "afternoon";
  if (h < 21) return "evening";
  return "night";
}

function getGreetingText(period: GreetingPeriod): string {
  return {
    morning: "Good morning",
    afternoon: "Good afternoon",
    evening: "Good evening",
    night: "Good night",
  }[period];
}

// function GreetingIcon({ period }: { period: GreetingPeriod }) {
//   const cls = "h-5 w-5 shrink-0";
//   if (period === "morning")
//     return <Sunrise className={`${cls} text-amber-500`} strokeWidth={1.8} />;
//   if (period === "afternoon")
//     return <Sun className={`${cls} text-amber-500`} strokeWidth={1.8} />;
//   if (period === "evening")
//     return <MoonStar className={`${cls} text-violet-400`} strokeWidth={1.8} />;
//   return <Sparkles className={`${cls} text-signal`} strokeWidth={1.8} />;
// }
function GreetingIcon({ period }: { period: GreetingPeriod }) {
  const cls = "h-6 w-6 shrink-0";

  if (period === "morning")
    return (
      <Sunrise
        className={`${cls} text-amber-500 animate-bounce`}
        strokeWidth={2.5}
      />
    );

  if (period === "afternoon")
    return (
      <Sun
        className={`${cls} text-yellow-400 animate-[spin_8s_linear_infinite]`}
        strokeWidth={2.5}
      />
      

    );

  if (period === "evening")
    return (
      <MoonStar
        className={`${cls} text-violet-400 animate-pulse`}
        strokeWidth={2.2}
      />
    );

  return (
    <Sparkles
      className={`${cls} text-signal animate-pulse`}
      strokeWidth={2.5}
    />
  );
}

function formatTimeBadge(date: Date): string {
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}

// ─── Filter types ─────────────────────────────────────────────────────────────


type QuickFilter = "all" | "excellent" | "good" | "remote";

const QUICK_FILTERS: { id: QuickFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "excellent", label: "Excellent" },
  { id: "good", label: "Good" },
  { id: "remote", label: "Remote" },
];

// Employment type options matching backend values
const EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract", "Internship", "Freelance"];

interface MoreFilters {
  employmentType: string;
  location: string;
}

// ─── More Filters Dropdown ────────────────────────────────────────────────────

function MoreFiltersDropdown({
  open,
  onClose,
  filters,
  onChange,
}: {
  open: boolean;
  onClose: () => void;
  filters: MoreFilters;
  onChange: (f: MoreFilters) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open, onClose]);

  if (!open) return null;

  const hasActive = filters.employmentType !== "" || filters.location !== "";

  return (
    <div
      ref={ref}
      className="absolute right-0 top-full z-30 mt-2 w-72 rounded-xl border border-line bg-surface p-4 shadow-card-hover dark:border-line-dark dark:bg-surface-dark"
    >
      <div className="mb-3 flex items-center justify-between">
        <p className="font-display text-[13px] font-medium text-ink dark:text-ink-dark">
          More Filters
        </p>
        {hasActive && (
          <button
            onClick={() => onChange({ employmentType: "", location: "" })}
            className="text-[11.5px] text-muted underline-offset-2 hover:text-danger hover:underline dark:text-muted-dark"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Location filter */}
      <div className="mb-3">
        <label className="mb-1.5 flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-muted dark:text-muted-dark">
          <MapPin className="h-3 w-3" />
          Location keyword
        </label>
        <input
          type="text"
          placeholder="e.g. London, Bangalore…"
          value={filters.location}
          onChange={(e) => onChange({ ...filters, location: e.target.value })}
          className="w-full rounded-lg border border-line bg-paper py-2 px-3 text-[12.5px] text-ink placeholder:text-muted focus:border-ink/30 focus:outline-none dark:border-line-dark dark:bg-paper-dark dark:text-ink-dark dark:placeholder:text-muted-dark"
        />
      </div>

      {/* Employment type filter */}
      <div>
        <label className="mb-1.5 flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-muted dark:text-muted-dark">
          <Briefcase className="h-3 w-3" />
          Employment type
        </label>
        <div className="flex flex-wrap gap-1.5">
          {EMPLOYMENT_TYPES.map((type) => (
            <button
              key={type}
              onClick={() =>
                onChange({
                  ...filters,
                  employmentType: filters.employmentType === type ? "" : type,
                })
              }
              className={`rounded-full border px-2.5 py-1 text-[11.5px] transition-colors ${
                filters.employmentType === type
                  ? "border-ink bg-ink text-paper dark:border-ink-dark dark:bg-ink-dark dark:text-paper-dark"
                  : "border-line text-muted hover:border-ink/30 hover:text-ink dark:border-line-dark dark:text-muted-dark"
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const { user } = useAuth();
  const { triggerRefresh } = usePipelineStatus();

  // Stats
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  // Recommendations
  const [jobs, setJobs] = useState<Recommendation[]>([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [jobsError, setJobsError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshStatus, setRefreshStatus] = useState<string | null>(null);

  // Activity + Skills
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [activityLoading, setActivityLoading] = useState(true);
  const [activityError, setActivityError] = useState<string | null>(null);
  const [skills, setSkills] = useState<SkillFrequency[]>([]);
  const [skillsLoading, setSkillsLoading] = useState(true);

  // UI state
  const [selectedJob, setSelectedJob] = useState<Recommendation | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<QuickFilter>("all");
  const [moreFiltersOpen, setMoreFiltersOpen] = useState(false);
  const [moreFilters, setMoreFilters] = useState<MoreFilters>({
    employmentType: "",
    location: "",
  });

  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    setStatsError(null);
    try {
      const data = await dashboardApi.stats();
      setStats(data);
    } catch (err) {
      setStatsError(err instanceof ApiError ? err.detail : "Failed to load stats.");
    } finally {
      setStatsLoading(false);
    }
  }, []);

  const fetchJobs = useCallback(async () => {
    setJobsLoading(true);
    setJobsError(null);
    try {
      const { recommendations } = await recommendationsApi.list();
      setJobs(recommendations);
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setJobs([]);
      } else {
        setJobsError(err instanceof ApiError ? err.detail : "Failed to load recommendations.");
      }
    } finally {
      setJobsLoading(false);
    }
  }, []);

  const fetchActivity = useCallback(async () => {
    setActivityLoading(true);
    setActivityError(null);
    try {
      const { events } = await dashboardApi.activity();
      setActivity(events);
    } catch (err) {
      setActivityError(err instanceof ApiError ? err.detail : "Failed to load activity.");
      setActivity([]);
    } finally {
      setActivityLoading(false);
    }
  }, []);

  const fetchSkills = useCallback(async () => {
    setSkillsLoading(true);
    try {
      const { skills: data } = await dashboardApi.skillFrequency();
      setSkills(data);
    } catch {
      setSkills([]);
    } finally {
      setSkillsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    fetchJobs();
    fetchActivity();
    fetchSkills();
  }, [fetchStats, fetchJobs, fetchActivity, fetchSkills]);

  // Called when the background pipeline finishes — refreshes all data
  const handlePipelineComplete = useCallback(async () => {
    await Promise.all([fetchJobs(), fetchStats(), fetchActivity(), fetchSkills()]);
  }, [fetchJobs, fetchStats, fetchActivity, fetchSkills]);

  async function handleRefresh() {
    setRefreshing(true);
    setRefreshStatus("This may take some time... We are finding the best recommendations for you...");
    try {
      await recommendationsApi.refresh();
      triggerRefresh();
      await Promise.all([fetchJobs(), fetchStats()]);
      setRefreshStatus("Done! Your matches have been updated.");
      setTimeout(() => setRefreshStatus(null), 3000);
    } catch {
      setRefreshStatus(null);
    } finally {
      setRefreshing(false);
    }
  }

  // Filter + search — exact match against backend values
  const filteredJobs = jobs.filter((job) => {
    const matchesSearch =
      !searchQuery ||
      job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.company.toLowerCase().includes(searchQuery.toLowerCase());

    // Quick filters — exact string comparison with backend overall_match values
    const matchesQuickFilter =
      activeFilter === "all" ||
      (activeFilter === "excellent" && job.overall_match === "Excellent Match") ||
      (activeFilter === "good" && job.overall_match === "Good Match") ||
      (activeFilter === "remote" && job.location?.toLowerCase().includes("remote"));

    // More filters
    const matchesEmployment =
      !moreFilters.employmentType ||
      job.employment_type?.toLowerCase().includes(moreFilters.employmentType.toLowerCase());

    const matchesLocation =
      !moreFilters.location ||
      job.location?.toLowerCase().includes(moreFilters.location.toLowerCase());

    return matchesSearch && matchesQuickFilter && matchesEmployment && matchesLocation;
  });

  const hasMoreFiltersActive =
    moreFilters.employmentType !== "" || moreFilters.location !== "";

  // Live clock — updates every minute
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(id);
  }, []);

  const period = getGreetingPeriod(now.getHours());
  const displayName = user?.name ?? user?.email?.split("@")[0] ?? "";

  return (
    <div className="h-screen overflow-y-auto px-6 py-8 md:px-10 md:py-10">
      <div className="mx-auto max-w-6xl">
        {/* ── Greeting ── */}
        <div className="mb-8 flex items-end justify-between">
          <div>
            {/* Time badge */}
            <div className="mb-2 inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1 dark:border-line-dark dark:bg-surface-dark">
              <span className="h-1.5 w-1.5 rounded-full bg-signal" />
              <span className="font-mono text-[11px] tabular-nums text-muted dark:text-muted-dark">
                {formatTimeBadge(now)}
              </span>
            </div>
            {/* Icon + greeting */}
            <div className="flex items-center gap-2">
              <GreetingIcon period={period} />
              <h1 className="font-display text-[1.6rem] font-medium tracking-tight text-ink dark:text-ink-dark">
                {getGreetingText(period)},{" "}
                <span className="text-signal">{displayName}</span>
              </h1>
            </div>
            <p className="mt-1 text-[13.5px] text-muted dark:text-muted-dark">
              Ready to discover your next opportunity?
            </p>
          </div>

          <div className="hidden flex-col items-end gap-2 md:flex">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 rounded-full border border-line px-4 py-2 text-[13px] text-muted transition-colors hover:border-ink/30 hover:text-ink disabled:opacity-50 dark:border-line-dark dark:text-muted-dark dark:hover:border-ink-dark/30 dark:hover:text-ink-dark"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
              {refreshing ? "Scanning..." : "Refresh matches"}
            </button>
            {/* Refresh status message */}
            {refreshStatus && (
              <p
                className={`text-[12px] transition-all duration-300 ${
                  refreshStatus.startsWith("Done")
                    ? "text-signal"
                    : "animate-pulse text-muted dark:text-muted-dark"
                }`}
              >
                {refreshStatus}
              </p>
            )}
          </div>
        </div>

        {/* ── Pipeline status banner (shows after upload, auto-refreshes on done) ── */}
        <PipelineStatusBanner onComplete={handlePipelineComplete} />

        {/* ── Stat cards — 4 cards, no duplicates with Live Scheduler ── */}
        <div className="mb-8 grid grid-cols-2 gap-3 md:grid-cols-4">
          {statsLoading ? (
            <>
              <SkeletonStatCard />
              <SkeletonStatCard />
              <SkeletonStatCard />
              <SkeletonStatCard />
            </>
          ) : (
            <>
              <StatCard
                label="New matches today"
                value={stats?.new_matches_today}
                icon={Sparkles}
                iconColor="text-signal"
              />
              <StatCard
                label="Avg match score"
                value={stats?.avg_match_score}
                suffix="%"
                icon={BarChart2}
              />
              <StatCard
                label="Resume strength"
                value={stats?.resume_strength}
                suffix="%"
                icon={FileText}
              />
              <StatCard
                label="Emails sent"
                value={stats?.emails_sent}
                icon={Mail}
              />
            </>
          )}
        </div>

        {/* ── Stats error ── */}
        {statsError && (
          <div className="mb-6 flex items-center gap-2 rounded-lg border border-danger/20 bg-danger/5 px-4 py-3 text-[13px] text-danger">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {statsError}
          </div>
        )}

        {/* ── Main grid: jobs + right panel ── */}
        <div className="grid gap-8 lg:grid-cols-[1fr_296px]">
          {/* ── Left: Filters + Job cards ── */}
          <div>
            {/* Filter bar */}
            <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="relative w-full max-w-sm">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-[15px] w-[15px] -translate-y-1/2 text-muted dark:text-muted-dark" />
                <input
                  type="text"
                  placeholder="Search by title or company"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-lg border border-line bg-surface py-2 pl-9 pr-3 text-[13.5px] text-ink placeholder:text-muted focus:border-ink/30 focus:outline-none dark:border-line-dark dark:bg-surface-dark dark:text-ink-dark dark:placeholder:text-muted-dark dark:focus:border-ink-dark/30"
                />
              </div>

              <div className="flex items-center gap-2">
                {QUICK_FILTERS.map(({ id, label }) => (
                  <button
                    key={id}
                    onClick={() => setActiveFilter(id)}
                    className={`rounded-full border px-3 py-1.5 text-[12.5px] transition-colors ${
                      activeFilter === id
                        ? "border-ink bg-ink text-paper dark:border-ink-dark dark:bg-ink-dark dark:text-paper-dark"
                        : "border-line text-muted hover:border-ink/30 hover:text-ink dark:border-line-dark dark:text-muted-dark dark:hover:border-ink-dark/30 dark:hover:text-ink-dark"
                    }`}
                  >
                    {label}
                  </button>
                ))}

                {/* More button with dropdown */}
                <div className="relative">
                  <button
                    onClick={() => setMoreFiltersOpen((v) => !v)}
                    className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[12.5px] transition-colors ${
                      hasMoreFiltersActive
                        ? "border-ink bg-ink text-paper dark:border-ink-dark dark:bg-ink-dark dark:text-paper-dark"
                        : "border-line text-muted hover:border-ink/30 hover:text-ink dark:border-line-dark dark:text-muted-dark dark:hover:border-ink-dark/30 dark:hover:text-ink-dark"
                    }`}
                  >
                    <SlidersHorizontal className="h-3 w-3" strokeWidth={2} />
                    More
                    {hasMoreFiltersActive && (
                      <span className="ml-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-paper text-[9px] font-bold text-ink dark:bg-paper-dark dark:text-ink-dark">
                        {[moreFilters.employmentType, moreFilters.location].filter(Boolean).length}
                      </span>
                    )}
                  </button>
                  <MoreFiltersDropdown
                    open={moreFiltersOpen}
                    onClose={() => setMoreFiltersOpen(false)}
                    filters={moreFilters}
                    onChange={setMoreFilters}
                  />
                </div>

                {/* Clear more filters if active */}
                {hasMoreFiltersActive && (
                  <button
                    onClick={() => setMoreFilters({ employmentType: "", location: "" })}
                    className="flex h-7 w-7 items-center justify-center rounded-full border border-line text-muted hover:border-danger/30 hover:text-danger dark:border-line-dark dark:text-muted-dark"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
            </div>

            {/* Job cards */}
            {jobsLoading ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {[...Array(4)].map((_, i) => (
                  <SkeletonJobCard key={i} />
                ))}
              </div>
            ) : jobsError ? (
              <div className="flex flex-col items-center justify-center rounded-xl2 border border-line bg-surface px-6 py-16 text-center dark:border-line-dark dark:bg-surface-dark">
                <AlertCircle className="mb-3 h-8 w-8 text-danger/50" />
                <p className="font-display text-[15px] font-medium text-ink dark:text-ink-dark">
                  Couldn&apos;t load recommendations
                </p>
                <p className="mt-1 text-[13px] text-muted dark:text-muted-dark">{jobsError}</p>
                <button
                  onClick={fetchJobs}
                  className="mt-4 rounded-full border border-line px-4 py-2 text-[13px] text-muted transition-colors hover:border-ink/30 hover:text-ink dark:border-line-dark dark:text-muted-dark"
                >
                  Try again
                </button>
              </div>
            ) : filteredJobs.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-xl2 border border-dashed border-line bg-surface px-6 py-16 text-center dark:border-line-dark dark:bg-surface-dark">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-line bg-paper dark:border-line-dark dark:bg-paper-dark">
                  <Sparkles className="h-5 w-5 text-muted dark:text-muted-dark" />
                </div>
                {jobs.length === 0 ? (
                  <>
                    <p className="font-display text-[16px] font-medium text-ink dark:text-ink-dark">
                      Looks quiet today.
                    </p>
                    <p className="mt-2 max-w-xs text-[13.5px] leading-relaxed text-muted dark:text-muted-dark">
                      We&apos;re continuously searching for jobs that match your profile. Upload
                      your resume to start the pipeline.
                    </p>
                    <a
                      href="/dashboard/resume"
                      className="mt-5 rounded-full bg-ink px-5 py-2.5 text-[13px] font-medium text-paper transition-colors hover:bg-ink/85 dark:bg-ink-dark dark:text-paper-dark"
                    >
                      Upload resume
                    </a>
                  </>
                ) : (
                  <>
                    <p className="font-display text-[16px] font-medium text-ink dark:text-ink-dark">
                      No results found
                    </p>
                    <p className="mt-1 text-[13px] text-muted dark:text-muted-dark">
                      Try adjusting your search or filters.
                    </p>
                    <button
                      onClick={() => {
                        setSearchQuery("");
                        setActiveFilter("all");
                        setMoreFilters({ employmentType: "", location: "" });
                      }}
                      className="mt-4 text-[13px] text-muted underline-offset-2 hover:underline dark:text-muted-dark"
                    >
                      Clear all filters
                    </button>
                  </>
                )}
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {filteredJobs.map((job) => (
                  <JobCard key={job.job_id} job={job} onViewDetails={setSelectedJob} />
                ))}
              </div>
            )}
          </div>

          {/* ── Right panel ── */}
          <div className="space-y-6 lg:pt-11">
            {/* Scheduler widget */}
            <SchedulerWidget stats={stats} loading={statsLoading} />

            {/* Activity timeline */}
            <div className="rounded-xl2 border border-line bg-surface p-5 dark:border-line-dark dark:bg-surface-dark">
              <p className="mb-4 font-display text-[14px] font-medium text-ink dark:text-ink-dark">
                Activity
              </p>
              <ActivityTimeline
                events={activity}
                loading={activityLoading}
                error={activityError}
              />
            </div>

            {/* Skill Galaxy */}
            <div>
              <p className="mb-3 font-display text-[14px] font-medium text-ink dark:text-ink-dark">
                Skill Galaxy
              </p>
              <p className="mb-3 text-[12.5px] text-muted dark:text-muted-dark">
                Skills matched across your recommendations — larger = more frequent.
              </p>
              <SkillGalaxy skills={skills} loading={skillsLoading} />
            </div>

            {/* Resume Insights */}
            <ResumeInsightsPanel skills={skills} loading={skillsLoading} />
          </div>
        </div>
      </div>

      {/* Job detail drawer */}
      <JobDrawer job={selectedJob} onClose={() => setSelectedJob(null)} />

      {/* Footer */}
      <DashboardFooter />
    </div>
  );
}
