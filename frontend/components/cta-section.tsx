import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

export function CtaSection() {
  return (
    <section className="border-t border-line py-24 dark:border-line-dark">
      <div className="mx-auto max-w-6xl px-6">
        <div className="flex flex-col items-start justify-between gap-8 rounded-xl2 border border-line bg-surface p-10 dark:border-line-dark dark:bg-surface-dark md:flex-row md:items-center md:p-14">
          <div>
            <h2 className="font-display text-[1.9rem] font-medium tracking-tight text-ink dark:text-ink-dark">
              Your next role is already posted somewhere.
            </h2>
            <p className="mt-2 max-w-md text-[14.5px] text-muted dark:text-muted-dark">
              RoleRadar just has to find it before you scroll past it.
            </p>
          </div>
          <Link
            href="/dashboard"
            className="group flex shrink-0 items-center gap-1.5 rounded-full bg-ink px-5 py-3 text-[14px] font-medium text-paper transition-colors hover:bg-ink/85 dark:bg-ink-dark dark:text-paper-dark dark:hover:bg-ink-dark/85"
          >
            Upload your resume
            <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </Link>
        </div>
      </div>
    </section>
  );
}
