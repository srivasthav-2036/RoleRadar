"use client";

import { useEffect, useRef } from "react";
import { Loader2, CheckCircle2, Sparkles, X } from "lucide-react";
import { usePipelineStatus } from "@/lib/pipeline-status-context";

interface PipelineStatusBannerProps {
  /** Called when pipeline reaches "done" — use to refresh page data */
  onComplete?: () => void;
}

export function PipelineStatusBanner({
  onComplete,
}: PipelineStatusBannerProps) {
  const { status, displayStep, isClosed, closeBanner } = usePipelineStatus();
  const doneCalledRef = useRef(false);

  useEffect(() => {
    if (status === "running") {
      doneCalledRef.current = false;
    }
    if (status === "done" && !doneCalledRef.current) {
      doneCalledRef.current = true;
      onComplete?.();
    }
  }, [status, onComplete]);

  if (status === "idle" || isClosed) return null;

  if (status === "done") {
    return (
      <div className="mb-6 rounded-xl border border-signal/25 bg-signal-soft/60 px-5 py-4 dark:bg-signal-soft-dark/40">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-signal" />
          <div className="flex-1 min-w-0">
            <p className="text-[13.5px] font-medium text-ink dark:text-ink-dark">
              Recommendations updated
            </p>
            <p className="mt-1 text-[12.5px] leading-relaxed text-muted dark:text-muted-dark">
              We continuously scan for new jobs every 4 hours. If we find better matches,
              we&apos;ll automatically recommend them and notify you by email.
            </p>
          </div>
          <button
            onClick={closeBanner}
            className="rounded-lg p-1 text-muted hover:bg-line/50 hover:text-ink dark:text-muted-dark dark:hover:bg-line-dark/50 dark:hover:text-ink-dark transition-colors shrink-0"
            aria-label="Close banner"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  // running
  return (
    <div className="mb-6 rounded-xl border border-line bg-surface px-5 py-4 dark:border-line-dark dark:bg-surface-dark">
      <div className="flex items-center gap-3">
        <div className="relative flex h-8 w-8 shrink-0 items-center justify-center">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal/15" />
          <Loader2 className="h-4 w-4 animate-spin text-signal" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[13px] font-medium text-ink dark:text-ink-dark">
            Running recommendation pipeline…
          </p>
          <p className="mt-0.5 truncate text-[12px] text-muted dark:text-muted-dark">
            {displayStep}
          </p>
        </div>
        <Sparkles className="h-4 w-4 shrink-0 text-signal/50" />
        <button
          onClick={closeBanner}
          className="rounded-lg p-1 text-muted hover:bg-line/50 hover:text-ink dark:text-muted-dark dark:hover:bg-line-dark/50 dark:hover:text-ink-dark transition-colors shrink-0"
          aria-label="Close banner"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Indeterminate progress bar */}
      <div className="mt-3 h-0.5 w-full overflow-hidden rounded-full bg-line dark:bg-line-dark">
        <div
          className="h-full rounded-full bg-signal"
          style={{ animation: "progress-slide 2s ease-in-out infinite" }}
        />
      </div>

      <style>{`
        @keyframes progress-slide {
          0%   { width: 0%;   margin-left: 0;    }
          50%  { width: 60%;  margin-left: 20%;  }
          100% { width: 0%;   margin-left: 100%; }
        }
      `}</style>
    </div>
  );
}
