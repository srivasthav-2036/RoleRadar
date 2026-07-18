"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { DashboardSidebar } from "@/components/dashboard-sidebar";
import { PageLoadingScreen } from "@/components/navigation-loading";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [user, isLoading, router]);

  // Premium loading screen (with rotating messages) while validating session
  if (isLoading) {
    return <PageLoadingScreen hint="Connecting to RoleRadar…" />;
  }

  // Not authenticated — redirect is already triggered above
  if (!user) return null;

  return (
    <div className="flex min-h-screen bg-paper dark:bg-paper-dark">
      <DashboardSidebar />
      <main className="flex-1 overflow-hidden">{children}</main>
    </div>
  );
}
