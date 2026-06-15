import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { type Sev, SEV_COLOR, SEV_LABEL } from "@/lib/severity";
import { useT } from "@/lib/i18n";

export function SeverityBadge({
  sev,
  label,
  className,
}: {
  sev: Sev;
  label?: string;
  className?: string;
}) {
  const t = useT();
  const c = SEV_COLOR[sev];
  return (
    <Badge
      variant="outline"
      className={cn("gap-1.5 font-semibold uppercase tracking-wide", className)}
      style={{
        color: c,
        borderColor: `color-mix(in oklch, ${c} 40%, transparent)`,
        background: `color-mix(in oklch, ${c} 12%, transparent)`,
      }}
    >
      <span className="size-1.5 rounded-full" style={{ background: c }} />
      {label ?? t(`sev.${sev}`, SEV_LABEL[sev])}
    </Badge>
  );
}
