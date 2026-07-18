"use client";

import { useEffect, useState } from "react";

// ─── Rotating messages ───────────────────────────────────────────────────────

const MESSAGES = [
  { text: "Scanning your matches…", sub: "This may take a moment on first load." },
  { text: "Connecting to RoleRadar…", sub: "Waking up the server — hang tight." },
  { text: "Analysing your profile…", sub: "Great opportunities are worth the wait." },
  { text: "Preparing your dashboard…", sub: "AI-powered insights loading." },
  { text: "Fetching recommendations…", sub: "Finding roles that fit you best." },
  { text: "Almost there…", sub: "Loading your personalised data." },
  { text: "Ranking your top matches…", sub: "Sorting by how well each role fits you." },
  { text: "Your career radar is active…", sub: "Monitoring the job market for you." },
];

import { useNavigationLoading } from "@/lib/navigation-context";

// ─── Nav Progress Bar ────────────────────────────────────────────────────────
// Thin top progress bar that animates during route transitions.

export function NavigationProgress() {
  const { isLoading, progress } = useNavigationLoading();

  if (!isLoading) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-[100] h-0.5 bg-transparent">
      <div
        className="h-full bg-signal transition-all duration-300 ease-out"
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}

// ─── Full-page loading screen ─────────────────────────────────────────────────

export function PageLoadingScreen({ hint }: { hint?: string }) {
  const [msgIdx, setMsgIdx] = useState(0);

  useEffect(() => {
    // Rotate message every 2.5 s
    const interval = setInterval(() => {
      setMsgIdx((i) => (i + 1) % MESSAGES.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  const msg = MESSAGES[msgIdx];

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 bg-paper dark:bg-paper-dark">
      {/* Animated radar rings */}
      <div className="relative flex h-20 w-20 items-center justify-center">
        <span
          className="absolute inline-flex h-full w-full animate-ping rounded-full bg-ink/10 dark:bg-ink-dark/10"
          style={{ animationDuration: "2.2s" }}
        />
        <span
          className="absolute inline-flex h-14 w-14 animate-ping rounded-full bg-ink/8 dark:bg-ink-dark/8"
          style={{ animationDuration: "2.2s", animationDelay: "0.5s" }}
        />
        {/* Logo mark */}
        <svg
          width="30"
          height="30"
          viewBox="0 0 20 20"
          fill="none"
          className="relative z-10 text-ink dark:text-ink-dark"
        >
          <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.2" opacity="0.25" />
          <circle cx="10" cy="10" r="5.5" stroke="currentColor" strokeWidth="1.2" opacity="0.55" />
          <circle cx="10" cy="10" r="2" fill="#B8862E" />
        </svg>
      </div>

      {/* Brand */}
      <span className="font-display text-[15px] font-medium tracking-tight text-ink dark:text-ink-dark">
        RoleRadar
      </span>

      {/* Rotating message */}
      <div
        key={msgIdx}
        className="flex flex-col items-center gap-1.5 text-center transition-all duration-500"
        style={{ animation: "fadeIn 0.4s ease" }}
      >
        <p className="text-[14px] font-medium text-ink dark:text-ink-dark">
          {hint ?? msg.text}
        </p>
        {!hint && (
          <p className="text-[12.5px] text-muted dark:text-muted-dark">
            {msg.sub}
          </p>
        )}
      </div>

      {/* Dot loader */}
      <div className="flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 rounded-full bg-muted dark:bg-muted-dark animate-bounce"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to   { opacity: 1; transform: translateY(0);   }
        }
      `}</style>
    </div>
  );
}
