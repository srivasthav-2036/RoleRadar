import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number | null | undefined;
  suffix?: string;
  icon?: LucideIcon;
  iconColor?: string;
  description?: string;
  loading?: boolean;
}

export function StatCard({
  label,
  value,
  suffix,
  icon: Icon,
  iconColor,
  description,
  loading = false,
}: StatCardProps) {
  const displayValue = value === null || value === undefined ? "—" : value;

  if (loading) {
    return (
      <div className="rounded-xl border border-line bg-surface px-5 py-4 dark:border-line-dark dark:bg-surface-dark">
        <div className="h-2.5 w-20 animate-pulse rounded bg-line dark:bg-line-dark" />
        <div className="mt-3 h-8 w-14 animate-pulse rounded bg-line dark:bg-line-dark" />
      </div>
    );
  }

  return (
    <div className="group rounded-xl border border-line bg-surface px-5 py-4 transition-shadow hover:shadow-card dark:border-line-dark dark:bg-surface-dark">
      <div className="flex items-center justify-between">
        <p className="font-mono text-[10.5px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
          {label}
        </p>
        {Icon && (
          <Icon
            className={cn("h-3.5 w-3.5 opacity-50", iconColor ?? "text-muted dark:text-muted-dark")}
            strokeWidth={1.75}
          />
        )}
      </div>
      <p className="mt-1.5 font-mono text-[26px] font-medium tabular-nums text-ink dark:text-ink-dark">
        {displayValue}
        {suffix && displayValue !== "—" && (
          <span className="ml-0.5 text-[15px] text-muted dark:text-muted-dark">{suffix}</span>
        )}
      </p>
      {description && (
        <p className="mt-1 text-[11.5px] text-muted dark:text-muted-dark">{description}</p>
      )}
    </div>
  );
}
