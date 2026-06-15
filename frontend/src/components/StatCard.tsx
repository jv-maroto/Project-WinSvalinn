import { motion } from "framer-motion";
import { type LucideIcon } from "lucide-react";

interface Props {
  label: string;
  value: string | number;
  icon: LucideIcon;
  color?: string;
}

export function StatCard({ label, value, icon: Icon, color }: Props) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="card flex items-center gap-4"
    >
      <div
        className="grid place-items-center rounded-xl p-2.5"
        style={{
          background: `color-mix(in oklch, ${color ?? "var(--color-accent)"} 15%, transparent)`,
          color: color ?? "var(--color-accent)",
        }}
      >
        <Icon size={24} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-xs text-[var(--color-text-dim)] truncate">{label}</div>
        <div className="text-2xl font-bold tabular-nums">{value}</div>
      </div>
    </motion.div>
  );
}
