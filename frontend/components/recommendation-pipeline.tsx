"use client";

import { useEffect, useState } from "react";
import {
  Upload,
  FileText,
  Brain,
  Search,
  Download,
  Cpu,
  GitCompare,
  ListOrdered,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";

const PIPELINE_STEPS = [
  { id: "upload", label: "Uploading resume", icon: Upload },
  { id: "parse", label: "Parsing resume", icon: FileText },
  { id: "skills", label: "Extracting skills", icon: Brain },
  { id: "experience", label: "Understanding experience", icon: Search },
  { id: "queries", label: "Generating search queries", icon: Search },
  { id: "fetch", label: "Fetching jobs", icon: Download },
  { id: "embeddings", label: "Computing embeddings", icon: Cpu },
  { id: "compare", label: "Comparing similarities", icon: GitCompare },
  { id: "rank", label: "Ranking jobs", icon: ListOrdered },
  { id: "done", label: "Done", icon: CheckCircle2 },
];

interface RecommendationPipelineProps {
  /** Which step index is active (0-9). Steps < current are "done", current is "active", rest are "pending" */
  currentStep: number;
  /** True when all steps are complete */
  complete?: boolean;
}

export function RecommendationPipeline({
  currentStep,
  complete = false,
}: RecommendationPipelineProps) {
  const [animatedStep, setAnimatedStep] = useState(-1);

  // Animate steps one by one up to currentStep
  useEffect(() => {
    if (animatedStep < currentStep) {
      const t = setTimeout(() => {
        setAnimatedStep((s) => s + 1);
      }, 320);
      return () => clearTimeout(t);
    }
  }, [animatedStep, currentStep]);

  return (
    <div className="rounded-xl2 border border-line bg-surface p-6 dark:border-line-dark dark:bg-surface-dark">
      <p className="mb-5 font-mono text-[10.5px] uppercase tracking-[0.2em] text-muted dark:text-muted-dark">
        Processing pipeline
      </p>

      <div className="space-y-3">
        {PIPELINE_STEPS.map((step, i) => {
          const isDone = complete ? i < PIPELINE_STEPS.length : i < animatedStep;
          const isActive = !complete && i === animatedStep;
          const isPending = !complete && i > animatedStep;

          return (
            <div
              key={step.id}
              className={cn(
                "flex items-center gap-3 transition-all duration-300",
                isPending && "opacity-30"
              )}
            >
              {/* Step icon */}
              <div
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full border transition-colors duration-300",
                  isDone &&
                    "border-signal/30 bg-signal-soft text-signal dark:bg-signal-soft-dark dark:text-signal-dark",
                  isActive &&
                    "border-ink bg-ink text-paper dark:border-ink-dark dark:bg-ink-dark dark:text-paper-dark",
                  isPending &&
                    "border-line bg-paper text-muted dark:border-line-dark dark:bg-paper-dark dark:text-muted-dark"
                )}
              >
                {isDone ? (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                ) : (
                  <step.icon
                    className={cn("h-3.5 w-3.5", isActive && "animate-pulse")}
                  />
                )}
              </div>

              {/* Label + progress bar for active */}
              <div className="flex-1 min-w-0">
                <p
                  className={cn(
                    "text-[13px] transition-colors duration-300",
                    isDone && "text-muted dark:text-muted-dark",
                    isActive && "font-medium text-ink dark:text-ink-dark",
                    isPending && "text-muted dark:text-muted-dark"
                  )}
                >
                  {step.label}
                </p>
                {isActive && (
                  <div className="mt-1 h-0.5 w-full overflow-hidden rounded-full bg-line dark:bg-line-dark">
                    <div className="h-full animate-[sweep_2s_ease-in-out_infinite] rounded-full bg-signal" />
                  </div>
                )}
              </div>

              {/* Done checkmark */}
              {isDone && (
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-signal dark:text-signal-dark" />
              )}
            </div>
          );
        })}
      </div>

      {complete && (
        <div className="mt-5 rounded-lg border border-signal/20 bg-signal-soft px-4 py-3 dark:bg-signal-soft-dark">
          <p className="text-[13px] font-medium text-ink dark:text-ink-dark">
            ✓ Resume processed successfully
          </p>
          <p className="mt-0.5 text-[12px] text-muted dark:text-muted-dark">
            Your recommendations will update on the next scheduled scan.
          </p>
        </div>
      )}
    </div>
  );
}

// Hook to drive the pipeline during upload
export function usePipelineProgress(
  isUploading: boolean,
  uploadPct: number,
  isComplete: boolean
) {
  const [step, setStep] = useState(-1);

  useEffect(() => {
    if (!isUploading && !isComplete) {
      setStep(-1);
      return;
    }

    if (isComplete) {
      setStep(9); // All done
      return;
    }

    if (isUploading) {
      setStep(0); // Uploading
    }
  }, [isUploading, isComplete]);

  // Advance through steps during upload based on progress
  useEffect(() => {
    if (!isUploading) return;

    // Map upload % to pipeline steps 0-8 (step 9 = done, set by parent)
    // upload 0-30% = step 0 (uploading)
    // upload 30-60% = steps 1-4 (parse, skills, experience, queries)
    // upload 60-90% = steps 5-7 (fetch, embeddings, compare)
    // upload 90-100% = step 8 (rank)
    let targetStep = 0;
    if (uploadPct >= 90) targetStep = 8;
    else if (uploadPct >= 70) targetStep = 7;
    else if (uploadPct >= 55) targetStep = 6;
    else if (uploadPct >= 40) targetStep = 5;
    else if (uploadPct >= 30) targetStep = 4;
    else if (uploadPct >= 22) targetStep = 3;
    else if (uploadPct >= 15) targetStep = 2;
    else if (uploadPct >= 8) targetStep = 1;
    else targetStep = 0;

    setStep(targetStep);
  }, [isUploading, uploadPct]);

  return step;
}
