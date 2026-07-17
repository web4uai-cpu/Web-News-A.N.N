"use client";

import { useUIStore } from "./ui-store";

/**
 * Theme-aware colors for Recharts (SVG attributes can't resolve CSS variables,
 * so charts read resolved values per theme from here).
 *
 * The categorical tier palette was validated with the dataviz six-checks
 * validator against both surfaces (#05050a dark, #f5f6fa light): lightness band,
 * chroma floor, CVD separation, normal-vision floor, contrast. The light-mode
 * amber contrast WARN is relieved by visible text labels beside every swatch.
 */
export const TIER_COLORS: Record<string, string> = {
  free: "#d97706",
  starter: "#0891b2",
  standard: "#0891b2",
  pro: "#8b5cf6",
  enterprise: "#059669",
};

const themes = {
  dark: {
    tick: "#64748b",
    grid: "rgba(255,255,255,0.06)",
    series: "#3b82f6",
    seriesFillFrom: 0.3,
    tooltip: {
      background: "#0f0f1e",
      border: "1px solid rgba(255,255,255,0.1)",
      borderRadius: 8,
      fontSize: 11,
      color: "#f8fafc",
    },
    tooltipLabel: { color: "#94a3b8" },
  },
  light: {
    tick: "#475569",
    grid: "rgba(15,23,42,0.08)",
    series: "#2563eb",
    seriesFillFrom: 0.2,
    tooltip: {
      background: "#ffffff",
      border: "1px solid rgba(15,23,42,0.12)",
      borderRadius: 8,
      fontSize: 11,
      color: "#0f172a",
    },
    tooltipLabel: { color: "#475569" },
  },
} as const;

export type ChartTheme = (typeof themes)["dark"] | (typeof themes)["light"];

export function useChartTheme(): ChartTheme {
  const theme = useUIStore((s) => s.theme);
  return themes[theme];
}
