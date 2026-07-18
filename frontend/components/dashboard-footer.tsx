"use client";

import Link from "next/link";

/**
 * Compact footer for use inside the dashboard layout (sidebar pages).
 * Sits at the bottom of the scrollable content area for each page.
 */
export function DashboardFooter() {
  return (
    <footer className="mt-12 border-t border-line dark:border-line-dark">
      <div className="px-6 py-6 md:px-10">
        {/* Provider notice */}
        <div className="rounded-xl border border-line bg-surface px-4 py-3.5 dark:border-line-dark dark:bg-surface-dark">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:gap-8">
            <div className="flex-1">
              <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
                Platform Notice
              </p>
              <p className="mt-1 text-[12px] leading-relaxed text-muted dark:text-muted-dark">
                RoleRadar currently searches a{" "}
                <span className="font-medium text-ink dark:text-ink-dark">
                  limited number of job providers
                </span>
                . More are being added continuously. We recommend also searching LinkedIn, Indeed,
                and Glassdoor.{" "}
                <span className="text-muted/60 dark:text-muted-dark/60">
                  This project is under active development.
                </span>
              </p>
            </div>

            <div className="shrink-0 border-t border-line pt-2.5 sm:border-l sm:border-t-0 sm:pl-6 sm:pt-0 dark:border-line-dark">
              <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
                Found a bug?
              </p>
              <p className="mt-1 text-[12px] leading-relaxed text-muted dark:text-muted-dark">
                Email{" "}
                <a
                  href="mailto:roleradar.notifications@gmail.com"
                  className="text-ink underline-offset-2 hover:underline dark:text-ink-dark"
                >
                  roleradar.notifications@gmail.com
                </a>
                <br />
                <span className="text-[11px] text-muted/60 dark:text-muted-dark/60">
                  Screenshots or a description help a lot.
                </span>
              </p>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-3 flex flex-col items-center justify-between gap-2 text-[11.5px] text-muted dark:text-muted-dark sm:flex-row">
          <p>&copy; {new Date().getFullYear()} RoleRadar. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <Link href="/" className="transition-colors hover:text-ink dark:hover:text-ink-dark">
              Home
            </Link>
            <Link href="/dashboard" className="transition-colors hover:text-ink dark:hover:text-ink-dark">
              Dashboard
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
