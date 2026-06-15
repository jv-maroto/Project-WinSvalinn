import { Lock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { hasFeature, type ProFeature } from "@/lib/edition";

export function ProBadge({ className }: { className?: string }) {
  return (
    <Badge
      className={cn(
        "gap-1 border font-semibold",
        "bg-[color-mix(in_oklch,var(--severity-info)_16%,transparent)]",
        "text-[var(--severity-info)]",
        "border-[color-mix(in_oklch,var(--severity-info)_35%,transparent)]",
        className,
      )}
    >
      <Lock className="size-3" /> PRO
    </Badge>
  );
}

/**
 * Gates a block behind a Pro feature. In Community it renders the block
 * dimmed and non-interactive with a PRO badge, so the value is visible
 * but locked (an upsell, not a hidden feature).
 */
export function ProGate({
  feature,
  children,
  className,
}: {
  feature: ProFeature;
  children: React.ReactNode;
  className?: string;
}) {
  if (hasFeature(feature)) return <>{children}</>;
  return (
    <div className={cn("relative", className)}>
      <div className="pointer-events-none select-none opacity-45">{children}</div>
      <div className="absolute right-2 top-2 z-10">
        <ProBadge />
      </div>
    </div>
  );
}
