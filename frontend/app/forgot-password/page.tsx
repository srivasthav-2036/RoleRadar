"use client";

import Link from "next/link";
import { ArrowLeft, Mail } from "lucide-react";

function LogoMark() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.2" opacity="0.35" />
      <circle cx="10" cy="10" r="5.5" stroke="currentColor" strokeWidth="1.2" opacity="0.6" />
      <circle cx="10" cy="10" r="2" fill="#B8862E" />
    </svg>
  );
}

export default function ForgotPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-6 dark:bg-paper-dark">
      <div className="w-full max-w-[400px]">
        {/* Logo */}
        <Link
          href="/"
          className="mb-12 flex items-center gap-2.5 text-ink dark:text-ink-dark"
        >
          <LogoMark />
          <span className="font-display text-[15px] font-medium tracking-tight">
            RoleRadar
          </span>
        </Link>

        {/* Icon */}
        <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl border border-line bg-surface dark:border-line-dark dark:bg-surface-dark">
          <Mail className="h-5 w-5 text-signal" strokeWidth={1.75} />
        </div>

        <h1 className="font-display text-[1.6rem] font-medium tracking-tight text-ink dark:text-ink-dark">
          Forgot your password?
        </h1>
        <p className="mt-2 text-[14px] leading-relaxed text-muted dark:text-muted-dark">
          Password reset via email is on our roadmap. In the meantime, if you
          can&apos;t access your account, please reach out and we&apos;ll help you
          manually.
        </p>

        {/* Coming soon notice */}
        <div className="mt-6 rounded-xl border border-signal/20 bg-signal-soft px-5 py-4 dark:bg-signal-soft-dark">
          <p className="font-mono text-[10.5px] uppercase tracking-[0.15em] text-signal">
            Coming soon
          </p>
          <p className="mt-1.5 text-[13px] text-ink dark:text-ink-dark">
            We&apos;re building email-based password reset. You&apos;ll be notified
            when it&apos;s available.
          </p>
        </div>

        <Link
          href="/login"
          className="mt-8 inline-flex items-center gap-2 text-[13.5px] text-muted transition-colors hover:text-ink dark:text-muted-dark dark:hover:text-ink-dark"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to login
        </Link>
      </div>
    </div>
  );
}
