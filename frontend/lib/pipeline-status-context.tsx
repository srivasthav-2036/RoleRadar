"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  useCallback,
} from "react";
import { resumesApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const STAGES = [
  "Analyzing your resume\u2026",
  "Updating your profile\u2026",
  "Finding the best matches from our current job database\u2026",
  "Ranking recommendations\u2026",
  "Preparing your personalized recommendations\u2026",
  "Sending your recommendation email\u2026",
];

interface PipelineStatusContextType {
  status: "idle" | "running" | "done";
  step: string;
  displayStep: string;
  isClosed: boolean;
  closeBanner: () => void;
  triggerRefresh: () => void;
}

const PipelineStatusContext = createContext<PipelineStatusContextType | null>(
  null
);

export function PipelineStatusProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, token } = useAuth();
  const [status, setStatus] = useState<"idle" | "running" | "done">("idle");
  const [step, setStep] = useState(STAGES[0]);
  const [localIdx, setLocalIdx] = useState(0);
  const [isClosed, setIsClosed] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stageRotatorRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const dismissTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Trigger status check manually (e.g., on upload or manual refresh)
  const triggerRefresh = useCallback(() => {
    setIsClosed(false);
    setStatus("running");
    setRefreshTrigger((prev) => prev + 1);
  }, []);

  // Stage message rotator for visual progress
  useEffect(() => {
    if (status !== "running") {
      if (stageRotatorRef.current) clearInterval(stageRotatorRef.current);
      return;
    }
    stageRotatorRef.current = setInterval(() => {
      setLocalIdx((i) => (i + 1) % STAGES.length);
    }, 2800);
    return () => {
      if (stageRotatorRef.current) clearInterval(stageRotatorRef.current);
    };
  }, [status]);

  // Polling pipeline status
  useEffect(() => {
    if (!user || !token) {
      setStatus("idle");
      return;
    }

    let isMounted = true;

    // Helper to start the polling loop
    const startPolling = () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (dismissTimeoutRef.current) {
        clearTimeout(dismissTimeoutRef.current);
      }

      intervalRef.current = setInterval(async () => {
        try {
          const res = await resumesApi.pipelineStatus();
          if (!isMounted) return;

          if (res.status === "running") {
            setStatus((prev) => {
              if (prev !== "running") {
                setIsClosed(false);
              }
              return "running";
            });
            if (res.step) setStep(res.step);
          } else if (res.status === "done") {
            setStatus("done");
            if (res.step) setStep(res.step);

            // Stop polling immediately
            if (intervalRef.current) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }

            // Dismiss automatically after 3 seconds
            dismissTimeoutRef.current = setTimeout(() => {
              if (isMounted) setStatus("idle");
            }, 3000);
          } else {
            // idle
            setStatus("idle");
            if (intervalRef.current) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }
          }
        } catch {
          // ignore poll errors
        }
      }, 2500);
    };

    // On initial check or when refreshTrigger is triggered
    resumesApi
      .pipelineStatus()
      .then((res) => {
        if (!isMounted) return;

        // If this is a manual trigger or the status is actively running, start polling
        if (refreshTrigger > 0 || res.status === "running") {
          if (res.status === "running") {
            setStatus("running");
            if (res.step) setStep(res.step);
            startPolling();
          } else if (res.status === "done") {
            // Show done, then auto-dismiss (relevant if manual trigger finishes instantly)
            setStatus("done");
            if (res.step) setStep(res.step);
            dismissTimeoutRef.current = setTimeout(() => {
              if (isMounted) setStatus("idle");
            }, 3000);
          } else {
            setStatus("idle");
          }
        } else {
          // On fresh load, if not actively running, remain idle
          setStatus("idle");
        }
      })
      .catch(() => {
        if (isMounted) setStatus("idle");
      });

    return () => {
      isMounted = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (dismissTimeoutRef.current) {
        clearTimeout(dismissTimeoutRef.current);
        dismissTimeoutRef.current = null;
      }
    };
  }, [user, token, refreshTrigger]);

  const closeBanner = useCallback(() => {
    setIsClosed(true);
  }, []);

  const displayStep = status === "running" ? STAGES[localIdx] : step;

  return (
    <PipelineStatusContext.Provider
      value={{
        status,
        step,
        displayStep,
        isClosed,
        closeBanner,
        triggerRefresh,
      }}
    >
      {children}
    </PipelineStatusContext.Provider>
  );
}

export function usePipelineStatus() {
  const context = useContext(PipelineStatusContext);
  if (!context) {
    throw new Error(
      "usePipelineStatus must be used within a PipelineStatusProvider"
    );
  }
  return context;
}
