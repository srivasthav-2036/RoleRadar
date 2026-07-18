"use client";

import { cn } from "@/lib/utils";

interface MatchDialProps {
  score: number; // 0–100
  size?: "sm" | "md" | "lg";
  className?: string;
}

// Each size configuration is carefully proportioned so the score number
// and "MATCH" label never collide, even at 3-digit-like values (e.g. 100).
const SIZES = {
  sm: {
    box: 60,
    stroke: 3.5,
    // Score sits in upper-centre; MATCH sits below it with a fixed gap
    scoreFontSize: 11,
    labelFontSize: 7,
    gap: 2,          // px between bottom of score text and top of label
    scoreOffsetY: -4, // shift score up from absolute centre
  },
  md: {
    box: 88,
    stroke: 4,
    scoreFontSize: 18,
    labelFontSize: 8,
    gap: 3,
    scoreOffsetY: -5,
  },
  lg: {
    box: 128,
    stroke: 5,
    scoreFontSize: 26,
    labelFontSize: 10,
    gap: 4,
    scoreOffsetY: -7,
  },
};

function dialColor(score: number): string {
  if (score >= 85) return "#B8862E";   // signal gold (Excellent)
  if (score >= 65) return "#52525b";   // ink/zinc-600 (Good)
  return "#a1a1aa";                    // muted/zinc-400 (Average/Weak)
}

export function MatchDial({ score, size = "md", className }: MatchDialProps) {
  const cfg = SIZES[size];
  const cx = cfg.box / 2;
  const cy = cfg.box / 2;
  const radius = cfg.box / 2 - cfg.stroke * 2.2;
  const circumference = 2 * Math.PI * radius;
  const arcFraction = 0.75; // 270-degree sweep
  const arcLength = circumference * arcFraction;
  const offset = arcLength - (Math.min(Math.max(score, 0), 100) / 100) * arcLength;
  const color = dialColor(score);

  // Display value — round to 1 decimal only if not an integer
  const displayScore =
    Number.isInteger(score) ? String(score) : score.toFixed(1);

  // Vertical centres: score text sits at (cy + scoreOffsetY), label sits below
  const scoreY = cy + cfg.scoreOffsetY;
  const labelY = scoreY + cfg.scoreFontSize * 0.85 + cfg.gap + cfg.labelFontSize;

  return (
    <div
      className={cn("relative shrink-0", className)}
      style={{ width: cfg.box, height: cfg.box }}
      role="img"
      aria-label={`Match score ${displayScore} percent`}
    >
      <svg
        width={cfg.box}
        height={cfg.box}
        viewBox={`0 0 ${cfg.box} ${cfg.box}`}
        aria-hidden="true"
      >
        {/* ── Track (full arc, dim) ── */}
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          strokeWidth={cfg.stroke}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeLinecap="round"
          stroke="currentColor"
          strokeOpacity="0.12"
          className="text-ink dark:text-ink-dark"
          transform={`rotate(135 ${cx} ${cy})`}
        />

        {/* ── Filled arc (score progress) ── */}
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          strokeWidth={cfg.stroke}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          stroke={color}
          transform={`rotate(135 ${cx} ${cy})`}
          style={{ transition: "stroke-dashoffset 1s ease-out" }}
        />

        {/* ── Score number (centred vertically above label) ── */}
        <text
          x={cx}
          y={scoreY}
          textAnchor="middle"
          dominantBaseline="middle"
          fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
          fontSize={cfg.scoreFontSize}
          fontWeight="600"
          fill={color}
        >
          {displayScore}
        </text>

        {/* ── MATCH label (below score, never overlapping) ── */}
        <text
          x={cx}
          y={labelY}
          textAnchor="middle"
          dominantBaseline="middle"
          fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
          fontSize={cfg.labelFontSize}
          fontWeight="500"
          letterSpacing="0.15em"
          fill="currentColor"
          fillOpacity="0.4"
          className="text-ink dark:text-ink-dark"
        >
          MATCH
        </text>
      </svg>
    </div>
  );
}
