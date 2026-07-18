"use client";

import { useState, useMemo, useEffect } from "react";
import { cn } from "@/lib/utils";
import type { SkillFrequency } from "@/lib/types";

interface SkillGalaxyProps {
  skills: SkillFrequency[];
  loading?: boolean;
}

function hashHue(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash) % 360;
}

export function SkillGalaxy({ skills, loading }: SkillGalaxyProps) {
  const [hoveredSkill, setHoveredSkill] = useState<string | null>(null);
  const [isDark, setIsDark] = useState(false);

  // Detect dark mode by watching the <html> class
  useEffect(() => {
    const check = () =>
      setIsDark(document.documentElement.classList.contains("dark"));
    check();
    const observer = new MutationObserver(check);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
    return () => observer.disconnect();
  }, []);

  const processed = useMemo(() => {
    if (!skills || skills.length === 0) return [];
    const maxCount = Math.max(...skills.map((s) => s.count), 1);
    return skills.slice(0, 28).map((s) => {
      const hue = hashHue(s.skill);
      return {
        ...s,
        size: 28 + (s.count / maxCount) * 52, // 28px to 80px
        hue,
      };
    });
  }, [skills]);

  if (loading) {
    return (
      <div className="flex flex-wrap gap-2">
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="animate-pulse rounded-full bg-line dark:bg-line-dark"
            style={{
              width: 40 + (i % 4) * 16,
              height: 40 + (i % 4) * 16,
            }}
          />
        ))}
      </div>
    );
  }

  if (processed.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-line bg-paper py-10 text-center dark:border-line-dark dark:bg-paper-dark">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-line bg-surface dark:border-line-dark dark:bg-surface-dark">
          <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.2" opacity="0.4" />
            <circle cx="10" cy="10" r="5.5" stroke="currentColor" strokeWidth="1.2" opacity="0.65" />
            <circle cx="10" cy="10" r="2" fill="#B8862E" />
          </svg>
        </div>
        <p className="font-mono text-[10.5px] uppercase tracking-[0.15em] text-muted dark:text-muted-dark">
          No skill data yet
        </p>
        <p className="mt-1 text-[12.5px] text-muted dark:text-muted-dark">
          Skills will appear after you receive recommendations.
        </p>
      </div>
    );
  }

  return (
    <div
      className="relative flex flex-wrap items-center gap-2.5 rounded-xl border border-line bg-paper p-4 dark:border-line-dark dark:bg-paper-dark"
      role="list"
      aria-label="Skill frequency galaxy"
    >
      {processed.map(({ skill, count, size, hue }) => {
        const isHovered = hoveredSkill === skill;
        const opacity = hoveredSkill ? (isHovered ? 1 : 0.35) : 0.85;

        // Theme-aware: darker in light mode, lighter in dark mode
        const lightness = isDark ? 68 : 38;
        const saturation = isDark ? 65 : 60;
        const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
        const bgColor = `hsl(${hue}, ${saturation}%, ${lightness}%, 0.12)`;
        const borderColor = `hsl(${hue}, ${saturation}%, ${lightness}%, 0.35)`;

        return (
          <div
            key={skill}
            role="listitem"
            style={{ width: size, height: size }}
            className="relative flex-shrink-0 cursor-default"
            onMouseEnter={() => setHoveredSkill(skill)}
            onMouseLeave={() => setHoveredSkill(null)}
          >
            <div
              className={cn(
                "flex h-full w-full items-center justify-center rounded-full border transition-all duration-200",
                isHovered && "shadow-card-hover"
              )}
              style={{
                backgroundColor: bgColor,
                borderColor: borderColor,
                color,
                opacity,
                transform: isHovered ? "scale(1.1)" : "scale(1)",
              }}
              title={`${skill}: ${count} match${count !== 1 ? "es" : ""}`}
            >
              <span
                className="select-none overflow-hidden text-center font-medium leading-tight"
                style={{ fontSize: Math.max(9, size / 5.5) }}
              >
                {skill}
              </span>
            </div>

            {/* Hover tooltip */}
            {isHovered && (
              <div className="pointer-events-none absolute -top-8 left-1/2 z-10 -translate-x-1/2 whitespace-nowrap rounded border border-line bg-surface px-2 py-1 font-mono text-[10.5px] text-ink shadow-card dark:border-line-dark dark:bg-surface-dark dark:text-ink-dark">
                {count} match{count !== 1 ? "es" : ""}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
