"use client";

import { usePathname, useRouter } from "next/navigation";
import {
  LayoutGrid,
  FileText,
  Sparkles,
  Settings,
  LogOut,
  Clock,
  X,
} from "lucide-react";
import { ThemeToggle } from "./theme-toggle";
import { useAuth } from "@/lib/auth-context";
import { useNavigationLoading } from "@/lib/navigation-context";

const navItems = [
  { label: "Dashboard", icon: LayoutGrid, href: "/dashboard" },
  { label: "Resume", icon: FileText, href: "/dashboard/resume" },
  { label: "Your Matches", icon: Sparkles, href: "/dashboard/tailored" },
  { label: "Activity", icon: Clock, href: "/dashboard/activity" },
  { label: "Settings", icon: Settings, href: "/dashboard/settings" },
];

function UserInitials({ name, email }: { name: string | null; email: string }) {
  const initials = name
    ? name
        .split(" ")
        .slice(0, 2)
        .map((n) => n[0])
        .join("")
        .toUpperCase()
    : email[0].toUpperCase();
  return <>{initials}</>;
}

interface DashboardSidebarProps {
  /** Mobile only: whether the sidebar overlay is open */
  isOpen?: boolean;
  /** Mobile only: called when the user closes the sidebar */
  onClose?: () => void;
}

export function DashboardSidebar({ isOpen = false, onClose }: DashboardSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { startLoading } = useNavigationLoading();

  function navigate(href: string) {
    if (pathname === href) {
      onClose?.();
      return;
    }
    startLoading();
    onClose?.();
    router.push(href);
  }

  function handleLogout() {
    startLoading();
    onClose?.();
    logout();
    router.push("/login");
  }

  const displayName = user?.name ?? user?.email?.split("@")[0] ?? "";

  // ─── Sidebar content (shared between mobile overlay and desktop) ──────────
  const SidebarContent = (
    <>
      {/* Logo + Mobile close button row */}
      <div className="mb-10 flex items-center justify-between px-1.5">
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2.5"
        >
          <svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.2" opacity="0.35" />
            <circle cx="10" cy="10" r="5.5" stroke="currentColor" strokeWidth="1.2" opacity="0.6" />
            <circle cx="10" cy="10" r="2" fill="#B8862E" />
          </svg>
          <span className="font-display text-[14.5px] font-medium tracking-tight text-ink dark:text-ink-dark">
            RoleRadar
          </span>
        </button>

        {/* Close button — only shown on mobile overlay */}
        <button
          onClick={onClose}
          aria-label="Close menu"
          className="flex h-7 w-7 items-center justify-center rounded-lg text-muted transition-colors hover:bg-line/50 hover:text-ink dark:text-muted-dark dark:hover:bg-line-dark/50 dark:hover:text-ink-dark md:hidden"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex flex-1 flex-col gap-0.5">
        {navItems.map(({ label, icon: Icon, href }) => {
          const isActive =
            href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(href);
          return (
            <button
              key={label}
              onClick={() => navigate(href)}
              className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13.5px] transition-colors text-left w-full ${
                isActive
                  ? "bg-ink text-paper dark:bg-ink-dark dark:text-paper-dark"
                  : "text-muted hover:bg-line/50 hover:text-ink dark:text-muted-dark dark:hover:bg-line-dark/50 dark:hover:text-ink-dark"
              }`}
            >
              <Icon className="h-[15px] w-[15px]" strokeWidth={1.75} />
              {label}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-line pt-4 dark:border-line-dark">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-depth font-mono text-[11px] text-paper dark:bg-depth-dark">
              {user ? (
                <UserInitials name={user.name} email={user.email} />
              ) : (
                "?"
              )}
            </div>
            <span className="truncate text-[12.5px] text-muted dark:text-muted-dark">
              {displayName}
            </span>
          </div>
          <ThemeToggle />
        </div>

        <button
          onClick={handleLogout}
          className="mt-2 flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] text-muted transition-colors hover:bg-danger/8 hover:text-danger dark:text-muted-dark dark:hover:bg-danger/10 dark:hover:text-danger"
        >
          <LogOut className="h-[14px] w-[14px]" strokeWidth={1.75} />
          Sign out
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* ── Desktop sidebar (always visible on md+) ─────────────────────── */}
      <aside className="hidden w-60 shrink-0 border-r border-line px-4 py-6 dark:border-line-dark md:flex md:flex-col">
        {SidebarContent}
      </aside>

      {/* ── Mobile overlay backdrop ──────────────────────────────────────── */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* ── Mobile slide-in sidebar ──────────────────────────────────────── */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-line bg-paper px-4 py-6 shadow-xl transition-transform duration-300 dark:border-line-dark dark:bg-paper-dark md:hidden ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        aria-label="Navigation menu"
      >
        {SidebarContent}
      </aside>
    </>
  );
}
