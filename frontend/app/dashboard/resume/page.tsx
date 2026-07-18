"use client";

import { useCallback, useEffect, useState } from "react";
import {
  FileText,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Loader2,
} from "lucide-react";
import { resumesApi, ApiError } from "@/lib/api";
import { ResumeUploadZone } from "@/components/resume-upload-zone";
import type { ResumeData } from "@/lib/types";
import { cn } from "@/lib/utils";
import { PipelineStatusBanner } from "@/components/pipeline-status-banner";
import { usePipelineStatus } from "@/lib/pipeline-status-context";

// ─── Section Accordion ───────────────────────────────────────────────────────


function Section({
  title,
  badge,
  children,
  defaultOpen = true,
}: {
  title: string;
  badge?: string | number;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-xl border border-line bg-surface dark:border-line-dark dark:bg-surface-dark">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-5 py-4"
      >
        <div className="flex items-center gap-2.5">
          <span className="font-display text-[14px] font-medium text-ink dark:text-ink-dark">
            {title}
          </span>
          {badge !== undefined && (
            <span className="rounded-full border border-line bg-paper px-2 py-0.5 font-mono text-[10.5px] text-muted dark:border-line-dark dark:bg-paper-dark dark:text-muted-dark">
              {badge}
            </span>
          )}
        </div>
        {open ? (
          <ChevronDown className="h-4 w-4 text-muted dark:text-muted-dark" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted dark:text-muted-dark" />
        )}
      </button>
      {open && (
        <div className="border-t border-line px-5 pb-5 pt-4 dark:border-line-dark">
          {children}
        </div>
      )}
    </div>
  );
}

// ─── Skill chip ──────────────────────────────────────────────────────────────

function SkillChip({ label }: { label: string }) {
  return (
    <span className="rounded-md border border-signal/25 bg-signal-soft px-2.5 py-1 text-[12px] text-ink dark:border-signal/20 dark:bg-signal-soft-dark dark:text-ink-dark">
      {label}
    </span>
  );
}

// ─── Flat skill list helper ───────────────────────────────────────────────────

function flatSkills(
  skills: Record<string, string[]> | string[] | undefined
): string[] {
  if (!skills) return [];
  if (Array.isArray(skills)) return skills;
  return Object.values(skills).flat();
}

// ─── Resume Display ───────────────────────────────────────────────────────────

function ResumeDisplay({
  data,
  onDelete,
  onReplace,
  deleting,
}: {
  data: ResumeData;
  onDelete: () => void;
  onReplace: () => void;
  deleting: boolean;
}) {
  const { resume } = data;
  const allSkills = flatSkills(resume.skills);

  return (
    <div className="space-y-4">
      {/* Header bar */}
      <div className="flex items-center justify-between rounded-xl border border-signal/20 bg-signal-soft px-5 py-3.5 dark:bg-signal-soft-dark">
        <div className="flex items-center gap-3">
          <CheckCircle2 className="h-5 w-5 text-signal" />
          <div>
            <p className="font-display text-[14px] font-medium text-ink dark:text-ink-dark">
              Resume on file
            </p>
            {data.name && (
              <p className="text-[12.5px] text-muted dark:text-muted-dark">
                {data.name}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onReplace}
            className="flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-[12.5px] text-muted transition-colors hover:border-ink/30 hover:text-ink dark:border-line-dark dark:text-muted-dark dark:hover:border-ink-dark/30 dark:hover:text-ink-dark"
          >
            <RefreshCw className="h-3 w-3" />
            Replace
          </button>
          <button
            onClick={onDelete}
            disabled={deleting}
            className="flex items-center gap-1.5 rounded-lg border border-danger/20 px-3 py-1.5 text-[12.5px] text-danger transition-colors hover:bg-danger/5 disabled:opacity-50"
          >
            {deleting ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Trash2 className="h-3 w-3" />
            )}
            Delete
          </button>
        </div>
      </div>

      {/* Summary */}
      {resume.summary && (
        <Section title="Summary">
          <p className="text-[13.5px] leading-relaxed text-ink dark:text-ink-dark">
            {resume.summary}
          </p>
        </Section>
      )}

      {/* Skills */}
      {allSkills.length > 0 && (
        <Section title="Skills" badge={allSkills.length}>
          {/* If skills are categorized */}
          {!Array.isArray(resume.skills) && typeof resume.skills === "object" ? (
            <div className="space-y-4">
              {Object.entries(resume.skills as Record<string, string[]>).map(
                ([category, list]) =>
                  list.length > 0 && (
                    <div key={category}>
                      <p className="mb-2 font-mono text-[10.5px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
                        {category}
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {list.map((s) => (
                          <SkillChip key={s} label={s} />
                        ))}
                      </div>
                    </div>
                  )
              )}
            </div>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {allSkills.map((s) => (
                <SkillChip key={s} label={s} />
              ))}
            </div>
          )}
        </Section>
      )}

      {/* Experience */}
      {resume.experience && resume.experience.length > 0 && (
        <Section title="Experience" badge={resume.experience.length}>
          <div className="space-y-5">
            {resume.experience.map((exp, i) => (
              <div key={i} className={cn(i > 0 && "border-t border-line pt-5 dark:border-line-dark")}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    {exp.role && (
                      <p className="font-display text-[14px] font-medium text-ink dark:text-ink-dark">
                        {exp.role}
                      </p>
                    )}
                    {exp.company && (
                      <p className="mt-0.5 text-[13px] text-muted dark:text-muted-dark">
                        {exp.company}
                      </p>
                    )}
                  </div>
                  {exp.duration && (
                    <span className="shrink-0 rounded border border-line px-2 py-0.5 font-mono text-[10.5px] text-muted dark:border-line-dark dark:text-muted-dark">
                      {exp.duration}
                    </span>
                  )}
                </div>
                {exp.description && (
                  <p className="mt-2 text-[13px] leading-relaxed text-muted dark:text-muted-dark">
                    {exp.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Projects */}
      {resume.projects && resume.projects.length > 0 && (
        <Section title="Projects" badge={resume.projects.length} defaultOpen={false}>
          <div className="space-y-5">
            {resume.projects.map((proj, i) => (
              <div key={i} className={cn(i > 0 && "border-t border-line pt-5 dark:border-line-dark")}>
                {proj.title && (
                  <p className="font-display text-[14px] font-medium text-ink dark:text-ink-dark">
                    {proj.title}
                  </p>
                )}
                {proj.description && (
                  <p className="mt-1 text-[13px] leading-relaxed text-muted dark:text-muted-dark">
                    {proj.description}
                  </p>
                )}
                {proj.technologies && proj.technologies.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {proj.technologies.map((t) => (
                      <span
                        key={t}
                        className="rounded border border-line px-2 py-0.5 text-[11.5px] text-muted dark:border-line-dark dark:text-muted-dark"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Education */}
      {resume.education && resume.education.length > 0 && (
        <Section title="Education" badge={resume.education.length} defaultOpen={false}>
          <div className="space-y-4">
            {resume.education.map((edu, i) => (
              <div key={i} className={cn(i > 0 && "border-t border-line pt-4 dark:border-line-dark")}>
                {edu.institution && (
                  <p className="font-display text-[14px] font-medium text-ink dark:text-ink-dark">
                    {edu.institution}
                  </p>
                )}
                <div className="mt-0.5 flex items-center gap-2 text-[13px] text-muted dark:text-muted-dark">
                  {edu.degree && <span>{edu.degree}</span>}
                  {edu.year && (
                    <>
                      <span className="opacity-40">·</span>
                      <span>{edu.year}</span>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Certifications */}
      {resume.certifications && resume.certifications.length > 0 && (
        <Section title="Certifications" badge={resume.certifications.length} defaultOpen={false}>
          <div className="flex flex-wrap gap-1.5">
            {resume.certifications.map((cert, idx) => {
              const label = typeof cert === "object" && cert
                ? (cert["name"] || cert["title"] || cert["certification"] || JSON.stringify(cert))
                : String(cert);
              return (
                <span
                  key={idx}
                  className="rounded-md border border-blue-200/50 bg-blue-50 px-2.5 py-1 text-[12px] text-blue-700 dark:border-blue-500/20 dark:bg-blue-900/15 dark:text-blue-300"
                >
                  {label}
                </span>
              );
            })}
          </div>
        </Section>
      )}

      {/* Achievements */}
      {resume.achievements && resume.achievements.length > 0 && (
        <Section title="Achievements" badge={resume.achievements.length} defaultOpen={false}>
          <div className="space-y-4">
            {resume.achievements.map((ach, idx) => {
              if (typeof ach === "object" && ach) {
                const title = ach["title"] || "";
                const awardedBy = ach["awarded_by"] || ach["awardedBy"] || "";
                const year = ach["year"] || "";
                const description = ach["description"] || "";
                return (
                  <div key={idx} className="text-[13px] leading-relaxed text-ink dark:text-ink-dark">
                    <p className="font-medium text-ink dark:text-ink-dark">
                      {title}
                      {awardedBy && <span className="font-normal text-muted dark:text-muted-dark"> — {awardedBy}</span>}
                      {year && <span className="font-mono text-[11px] text-muted dark:text-muted-dark ml-2">({year})</span>}
                    </p>
                    {description && <p className="text-[12.5px] text-muted dark:text-muted-dark mt-0.5">{description}</p>}
                  </div>
                );
              }
              return (
                <p key={idx} className="text-[13px] text-ink dark:text-ink-dark">
                  {String(ach)}
                </p>
              );
            })}
          </div>
        </Section>
      )}

      {/* Search queries */}
      {data.queries && data.queries.length > 0 && (
        <Section title="Generated Search Queries" badge={data.queries.length} defaultOpen={false}>
          <p className="mb-3 text-[12.5px] text-muted dark:text-muted-dark">
            These queries are used to fetch job listings that match your profile.
          </p>
          <div className="space-y-1.5">
            {data.queries.map((q, i) => (
              <div
                key={i}
                className="flex items-center gap-2.5 rounded-lg border border-line bg-paper px-3 py-2 dark:border-line-dark dark:bg-paper-dark"
              >
                <span className="font-mono text-[10px] text-muted dark:text-muted-dark">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="text-[12.5px] text-ink dark:text-ink-dark">{q}</span>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ResumePage() {
  const { triggerRefresh } = usePipelineStatus();
  const [resumeData, setResumeData] = useState<ResumeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [replacing, setReplacing] = useState(false);

  const fetchResume = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await resumesApi.get();
      setResumeData(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setResumeData(null);
      } else {
        setError(
          err instanceof ApiError ? err.detail : "Failed to load resume."
        );
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchResume();
  }, [fetchResume]);

  async function handleDelete() {
    setDeleting(true);
    try {
      await resumesApi.delete();
      setResumeData(null);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : "Failed to delete resume."
      );
    } finally {
      setDeleting(false);
    }
  }

  function handleSuccess(data: ResumeData) {
    setResumeData(data);
    setReplacing(false);
    triggerRefresh();
  }

  return (
    <div className="h-screen overflow-y-auto px-6 py-8 md:px-10 md:py-10">
      <div className="mx-auto max-w-3xl">
        <PipelineStatusBanner onComplete={fetchResume} />
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-line bg-surface dark:border-line-dark dark:bg-surface-dark">
              <FileText className="h-4 w-4 text-muted dark:text-muted-dark" />
            </div>
            <h1 className="font-display text-[1.4rem] font-medium tracking-tight text-ink dark:text-ink-dark">
              Resume
            </h1>
          </div>
          <p className="mt-2 text-[13.5px] text-muted dark:text-muted-dark">
            Your parsed resume powers all job matching. Replace it at any time.
          </p>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="h-6 w-6 animate-spin text-muted dark:text-muted-dark" />
            <p className="mt-3 text-[13px] text-muted dark:text-muted-dark">
              Loading your resume…
            </p>
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="flex items-center gap-2.5 rounded-xl border border-danger/20 bg-danger/5 px-5 py-4">
            <AlertCircle className="h-5 w-5 text-danger" />
            <div>
              <p className="text-[13.5px] text-danger">{error}</p>
              <button
                onClick={fetchResume}
                className="mt-1 text-[12.5px] text-danger/70 underline-offset-2 hover:underline"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* No resume / upload */}
        {!loading && !error && (resumeData === null || replacing) && (
          <div className="space-y-4">
            {replacing && (
              <button
                onClick={() => setReplacing(false)}
                className="text-[13px] text-muted underline-offset-2 hover:underline dark:text-muted-dark"
              >
                ← Keep existing resume
              </button>
            )}
            {!replacing && (
              <div className="mb-6 rounded-xl border border-dashed border-line bg-paper px-6 py-10 text-center dark:border-line-dark dark:bg-paper-dark">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-line bg-surface dark:border-line-dark dark:bg-surface-dark">
                  <FileText className="h-5 w-5 text-muted dark:text-muted-dark" />
                </div>
                <p className="font-display text-[16px] font-medium text-ink dark:text-ink-dark">
                  No resume uploaded yet
                </p>
                <p className="mt-1.5 text-[13.5px] text-muted dark:text-muted-dark">
                  Upload your PDF resume to start the AI matching pipeline.
                </p>
              </div>
            )}
            <ResumeUploadZone onSuccess={handleSuccess} />
          </div>
        )}

        {/* Resume data */}
        {!loading && !error && resumeData && !replacing && (
          <ResumeDisplay
            data={resumeData}
            onDelete={handleDelete}
            onReplace={() => setReplacing(true)}
            deleting={deleting}
          />
        )}
      </div>
    </div>
  );
}
