import Link from "next/link";
import { ThemeToggle } from "./theme-toggle";

function LogoMark() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.2" opacity="0.35" />
      <circle cx="10" cy="10" r="5.5" stroke="currentColor" strokeWidth="1.2" opacity="0.6" />
      <circle cx="10" cy="10" r="2" fill="#B8862E" />
    </svg>
  );
}

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-line/70 bg-paper/80 backdrop-blur-md dark:border-line-dark/70 dark:bg-paper-dark/80">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2.5 text-ink dark:text-ink-dark">
          <LogoMark />
          <span className="font-display text-[15px] font-medium tracking-tight">RoleRadar</span>
        </Link>

        <nav className="hidden items-center gap-8 text-[13.5px] text-muted dark:text-muted-dark md:flex">
          <Link href="#how-it-works" className="transition-colors hover:text-ink dark:hover:text-ink-dark">
            How it works
          </Link>
          <Link href="#features" className="transition-colors hover:text-ink dark:hover:text-ink-dark">
            Product
          </Link>
          <Link href="/dashboard" className="transition-colors hover:text-ink dark:hover:text-ink-dark">
            Dashboard
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Link
            href="/dashboard"
            className="rounded-full bg-ink px-4 py-[7px] text-[13px] font-medium text-paper transition-colors hover:bg-ink/85 dark:bg-ink-dark dark:text-paper-dark dark:hover:bg-ink-dark/85"
          >
            Get started
          </Link>
        </div>
      </div>
    </header>
  );
}
