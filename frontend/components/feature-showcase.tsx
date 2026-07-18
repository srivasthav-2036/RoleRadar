export function FeatureShowcase() {
  return (
    <section id="features" className="border-t border-line py-24 dark:border-line-dark">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-14 max-w-lg">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-signal">Under the hood</p>
          <h2 className="mt-3 font-display text-[2rem] font-medium tracking-tight text-ink dark:text-ink-dark">
            Built to be precise, not impressive.
          </h2>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {/* Feature 1: scoring, not a badge */}
          <div className="rounded-xl2 border border-line bg-surface p-6 dark:border-line-dark dark:bg-surface-dark">
            <p className="font-display text-[16px] font-medium text-ink dark:text-ink-dark">
              Scoring you can audit
            </p>
            <p className="mt-2 text-[13.5px] leading-relaxed text-muted dark:text-muted-dark">
              Every match score breaks down into required skills, experience fit, and
              project relevance — never a black box.
            </p>
            <div className="mt-5 space-y-2 rounded-lg border border-line bg-paper p-3.5 font-mono text-[11.5px] dark:border-line-dark dark:bg-paper-dark">
              <div className="flex justify-between text-muted dark:text-muted-dark">
                <span>skills</span>
                <span className="text-ink dark:text-ink-dark">92</span>
              </div>
              <div className="flex justify-between text-muted dark:text-muted-dark">
                <span>projects</span>
                <span className="text-ink dark:text-ink-dark">88</span>
              </div>
              <div className="flex justify-between border-t border-line pt-2 text-muted dark:border-line-dark dark:text-muted-dark">
                <span>overall</span>
                <span className="text-signal">94</span>
              </div>
            </div>
          </div>

          {/* Feature 2: tailoring */}
          <div className="rounded-xl2 border border-line bg-surface p-6 dark:border-line-dark dark:bg-surface-dark">
            <p className="font-display text-[16px] font-medium text-ink dark:text-ink-dark">
              Tailored, never invented
            </p>
            <p className="mt-2 text-[13.5px] leading-relaxed text-muted dark:text-muted-dark">
              RoleRadar reorders and reframes what's already true on your resume — it
              never fabricates experience to fit a listing.
            </p>
            <div className="mt-5 space-y-1.5 rounded-lg border border-line bg-paper p-3.5 text-[12px] leading-relaxed dark:border-line-dark dark:bg-paper-dark">
              <p className="text-muted line-through decoration-line dark:text-muted-dark dark:decoration-line-dark">
                Built internal tools for the data team
              </p>
              <p className="text-ink dark:text-ink-dark">
                Built <span className="bg-signal-soft px-0.5 dark:bg-signal-soft-dark">Python</span> tooling
                that cut data-team turnaround by 40%
              </p>
            </div>
          </div>

          {/* Feature 3: notifications */}
          <div className="rounded-xl2 border border-line bg-surface p-6 dark:border-line-dark dark:bg-surface-dark">
            <p className="font-display text-[16px] font-medium text-ink dark:text-ink-dark">
              A ping only when it matters
            </p>
            <p className="mt-2 text-[13.5px] leading-relaxed text-muted dark:text-muted-dark">
              No daily digest of noise. You hear from RoleRadar when a role clears your
              bar — nothing else.
            </p>
            <div className="mt-5 rounded-lg border border-line bg-paper p-3.5 dark:border-line-dark dark:bg-paper-dark">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-muted dark:text-muted-dark">
                  RoleRadar
                </span>
                <span className="font-mono text-[10.5px] text-muted dark:text-muted-dark">now</span>
              </div>
              <p className="mt-1.5 text-[12.5px] text-ink dark:text-ink-dark">
                3 new matches above 85 — including a role at Vercel.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
