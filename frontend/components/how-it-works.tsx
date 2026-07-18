const stages = [
  {
    n: "01",
    title: "Upload your resume",
    body: "RoleRadar reads it once — your skills, projects, and experience become a structured profile, not just a PDF.",
  },
  {
    n: "02",
    title: "It scans, you don't",
    body: "Every 4 hours, RoleRadar checks fresh listings across job boards and scores each one against your actual profile.",
  },
  {
    n: "03",
    title: "Apply with a tailored resume",
    body: "For roles that clear the bar, get a one-click resume tailored to that specific listing — ready to send.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="border-t border-line py-24 dark:border-line-dark">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-14 max-w-lg">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-signal">The process</p>
          <h2 className="mt-3 font-display text-[2rem] font-medium tracking-tight text-ink dark:text-ink-dark">
            Three stages, running quietly in the background.
          </h2>
        </div>

        <div className="grid gap-x-8 gap-y-14 md:grid-cols-3">
          {stages.map((stage, i) => (
            <div key={stage.n} className="relative">
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-[13px] text-signal">{stage.n}</span>
                <div className="h-px flex-1 bg-line dark:bg-line-dark" />
              </div>
              <h3 className="mt-4 font-display text-[19px] font-medium text-ink dark:text-ink-dark">
                {stage.title}
              </h3>
              <p className="mt-2.5 text-[14.5px] leading-relaxed text-muted dark:text-muted-dark">
                {stage.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
