import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-line dark:bg-line-dark",
        className
      )}
    />
  );
}

export function SkeletonStatCard() {
  return (
    <div className="rounded-xl border border-line bg-surface px-5 py-4 dark:border-line-dark dark:bg-surface-dark">
      <Skeleton className="h-3 w-20" />
      <Skeleton className="mt-3 h-8 w-16" />
    </div>
  );
}

export function SkeletonJobCard() {
  return (
    <div className="rounded-xl2 border border-line bg-surface p-5 dark:border-line-dark dark:bg-surface-dark">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
          <div className="flex gap-2 pt-1">
            <Skeleton className="h-5 w-16" />
            <Skeleton className="h-5 w-12" />
          </div>
        </div>
        <Skeleton className="h-14 w-14 rounded-full" />
      </div>
      <div className="mt-4 flex gap-1.5">
        <Skeleton className="h-5 w-16" />
        <Skeleton className="h-5 w-20" />
        <Skeleton className="h-5 w-14" />
      </div>
      <div className="mt-5 flex gap-2">
        <Skeleton className="h-8 flex-1" />
        <Skeleton className="h-8 w-16" />
      </div>
    </div>
  );
}

export function SkeletonTimeline() {
  return (
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex gap-3">
          <Skeleton className="mt-0.5 h-7 w-7 shrink-0 rounded-full" />
          <div className="flex-1 space-y-1.5 pt-1">
            <Skeleton className="h-3 w-2/3" />
            <Skeleton className="h-3 w-1/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function SkeletonDrawer() {
  return (
    <div className="flex gap-6 p-6">
      <div className="flex-1 space-y-4">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-4 w-1/3" />
      </div>
      <div className="w-72 space-y-3">
        <Skeleton className="h-5 w-28" />
        {[...Array(5)].map((_, i) => (
          <div key={i} className="space-y-1">
            <div className="flex justify-between">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-3 w-8" />
            </div>
            <Skeleton className="h-1.5 w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
