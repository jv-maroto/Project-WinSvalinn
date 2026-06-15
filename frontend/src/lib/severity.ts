/** Functional severity scale (Nord Aurora). Drives badges and bars. */

export type Sev = "crit" | "high" | "med" | "ok" | "info";

export const SEV_COLOR: Record<Sev, string> = {
  crit: "var(--severity-crit)",
  high: "var(--severity-high)",
  med: "var(--severity-med)",
  ok: "var(--severity-ok)",
  info: "var(--severity-info)",
};

export const SEV_LABEL: Record<Sev, string> = {
  crit: "Crítico",
  high: "Alto",
  med: "Medio",
  ok: "Correcto",
  info: "Info",
};

/** Score 0-100: higher is better. */
export function scoreSev(v: number | null): Sev {
  if (v == null) return "info";
  if (v >= 75) return "ok";
  if (v >= 50) return "med";
  return "crit";
}

/** Resource usage percent: higher is worse. */
export function usageSev(pct: number): Sev {
  if (pct >= 85) return "crit";
  if (pct >= 60) return "med";
  return "ok";
}

/** Normalise the backend's free-form severity strings. */
export function normSev(raw: unknown): Sev {
  const s = String(raw ?? "").toLowerCase();
  if (s.includes("crit")) return "crit";
  if (s.includes("high") || s.includes("alto")) return "high";
  if (s.includes("med") || s.includes("warn")) return "med";
  if (s.includes("ok") || s.includes("pass") || s.includes("low")) return "ok";
  return "info";
}
