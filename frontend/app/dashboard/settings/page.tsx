"use client";

import { useCallback, useState } from "react";
import { Settings, User, LogOut, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { PipelineStatusBanner } from "@/components/pipeline-status-banner";
import { useNavigationLoading } from "@/lib/navigation-context";

export default function SettingsPage() {
  const { startLoading } = useNavigationLoading();
  const { user, logout, refreshUser } = useAuth();
  const router = useRouter();
  const [loggingOut, setLoggingOut] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);

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

  return (
    <div className="h-screen overflow-y-auto px-6 py-8 md:px-10 md:py-10">
      <div className="mx-auto max-w-2xl">
        <PipelineStatusBanner />
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2.5">
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
                {refreshing ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : null}
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
