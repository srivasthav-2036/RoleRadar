import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-line dark:border-line-dark">
      {/* Main footer row */}
      <div className="mx-auto max-w-6xl px-6 py-8 md:py-10">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          {/* Brand */}
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center gap-2">
              <svg width="14" height="14" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.4" opacity="0.3" />
                <circle cx="10" cy="10" r="5.5" stroke="currentColor" strokeWidth="1.4" opacity="0.6" />
                <circle cx="10" cy="10" r="2" fill="#B8862E" />
              </svg>
              <span className="font-display text-[13.5px] font-medium text-ink dark:text-ink-dark">
                RoleRadar
              </span>
            </div>
            <p className="text-[12px] text-muted dark:text-muted-dark">
              &copy; {new Date().getFullYear()} RoleRadar. All rights reserved.
            </p>
          </div>

          {/* Nav links */}
          <div className="flex items-center gap-5 text-[13px] text-muted dark:text-muted-dark">
            <a
              href="#how-it-works"
              className="transition-colors hover:text-ink dark:hover:text-ink-dark"
            >
              How it works
            </a>
            <Link
              href="/dashboard"
              className="transition-colors hover:text-ink dark:hover:text-ink-dark"
            >
              Dashboard
            </Link>
          </div>
        </div>

        {/* Provider notice */}
        <div className="mt-8 rounded-xl border border-line bg-surface px-5 py-4 dark:border-line-dark dark:bg-surface-dark">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:gap-6">
            <div className="flex-1">
              <p className="font-mono text-[10.5px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
                Platform Notice
              </p>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted dark:text-muted-dark">
                RoleRadar currently searches a{" "}
                <span className="text-ink dark:text-ink-dark font-medium">
                  limited number of job providers
                </span>
                . More providers are continuously being added. We recommend continuing to
                search on other job platforms (LinkedIn, Indeed, Glassdoor, etc.) alongside
                RoleRadar.{" "}
                <span className="text-muted/70 dark:text-muted-dark/70">
                  This project is still under active development.
                </span>
              </p>
            </div>

            <div className="shrink-0 border-t border-line pt-3 sm:border-l sm:border-t-0 sm:pl-6 sm:pt-0 dark:border-line-dark">
              <p className="font-mono text-[10.5px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
                Found a bug?
              </p>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted dark:text-muted-dark">
                Email us at{" "}
                <a
                  href="mailto:roleradar.notifications@gmail.com"
                  className="text-ink underline-offset-2 hover:underline dark:text-ink-dark"
                >
                  roleradar.notifications@gmail.com
                </a>
                <br />
                <span className="text-[11.5px] text-muted/70 dark:text-muted-dark/70">
                  Include screenshots or a short description.
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
