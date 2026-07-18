"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, ArrowRight, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useNavigationLoading } from "@/lib/navigation-context";

function LogoMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.2" opacity="0.35" />
      <circle cx="10" cy="10" r="5.5" stroke="currentColor" strokeWidth="1.2" opacity="0.6" />
      <circle cx="10" cy="10" r="2" fill="#B8862E" />
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const { startLoading } = useNavigationLoading();
  const { login, isLoading, error, clearError, user } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      startLoading();
      router.replace("/dashboard");
    }
  }, [user, router, startLoading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    clearError();
    setSubmitting(true);
    try {
      await login(email, password);
      startLoading();
      router.replace("/dashboard");
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setSubmitting(false);
    }
  }

  const displayError = formError || error;

  return (
    <div className="flex min-h-screen bg-paper dark:bg-paper-dark">
      {/* ── Left panel (brand) ── */}
      <div className="relative hidden w-[52%] flex-col justify-between overflow-hidden bg-depth p-14 lg:flex">
        {/* Subtle grid pattern */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
        {/* Soft glow */}
        <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-signal/10 blur-[120px]" />
        <div className="pointer-events-none absolute -bottom-24 right-0 h-80 w-80 rounded-full bg-signal/8 blur-[100px]" />

        {/* Logo */}
        <div className="relative flex items-center gap-3">
          <LogoMark />
          <span className="font-display text-[16px] font-medium tracking-tight text-white/90">
            RoleRadar
          </span>
        </div>

        {/* Hero text */}
        <div className="relative space-y-8">
          <div>
            <p className="font-mono text-[10.5px] uppercase tracking-[0.2em] text-signal">
              AI-powered job matching
            </p>
            <h1 className="mt-4 font-display text-[2.6rem] font-medium leading-[1.1] tracking-tight text-white">
              Stop scrolling.
              <br />
              <span className="text-signal">Let the roles find you.</span>
            </h1>
            <p className="mt-5 max-w-sm text-[15px] leading-relaxed text-white/55">
              Upload your resume once — RoleRadar scans thousands of listings every
              4 hours and surfaces only the roles that actually match your profile.
            </p>
          </div>

          {/* Feature bullets */}
          <div className="space-y-3">
            {[
              "Scores every role against your real skills",
              "Explains exactly why it's a match",
              "Tailors your resume for top picks",
            ].map((f) => (
              <div key={f} className="flex items-center gap-3">
                <div className="h-1.5 w-1.5 shrink-0 rounded-full bg-signal" />
                <span className="text-[13.5px] text-white/65">{f}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="relative font-mono text-[11px] text-white/25">
          © {new Date().getFullYear()} RoleRadar
        </p>
      </div>

      {/* ── Right panel (form) ── */}
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-[380px]">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <LogoMark />
            <span className="font-display text-[15px] font-medium tracking-tight text-ink dark:text-ink-dark">
              RoleRadar
            </span>
          </div>

          <div className="mb-8">
            <h2 className="font-display text-[1.7rem] font-medium tracking-tight text-ink dark:text-ink-dark">
              Welcome back
            </h2>
            <p className="mt-1.5 text-[14px] text-muted dark:text-muted-dark">
              Don&apos;t have an account?{" "}
              <Link
                href="/register"
                className="text-ink underline-offset-2 hover:underline dark:text-ink-dark"
              >
                Sign up free
              </Link>
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="mb-1.5 block text-[13px] font-medium text-ink dark:text-ink-dark"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-lg border border-line bg-surface px-3.5 py-2.5 text-[14px] text-ink placeholder:text-muted/60 transition-colors focus:border-signal/50 focus:outline-none dark:border-line-dark dark:bg-surface-dark dark:text-ink-dark dark:placeholder:text-muted-dark/60 dark:focus:border-signal/40"
              />
            </div>

            {/* Password */}
            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="text-[13px] font-medium text-ink dark:text-ink-dark"
                >
                  Password
                </label>
                <Link
                  href="/forgot-password"
                  className="text-[12.5px] text-muted transition-colors hover:text-ink dark:text-muted-dark dark:hover:text-ink-dark"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-lg border border-line bg-surface px-3.5 py-2.5 pr-10 text-[14px] text-ink placeholder:text-muted/60 transition-colors focus:border-signal/50 focus:outline-none dark:border-line-dark dark:bg-surface-dark dark:text-ink-dark dark:placeholder:text-muted-dark/60 dark:focus:border-signal/40"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted transition-colors hover:text-ink dark:text-muted-dark dark:hover:text-ink-dark"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Error */}
            {displayError && (
              <div className="rounded-lg border border-danger/25 bg-danger/8 px-4 py-3 text-[13px] text-danger dark:bg-danger/10">
                {displayError}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={submitting || isLoading}
              id="login-submit"
              className="group mt-1 flex w-full items-center justify-center gap-2 rounded-lg bg-ink py-2.5 text-[14px] font-medium text-paper transition-all hover:bg-ink/85 disabled:opacity-60 dark:bg-ink-dark dark:text-paper-dark dark:hover:bg-ink-dark/85"
            >
              {submitting || isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  Sign in
                  <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
