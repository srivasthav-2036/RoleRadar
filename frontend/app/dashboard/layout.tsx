"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { DashboardSidebar } from "@/components/dashboard-sidebar";
import { PageLoadingScreen } from "@/components/navigation-loading";
import { Menu } from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [user, isLoading, router]);

  // Close sidebar on route change (navigation completed)
  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  // Premium loading screen (with rotating messages) while validating session
  if (isLoading) {
    return <PageLoadingScreen hint="Connecting to RoleRadar…" />;
  }

  // Not authenticated — redirect is already triggered above
  if (!user) return null;

  return (
    <div className="flex min-h-screen bg-paper dark:bg-paper-dark">
      {/* Mobile hamburger button — fixed top-left, hidden on md+ */}
      <button
        id="mobile-menu-btn"
        aria-label="Open navigation menu"
        aria-expanded={sidebarOpen}
        onClick={() => setSidebarOpen(true)}
        className="fixed left-4 top-4 z-30 flex h-9 w-9 items-center justify-center rounded-lg border border-line bg-surface shadow-sm transition-colors hover:border-ink/20 hover:bg-paper active:scale-95 dark:border-line-dark dark:bg-surface-dark md:hidden"
      >
        <Menu className="h-4.5 w-4.5 text-ink dark:text-ink-dark" />
      </button>

      <DashboardSidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex-1 overflow-hidden">{children}</main>
    </div>
  );
}
