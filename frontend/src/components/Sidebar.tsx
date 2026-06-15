import {
  Home, Shield, Zap, MemoryStick, Trash2, Activity,
  Network, Settings, Building2, Sparkles,
  Gamepad2, SlidersHorizontal, EyeOff,
  ShieldCheck, ScanSearch, Radar, Lock,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useEdition } from "@/lib/edition";
import { useT } from "@/lib/i18n";
import { Badge } from "@/components/ui/badge";
import type { Section } from "@/lib/nav";

export type { Section } from "@/lib/nav";

interface NavItem {
  key: Section;
  labelKey: string;
  icon: React.ComponentType<{ className?: string }>;
  enterprise?: boolean;
}

const GROUPS: { titleKey: string; items: NavItem[] }[] = [
  {
    titleKey: "group.audit",
    items: [
      { key: "dashboard", labelKey: "nav.dashboard", icon: Home },
      { key: "security", labelKey: "nav.security", icon: Shield, enterprise: true },
    ],
  },
  {
    titleKey: "group.system",
    items: [
      { key: "optimization", labelKey: "nav.optimization", icon: Zap },
      { key: "memory", labelKey: "nav.memory", icon: MemoryStick },
      { key: "cleanup", labelKey: "nav.cleanup", icon: Trash2 },
      { key: "processes", labelKey: "nav.processes", icon: Activity },
      { key: "network", labelKey: "nav.network", icon: Network },
    ],
  },
  {
    titleKey: "group.tuning",
    items: [
      { key: "gaming", labelKey: "nav.gaming", icon: Gamepad2 },
      { key: "tweaks", labelKey: "nav.tweaks", icon: SlidersHorizontal },
      { key: "privacy", labelKey: "nav.privacy", icon: EyeOff },
    ],
  },
  {
    titleKey: "group.enterprise",
    items: [
      { key: "hardening", labelKey: "nav.hardening", icon: ShieldCheck, enterprise: true },
      { key: "audit", labelKey: "nav.audit", icon: ScanSearch, enterprise: true },
      { key: "threat", labelKey: "nav.threat", icon: Radar, enterprise: true },
    ],
  },
  {
    titleKey: "group.general",
    items: [{ key: "settings", labelKey: "nav.settings", icon: Settings }],
  },
];

interface Props {
  active: Section;
  onChange: (s: Section) => void;
}

export function Sidebar({ active, onChange }: Props) {
  const { edition } = useEdition();
  const t = useT();
  const isEnterprise = edition === "empresarial";

  return (
    <aside className="glass m-2 mr-0 flex w-[212px] flex-col rounded-2xl py-3 text-sidebar-foreground">
      <nav className="flex-1 space-y-5 overflow-y-auto px-2">
        {GROUPS.map((group) => (
          <div key={group.titleKey}>
            <div className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
              {t(group.titleKey)}
            </div>
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = active === item.key;
              return (
                <button
                  key={item.key}
                  onClick={() => onChange(item.key)}
                  className={cn(
                    "relative flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-all",
                    isActive
                      ? "bg-white/8 text-foreground"
                      : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
                  )}
                >
                  {isActive && (
                    <span
                      className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-full bg-accent-gradient"
                      style={{ boxShadow: "0 0 10px var(--accent-from)" }}
                    />
                  )}
                  <Icon className={cn("size-4", isActive && "text-[var(--accent-from)]")} />
                  {t(item.labelKey)}
                  {item.enterprise && !isEnterprise && (
                    <Lock className="ml-auto size-3 text-muted-foreground/70" />
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="mx-2 mb-1 mt-2 rounded-xl border border-white/10 bg-white/5 p-3">
        <div className="flex items-center gap-1.5 text-xs font-semibold">
          {isEnterprise ? (
            <Building2 className="size-3.5 shrink-0 text-[var(--severity-ok)]" />
          ) : (
            <Sparkles className="size-3.5 shrink-0 text-[var(--accent-from)]" />
          )}
          WinSvalinn
          {isEnterprise ? (
            <Badge className="ml-auto gap-1 border-0 bg-accent-gradient font-semibold text-[#05080d]">
              Empresarial
            </Badge>
          ) : (
            <Badge variant="secondary" className="ml-auto font-semibold">Free</Badge>
          )}
        </div>
        <p className="mt-1.5 text-[11px] leading-snug text-muted-foreground">
          {isEnterprise
            ? t("sidebar.editionEnterprise", "Edición Empresarial activa: informes, auditoría CIS completa y análisis avanzados.")
            : t("sidebar.editionFree", "Edición Free. Empresarial añade informes, auditoría CIS completa, amenazas y análisis programados.")}
        </p>
      </div>

      <div className="px-3 text-center text-[10px] text-muted-foreground/60">v1.0.2</div>
    </aside>
  );
}
