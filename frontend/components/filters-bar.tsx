"use client";

import { Search, SlidersHorizontal } from "lucide-react";

export function FiltersBar() {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="relative w-full max-w-sm">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-[15px] w-[15px] -translate-y-1/2 text-muted dark:text-muted-dark" />
        <input
          type="text"
          placeholder="Search matches by title or company"
          className="w-full rounded-lg border border-line bg-surface py-2 pl-9 pr-3 text-[13.5px] text-ink placeholder:text-muted focus:border-ink/30 dark:border-line-dark dark:bg-surface-dark dark:text-ink-dark dark:placeholder:text-muted-dark dark:focus:border-ink-dark/30"
        />
      </div>

      <div className="flex items-center gap-2">
        {["All", "85+", "70+", "Internship"].map((filter, i) => (
          <button
            key={filter}
            className={`rounded-full border px-3 py-1.5 text-[12.5px] transition-colors ${
              i === 0
                ? "border-ink bg-ink text-paper dark:border-ink-dark dark:bg-ink-dark dark:text-paper-dark"
                : "border-line text-muted hover:border-ink/30 hover:text-ink dark:border-line-dark dark:text-muted-dark dark:hover:border-ink-dark/30 dark:hover:text-ink-dark"
            }`}
          >
            {filter}
          </button>
        ))}
        <button className="flex items-center gap-1.5 rounded-full border border-line px-3 py-1.5 text-[12.5px] text-muted transition-colors hover:border-ink/30 hover:text-ink dark:border-line-dark dark:text-muted-dark dark:hover:border-ink-dark/30 dark:hover:text-ink-dark">
          <SlidersHorizontal className="h-3 w-3" strokeWidth={2} />
          More
        </button>
      </div>
    </div>
  );
}
