import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F8F8F6",
        "paper-dark": "#0E1116",
        surface: "#FFFFFF",
        "surface-dark": "#151920",
        ink: "#14171F",
        "ink-dark": "#EDEEF0",
        muted: "#5B6270",
        "muted-dark": "#9096A3",
        line: "#E4E4E0",
        "line-dark": "#242832",
        signal: "#B8862E",
        "signal-soft": "#F4E9D8",
        "signal-soft-dark": "#2A2313",
        "signal-dark": "#D9A54B",
        depth: "#1B2438",
        "depth-dark": "#2A3550",
        danger: "#B3492F",
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        body: ["var(--font-body)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(20,23,31,0.04), 0 1px 1px rgba(20,23,31,0.03)",
        "card-hover": "0 12px 28px rgba(20,23,31,0.09), 0 2px 6px rgba(20,23,31,0.04)",
        "card-dark": "0 1px 2px rgba(0,0,0,0.3)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        sweep: {
          "0%": { transform: "scaleX(0)" },
          "100%": { transform: "scaleX(1)" },
        },
        "dial-in": {
          "0%": { strokeDashoffset: "var(--dial-full)" },
          "100%": { strokeDashoffset: "var(--dial-offset)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.7s cubic-bezier(0.16,1,0.3,1) both",
        sweep: "sweep 1.2s cubic-bezier(0.16,1,0.3,1) both",
        "dial-in": "dial-in 1.1s cubic-bezier(0.16,1,0.3,1) both",
      },
    },
  },
  plugins: [],
};

export default config;
