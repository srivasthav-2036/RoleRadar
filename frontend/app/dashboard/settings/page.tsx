"use client";

import { useCallback, useState } from "react";
import {
  Settings,
  User,
  LogOut,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Bell,
  BellOff,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { PipelineStatusBanner } from "@/components/pipeline-status-banner";
import { useNavigationLoading } from "@/lib/navigation-context";
import { authApi, ApiError } from "@/lib/api";

export default function SettingsPage() {
  const { startLoading } = useNavigationLoading();
  const { user, logout, refreshUser } = useAuth();
  const router = useRouter();
  const [loggingOut, setLoggingOut] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);

  // Email notification preference
  const [notifEnabled, setNotifEnabled] = useState<boolean>(
    user?.email_notifications ?? true
  );
  const [notifSaving, setNotifSaving] = useState(false);
  const [notifMsg, setNotifMsg] = useState<string | null>(null);
  const [notifError, setNotifError] = useState<string | null>(null);

  function handleLogout() {
    setLoggingOut(true);
    startLoading();
    logout();
    router.push("/login");
  }

  const handleRefreshProfile = useCallback(async () => {
    setRefreshing(true);
    setRefreshMsg(null);
    try {
      await refreshUser();
      setRefreshMsg("Profile refreshed successfully.");
    } catch {
      setRefreshMsg("Could not refresh profile.");
    } finally {
      setRefreshing(false);
      setTimeout(() => setRefreshMsg(null), 3000);
    }
  }, [refreshUser]);

  const handleToggleNotifications = useCallback(async () => {
    const newValue = !notifEnabled;
    setNotifSaving(true);
    setNotifMsg(null);
    setNotifError(null);
    try {
      await authApi.setNotifications(newValue);
      setNotifEnabled(newValue);
      // Sync user object so preference is reflected everywhere
      await refreshUser();
      setNotifMsg(
        newValue
          ? "Recommendation emails turned on."
          : "Recommendation emails turned off."
      );
      setTimeout(() => setNotifMsg(null), 3000);
    } catch (err) {
      setNotifError(
        err instanceof ApiError ? err.detail : "Could not save preference."
      );
    } finally {
      setNotifSaving(false);
    }
  }, [notifEnabled, refreshUser]);

  return (
    <div className="h-screen overflow-y-auto px-6 py-8 md:px-10 md:py-10">
      <div className="mx-auto max-w-2xl">
        <PipelineStatusBanner />
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2.5 pl-10 md:pl-0">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-line bg-surface dark:border-line-dark dark:bg-surface-dark">
              <Settings className="h-4 w-4 text-muted dark:text-muted-dark" />
            </div>
            <h1 className="font-display text-[1.4rem] font-medium tracking-tight text-ink dark:text-ink-dark">
              Settings
            </h1>
          </div>
          <p className="mt-2 text-[13.5px] text-muted dark:text-muted-dark">
            Account preferences and session management.
          </p>
        </div>

        <div className="space-y-4">
          {/* Profile */}
          <div className="rounded-xl border border-line bg-surface p-6 dark:border-line-dark dark:bg-surface-dark">
            <div className="mb-4 flex items-center gap-2">
              <User className="h-4 w-4 text-muted dark:text-muted-dark" />
              <p className="font-display text-[14px] font-medium text-ink dark:text-ink-dark">
                Profile
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between rounded-lg border border-line bg-paper px-4 py-3 dark:border-line-dark dark:bg-paper-dark">
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
                    Email
                  </p>
                  <p className="mt-0.5 text-[13.5px] text-ink dark:text-ink-dark">
                    {user?.email ?? "—"}
                  </p>
                </div>
              </div>

              {user?.name && (
                <div className="flex items-center justify-between rounded-lg border border-line bg-paper px-4 py-3 dark:border-line-dark dark:bg-paper-dark">
                  <div>
                    <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
                      Name
                    </p>
                    <p className="mt-0.5 text-[13.5px] text-ink dark:text-ink-dark">
                      {user.name}
                    </p>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-between rounded-lg border border-line bg-paper px-4 py-3 dark:border-line-dark dark:bg-paper-dark">
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
                    User ID
                  </p>
                  <p className="mt-0.5 font-mono text-[12px] text-muted dark:text-muted-dark">
                    {user?.user_id ?? "—"}
                  </p>
                </div>
              </div>
            </div>

            {/* Refresh */}
            <div className="mt-4 flex items-center gap-3">
              <button
                onClick={handleRefreshProfile}
                disabled={refreshing}
                className="flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-[12.5px] text-muted transition-colors hover:border-ink/30 hover:text-ink disabled:opacity-50 dark:border-line-dark dark:text-muted-dark"
              >
                {refreshing ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
                Refresh profile
              </button>
              {refreshMsg && (
                <span className="flex items-center gap-1 text-[12.5px] text-signal">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  {refreshMsg}
                </span>
              )}
            </div>
          </div>

          {/* Notifications */}
          <div className="rounded-xl border border-line bg-surface p-6 dark:border-line-dark dark:bg-surface-dark">
            <div className="mb-4 flex items-center gap-2">
              <Bell className="h-4 w-4 text-muted dark:text-muted-dark" />
              <p className="font-display text-[14px] font-medium text-ink dark:text-ink-dark">
                Notifications
              </p>
            </div>

            <div className="rounded-lg border border-line bg-paper px-4 py-4 dark:border-line-dark dark:bg-paper-dark">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    {notifEnabled ? (
                      <Bell className="h-3.5 w-3.5 text-signal" />
                    ) : (
                      <BellOff className="h-3.5 w-3.5 text-muted dark:text-muted-dark" />
                    )}
                    <p className="text-[13.5px] font-medium text-ink dark:text-ink-dark">
                      Recommendation emails
                    </p>
                  </div>
                  <p className="mt-1 text-[12.5px] leading-relaxed text-muted dark:text-muted-dark">
                    {notifEnabled
                      ? "You will receive an email when new job matches are found."
                      : "You will not receive recommendation emails. Jobs are still matched and stored for you."}
                  </p>
                </div>

                {/* Toggle switch */}
                <button
                  type="button"
                  role="switch"
                  aria-checked={notifEnabled}
                  id="notifications-toggle"
                  disabled={notifSaving}
                  onClick={handleToggleNotifications}
                  className={`relative mt-0.5 h-6 w-11 shrink-0 rounded-full transition-colors focus:outline-none disabled:opacity-50 ${
                    notifEnabled
                      ? "bg-signal"
                      : "bg-line dark:bg-line-dark"
                  }`}
                >
                  <span
                    className={`block h-5 w-5 rounded-full bg-white shadow-sm transition-transform ${
                      notifEnabled ? "translate-x-[22px]" : "translate-x-[2px]"
                    }`}
                  />
                  {notifSaving && (
                    <span className="absolute inset-0 flex items-center justify-center">
                      <Loader2 className="h-3 w-3 animate-spin text-white/70" />
                    </span>
                  )}
                </button>
              </div>
            </div>

            {notifMsg && (
              <p className="mt-3 flex items-center gap-1.5 text-[12.5px] text-signal">
                <CheckCircle2 className="h-3.5 w-3.5" />
                {notifMsg}
              </p>
            )}
            {notifError && (
              <p className="mt-3 flex items-center gap-1.5 text-[12.5px] text-danger">
                <AlertCircle className="h-3.5 w-3.5" />
                {notifError}
              </p>
            )}
          </div>

          {/* Danger zone */}
          <div className="rounded-xl border border-danger/15 bg-danger/3 p-6 dark:bg-danger/5">
            <div className="mb-4 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-danger/60" />
              <p className="font-display text-[14px] font-medium text-ink dark:text-ink-dark">
                Session
              </p>
            </div>
            <p className="mb-4 text-[13px] text-muted dark:text-muted-dark">
              Signing out will clear your local session. Your data remains on the server.
            </p>
            <button
              onClick={handleLogout}
              disabled={loggingOut}
              className="flex items-center gap-1.5 rounded-lg border border-danger/20 bg-danger/5 px-4 py-2 text-[13px] font-medium text-danger transition-colors hover:bg-danger/10 disabled:opacity-50"
            >
              {loggingOut ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <LogOut className="h-3.5 w-3.5" />
              )}
              Sign out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
