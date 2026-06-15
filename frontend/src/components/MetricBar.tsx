import { SEV_COLOR, usageSev, type Sev } from "@/lib/severity";

/** Thin usage bar coloured by severity (higher pct = worse, unless `sev` given). */
export function MetricBar({ pct, sev }: { pct: number; sev?: Sev }) {
  const color = SEV_COLOR[sev ?? usageSev(pct)];
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${Math.min(100, Math.max(0, pct))}%`, background: color }}
      />
    </div>
  );
}
