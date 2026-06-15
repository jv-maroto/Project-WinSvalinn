import { motion } from "framer-motion";
import { useT } from "@/lib/i18n";

interface Props {
  value: number | null;
  label: string;
  size?: number;
}

function colorFor(v: number) {
  if (v >= 75) return "var(--color-success)";
  if (v >= 50) return "var(--color-warning)";
  return "var(--color-danger)";
}

/** Grade band → [i18n key, Spanish fallback]. */
function gradeFor(v: number): [string, string] {
  if (v >= 90) return ["grade.excellent", "EXCELENTE"];
  if (v >= 75) return ["grade.good", "BUENO"];
  if (v >= 55) return ["grade.fair", "REGULAR"];
  if (v >= 35) return ["grade.poor", "POBRE"];
  return ["grade.critical", "CRÍTICO"];
}

export function ScoreRing({ value, label, size = 140 }: Props) {
  const t = useT();
  const stroke = 12;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const v = value ?? 0;
  const offset = c - (v / 100) * c;
  const color = value === null
    ? "var(--color-text-dim)"
    : colorFor(value);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2} cy={size / 2} r={r}
            stroke="var(--color-bg-hover)"
            strokeWidth={stroke}
            fill="none"
          />
          <motion.circle
            cx={size / 2} cy={size / 2} r={r}
            stroke={color}
            strokeWidth={stroke}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={c}
            initial={{ strokeDashoffset: c }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold tabular-nums">
            {value === null ? "—" : value}
          </span>
          {value !== null && (
            <span
              className="text-[10px] font-bold tracking-wider mt-0.5"
              style={{ color }}
            >
              {t(...gradeFor(value))}
            </span>
          )}
        </div>
      </div>
      <span className="text-sm font-semibold">{label}</span>
    </div>
  );
}
