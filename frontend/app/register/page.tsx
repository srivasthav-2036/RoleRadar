"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Eye,
  EyeOff,
  ArrowRight,
  Loader2,
  Check,
  MailCheck,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useNavigationLoading } from "@/lib/navigation-context";
import { authApi, ApiError, setToken } from "@/lib/api";

// ─── OTP Resend cooldown (seconds) ───────────────────────────────────────────
const RESEND_COOLDOWN = 60;

function LogoMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.2" opacity="0.35" />
      <circle cx="10" cy="10" r="5.5" stroke="currentColor" strokeWidth="1.2" opacity="0.6" />
      <circle cx="10" cy="10" r="2" fill="#B8862E" />
    </svg>
  );
}

function PasswordStrength({ password }: { password: string }) {
  const checks = [
    { label: "At least 8 characters", ok: password.length >= 8 },
    { label: "Contains a number", ok: /\d/.test(password) },
    { label: "Contains a letter", ok: /[a-zA-Z]/.test(password) },
  ];
  if (!password) return null;
  return (
    <div className="mt-2 space-y-1">
      {checks.map(({ label, ok }) => (
        <div key={label} className="flex items-center gap-1.5 text-[11.5px]">
          <Check
            className={`h-3 w-3 transition-colors ${
              ok ? "text-signal" : "text-line dark:text-line-dark"
            }`}
          />
          <span className={ok ? "text-ink dark:text-ink-dark" : "text-muted dark:text-muted-dark"}>
            {label}
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── OTP Input (6 boxes) ──────────────────────────────────────────────────────
function OtpInput({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
}) {
  const refs = useRef<(HTMLInputElement | null)[]>([]);

  function handleKey(i: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !value[i] && i > 0) {
      refs.current[i - 1]?.focus();
    }
  }

  function handleChange(i: number, v: string) {
    const digit = v.replace(/\D/g, "").slice(-1);
    const arr = value.split("").concat(Array(6).fill("")).slice(0, 6);
    arr[i] = digit;
    const next = arr.join("");
    onChange(next);
    if (digit && i < 5) {
      refs.current[i + 1]?.focus();
    }
  }

  function handlePaste(e: React.ClipboardEvent) {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    onChange(pasted.padEnd(6, "").slice(0, 6));
    refs.current[Math.min(pasted.length, 5)]?.focus();
  }

  return (
    <div className="flex gap-2.5" onPaste={handlePaste}>
      {Array.from({ length: 6 }).map((_, i) => (
        <input
          key={i}
          ref={(el) => { refs.current[i] = el; }}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={value[i] ?? ""}
          disabled={disabled}
          onChange={(e) => handleChange(i, e.target.value)}
          onKeyDown={(e) => handleKey(i, e)}
          className="h-12 w-10 rounded-lg border border-line bg-surface text-center text-[18px] font-mono font-semibold text-ink transition-colors focus:border-signal/60 focus:outline-none disabled:opacity-50 dark:border-line-dark dark:bg-surface-dark dark:text-ink-dark dark:focus:border-signal/40"
          aria-label={`Digit ${i + 1}`}
        />
      ))}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function RegisterPage() {
  const router = useRouter();
  const { startLoading } = useNavigationLoading();
  const { refreshUser, user } = useAuth();

  // Step: "email" | "otp"
  const [step, setStep] = useState<"email" | "otp">("email");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [otp, setOtp] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      startLoading();
      router.replace("/dashboard");
    }
  }, [user, router, startLoading]);

  // Countdown timer for resend cooldown
  useEffect(() => {
    if (cooldown <= 0) return;
    const id = setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(id);
  }, [cooldown]);

  // ── Step 1: Send OTP ──────────────────────────────────────────────────────
  async function handleSendOtp(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await authApi.sendOtp(email);
      setStep("otp");
      setCooldown(RESEND_COOLDOWN);
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.detail
          : "Failed to send verification code. Please try again.";
      setFormError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  // ── Resend OTP ────────────────────────────────────────────────────────────
  const handleResend = useCallback(async () => {
    if (cooldown > 0) return;
    setFormError(null);
    try {
      await authApi.resendOtp(email);
      setCooldown(RESEND_COOLDOWN);
      setOtp("");
    } catch (err) {
      setFormError(err instanceof ApiError ? err.detail : "Could not resend code.");
    }
  }, [cooldown, email]);

  // ── Step 2: Verify OTP + create account ───────────────────────────────────
  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (password.length < 8) {
      setFormError("Password must be at least 8 characters.");
      return;
    }
    if (otp.replace(/\D/g, "").length < 6) {
      setFormError("Please enter the 6-digit verification code.");
      return;
    }
    setSubmitting(true);
    try {
      const { access_token } = await authApi.verifyOtp(email, otp, password);
      setToken(access_token);
      await refreshUser();
      startLoading();
      router.replace("/dashboard/resume");
    } catch (err) {
      setFormError(
        err instanceof ApiError
          ? err.detail
          : "Verification failed. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  // ─── Left panel (shared) ─────────────────────────────────────────────────
  const LeftPanel = (
    <div className="relative hidden w-[52%] flex-col justify-between overflow-hidden bg-depth p-14 lg:flex">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage:
            "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />
      <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-signal/10 blur-[120px]" />
      <div className="pointer-events-none absolute -bottom-24 right-0 h-80 w-80 rounded-full bg-signal/8 blur-[100px]" />

      <div className="relative flex items-center gap-3">
        <LogoMark />
        <span className="font-display text-[16px] font-medium tracking-tight text-white/90">
          RoleRadar
        </span>
      </div>

      <div className="relative space-y-6">
        <div>
          <p className="font-mono text-[10.5px] uppercase tracking-[0.2em] text-signal">
            Get started in 60 seconds
          </p>
          <h1 className="mt-4 font-display text-[2.4rem] font-medium leading-[1.1] tracking-tight text-white">
            Your resume.
            <br />
            <span className="text-signal">Hundreds of matches.</span>
          </h1>
          <p className="mt-5 max-w-sm text-[15px] leading-relaxed text-white/55">
            Create an account, upload your PDF, and let RoleRadar&apos;s pipeline
            run automatically — surfacing your best matches every 4 hours.
          </p>
        </div>

        <div className="space-y-4">
          {[
            { n: "01", text: "Create your free account" },
            { n: "02", text: "Upload your resume (PDF)" },
            { n: "03", text: "Get matched jobs in your inbox" },
          ].map(({ n, text }) => (
            <div key={n} className="flex items-center gap-4">
              <span className="font-mono text-[11px] text-signal">{n}</span>
              <div className="h-px w-5 bg-white/15" />
              <span className="text-[13.5px] text-white/65">{text}</span>
            </div>
          ))}
        </div>
      </div>

      <p className="relative font-mono text-[11px] text-white/25">
        © {new Date().getFullYear()} RoleRadar
      </p>
    </div>
  );

  // ─── Step 1: Email entry ───────────────────────────────────────────────────
  if (step === "email") {
    return (
      <div className="flex min-h-screen bg-paper dark:bg-paper-dark">
        {LeftPanel}

        <div className="flex flex-1 items-center justify-center px-6 py-12">
          <div className="w-full max-w-[380px]">
            <div className="mb-8 flex items-center gap-2.5 lg:hidden">
              <LogoMark />
              <span className="font-display text-[15px] font-medium tracking-tight text-ink dark:text-ink-dark">
                RoleRadar
              </span>
            </div>

            <div className="mb-8">
              <h2 className="font-display text-[1.7rem] font-medium tracking-tight text-ink dark:text-ink-dark">
                Create account
              </h2>
              <p className="mt-1.5 text-[14px] text-muted dark:text-muted-dark">
                Already have one?{" "}
                <Link
                  href="/login"
                  className="text-ink underline-offset-2 hover:underline dark:text-ink-dark"
                >
                  Sign in
                </Link>
              </p>
            </div>

            <form onSubmit={handleSendOtp} className="space-y-4">
              <div>
                <label
                  htmlFor="reg-email"
                  className="mb-1.5 block text-[13px] font-medium text-ink dark:text-ink-dark"
                >
                  Email
                </label>
                <input
                  id="reg-email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full rounded-lg border border-line bg-surface px-3.5 py-2.5 text-[14px] text-ink placeholder:text-muted/60 transition-colors focus:border-signal/50 focus:outline-none dark:border-line-dark dark:bg-surface-dark dark:text-ink-dark dark:placeholder:text-muted-dark/60 dark:focus:border-signal/40"
                />
                {/* Communication notice */}
                <p className="mt-2 text-[11.5px] leading-relaxed text-muted dark:text-muted-dark">
                  Your email address will be used to communicate with you about RoleRadar,
                  including personalised job recommendations and important account-related
                  notifications. You can manage recommendation email notifications anytime
                  from Settings.
                </p>
              </div>

              {formError && (
                <div className="rounded-lg border border-danger/25 bg-danger/8 px-4 py-3 text-[13px] text-danger dark:bg-danger/10">
                  {formError}
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                id="send-otp-btn"
                className="group mt-1 flex w-full items-center justify-center gap-2 rounded-lg bg-ink py-2.5 text-[14px] font-medium text-paper transition-all hover:bg-ink/85 disabled:opacity-60 dark:bg-ink-dark dark:text-paper-dark dark:hover:bg-ink-dark/85"
              >
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    Send verification code
                    <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                  </>
                )}
              </button>

              <p className="text-center text-[11.5px] text-muted dark:text-muted-dark">
                By creating an account you agree to our{" "}
                <span className="cursor-pointer underline underline-offset-2 hover:text-ink dark:hover:text-ink-dark">
                  Terms of Service
                </span>
                .
              </p>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // ─── Step 2: OTP + Password entry ─────────────────────────────────────────
  return (
    <div className="flex min-h-screen bg-paper dark:bg-paper-dark">
      {LeftPanel}

      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-[400px]">
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <LogoMark />
            <span className="font-display text-[15px] font-medium tracking-tight text-ink dark:text-ink-dark">
              RoleRadar
            </span>
          </div>

          {/* Header */}
          <div className="mb-6">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-signal/30 bg-signal/10">
              <MailCheck className="h-5 w-5 text-signal" />
            </div>
            <h2 className="font-display text-[1.55rem] font-medium tracking-tight text-ink dark:text-ink-dark">
              Verify your email
            </h2>
            <p className="mt-1.5 text-[13.5px] text-muted dark:text-muted-dark">
              We sent a 6-digit code to{" "}
              <span className="font-medium text-ink dark:text-ink-dark">{email}</span>.
              Enter it below along with your new password.
            </p>
          </div>

          <form onSubmit={handleVerify} className="space-y-5">
            {/* OTP */}
            <div>
              <label className="mb-2.5 block text-[13px] font-medium text-ink dark:text-ink-dark">
                Verification code
              </label>
              <OtpInput value={otp} onChange={setOtp} disabled={submitting} />
              {/* Resend */}
              <div className="mt-3 flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={cooldown > 0 || submitting}
                  className="flex items-center gap-1.5 text-[12px] text-muted transition-colors hover:text-ink disabled:cursor-not-allowed disabled:opacity-40 dark:text-muted-dark dark:hover:text-ink-dark"
                >
                  <RefreshCw className="h-3 w-3" />
                  {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend code"}
                </button>
                <span className="text-[12px] text-muted/40 dark:text-muted-dark/40">·</span>
                <button
                  type="button"
                  onClick={() => { setStep("email"); setFormError(null); setOtp(""); }}
                  className="text-[12px] text-muted transition-colors hover:text-ink dark:text-muted-dark dark:hover:text-ink-dark"
                >
                  Change email
                </button>
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="reg-password"
                className="mb-1.5 block text-[13px] font-medium text-ink dark:text-ink-dark"
              >
                Create password
              </label>
              <div className="relative">
                <input
                  id="reg-password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min. 8 characters"
                  className="w-full rounded-lg border border-line bg-surface px-3.5 py-2.5 pr-10 text-[14px] text-ink placeholder:text-muted/60 transition-colors focus:border-signal/50 focus:outline-none dark:border-line-dark dark:bg-surface-dark dark:text-ink-dark dark:placeholder:text-muted-dark/60 dark:focus:border-signal/40"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted transition-colors hover:text-ink dark:text-muted-dark dark:hover:text-ink-dark"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <PasswordStrength password={password} />
            </div>

            {formError && (
              <div className="rounded-lg border border-danger/25 bg-danger/8 px-4 py-3 text-[13px] text-danger dark:bg-danger/10">
                {formError}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting || otp.replace(/\D/g, "").length < 6}
              id="verify-otp-btn"
              className="group mt-1 flex w-full items-center justify-center gap-2 rounded-lg bg-ink py-2.5 text-[14px] font-medium text-paper transition-all hover:bg-ink/85 disabled:opacity-60 dark:bg-ink-dark dark:text-paper-dark dark:hover:bg-ink-dark/85"
            >
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <ShieldCheck className="h-4 w-4" />
                  Create account
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
