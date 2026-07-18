import Link from "next/link";
import { MatchDial } from "./match-dial";
import { ArrowUpRight } from "lucide-react";

export function Hero() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-20 pt-16 md:pb-28 md:pt-24">
      <div className="grid items-center gap-16 md:grid-cols-[1.1fr_1fr]">
        <div className="animate-fade-up">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-line px-3 py-1 text-[11.5px] text-muted dark:border-line-dark dark:text-muted-dark">
            <span className="h-1.5 w-1.5 rounded-full bg-signal" />
            Scanning 6 job boards, every 4 hours
          </div>

          <h1 className="font-display text-balance text-[2.65rem] font-medium leading-[1.08] tracking-tight text-ink dark:text-ink-dark md:text-[3.4rem]">
            Stop scrolling job boards.
            <br />
            Let the roles find <span className="text-signal">you</span>.
          </h1>

          <p className="mt-6 max-w-md text-balance text-[16.5px] leading-relaxed text-muted dark:text-muted-dark">
            RoleRadar reads your resume, scores every open role against it, and tells you
            exactly why it's a match — then tailors your resume for the ones worth applying to.
          </p>

          <div className="mt-9 flex items-center gap-4">
            <Link
              href="/dashboard"
              className="group inline-flex items-center gap-1.5 rounded-full bg-ink px-5 py-3 text-[14px] font-medium text-paper transition-colors hover:bg-ink/85 dark:bg-ink-dark dark:text-paper-dark dark:hover:bg-ink-dark/85"
            >
              Upload your resume
              <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </Link>
            <a
              href="#how-it-works"
              className="text-[14px] font-medium text-muted transition-colors hover:text-ink dark:text-muted-dark dark:hover:text-ink-dark"
            >
              See how it works
            </a>
          </div>

          <div className="mt-1 h-px w-full max-w-md origin-left animate-sweep bg-gradient-to-r from-line to-transparent dark:from-line-dark" />
        </div>

        <div className="relative animate-fade-up [animation-delay:150ms] flex items-center justify-center">
          {/* Glowing background blob */}
          <div className="absolute -z-10 h-72 w-72 rounded-full bg-signal/10 blur-[80px] dark:bg-signal/5" />
          
          <div className="relative flex h-[350px] w-[350px] items-center justify-center rounded-full border border-line bg-surface/30 backdrop-blur-sm dark:border-line-dark dark:bg-surface-dark/30">
            {/* Outer dotted orbit */}
            <div className="absolute h-[300px] w-[300px] rounded-full border border-dashed border-line/60 dark:border-line-dark/60 animate-[spin_40s_linear_infinite]" />
            
            {/* Middle orbit */}
            <div className="absolute h-[220px] w-[220px] rounded-full border border-line dark:border-line-dark" />
            
            {/* Inner orbit */}
            <div className="absolute h-[140px] w-[140px] rounded-full border border-line dark:border-line-dark" />
            
            {/* Glowing sweep scanner ray */}
            <div className="absolute inset-0 rounded-full animate-[spin_6s_linear_infinite]"
                 style={{
                   background: "conic-gradient(from 0deg, transparent 50%, rgba(184, 134, 46, 0.15) 100%)",
                 }}
            />
            
            {/* Center radar hub */}
            <div className="relative z-10 flex h-14 w-14 items-center justify-center rounded-full bg-ink text-paper shadow-card dark:bg-ink-dark dark:text-paper-dark animate-pulse">
              <svg width="24" height="24" viewBox="0 0 20 20" fill="none">
                <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.2" opacity="0.35" />
                <circle cx="10" cy="10" r="5.5" stroke="currentColor" strokeWidth="1.2" opacity="0.6" />
                <circle cx="10" cy="10" r="2" fill="#B8862E" />
              </svg>
            </div>

            {/* Glowing active match points (constellation style) */}
            <div className="absolute top-[20%] left-[25%] flex flex-col items-center gap-1.5 animate-bounce [animation-delay:0.2s]">
              <span className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal opacity-75" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-signal" />
              </span>
              <span className="rounded bg-surface/80 px-2 py-0.5 font-mono text-[9px] text-ink shadow border border-line dark:bg-surface-dark/80 dark:text-ink-dark dark:border-line-dark">
                AI Engineer Match: 98%
              </span>
            </div>

            <div className="absolute bottom-[25%] right-[15%] flex flex-col items-center gap-1.5 animate-bounce [animation-delay:0.8s]">
              <span className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-500 opacity-75" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-blue-500" />
              </span>
              <span className="rounded bg-surface/80 px-2 py-0.5 font-mono text-[9px] text-ink shadow border border-line dark:bg-surface-dark/80 dark:text-ink-dark dark:border-line-dark">
                SDE Match: 92%
              </span>
            </div>

            <div className="absolute top-[45%] right-[0%] flex flex-col items-center gap-1.5 animate-bounce [animation-delay:0.5s]">
              <span className="relative flex h-2 w-2">
                <span className="relative inline-flex h-2 w-2 rounded-full bg-signal/70" />
              </span>
              <span className="rounded bg-surface/80 px-2 py-0.5 font-mono text-[9px] text-ink shadow border border-line dark:bg-surface-dark/80 dark:text-ink-dark dark:border-line-dark">
              Data Engineer Match: 86%
              </span>
            </div>

            <div className="absolute bottom-[20%] left-[10%] flex flex-col items-center gap-1.5 animate-bounce [animation-delay:1.1s]">
              <span className="relative flex h-2.5 w-2.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-500/50 opacity-75" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-blue-400" />
              </span>
              <span className="rounded bg-surface/80 px-2 py-0.5 font-mono text-[9px] text-ink shadow border border-line dark:bg-surface-dark/80 dark:text-ink-dark dark:border-line-dark">
                Systems Engineer Match: 89%
              </span>
            </div>

            {/* Orbiting labels */}
            <div className="absolute top-[10%] right-[30%] rotate-12 select-none rounded-full border border-line/40 bg-surface/20 px-3 py-1 font-mono text-[10px] text-muted dark:border-line-dark/40 dark:bg-surface-dark/20 dark:text-muted-dark animate-[pulse_3s_ease-in-out_infinite]">
              PyTorch
            </div>
            
            <div className="absolute bottom-[10%] left-[32%] -rotate-12 select-none rounded-full border border-line/40 bg-surface/20 px-3 py-1 font-mono text-[10px] text-muted dark:border-line-dark/40 dark:bg-surface-dark/20 dark:text-muted-dark animate-[pulse_4s_ease-in-out_infinite]">
              FastAPI
            </div>
          </div>
          
          <div className="absolute -bottom-4 -right-4 -z-20 h-[360px] w-[360px] rounded-full border border-line/40 dark:border-line-dark/40" />
        </div>
      </div>
    </section>
  );
}
