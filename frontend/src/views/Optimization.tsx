import { useEffect, useState } from "react";
import {
  Zap, Cpu, MemoryStick, HardDrive,
  Play, Loader2, Bolt, Wand2, Network, Database, CheckCircle2, Settings2, RotateCcw, ChevronDown,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { MetricBar } from "@/components/MetricBar";
import { api } from "@/lib/api";
import { scoreSev, SEV_COLOR } from "@/lib/severity";
import { useT } from "../lib/i18n";

interface LogLine { ts: string; msg: string; level: "info" | "ok" | "warn" | "err"; }

interface GroupSpec { group: string; label: string; icon: LucideIcon; }

// Every optimization action is an expandable card with per-tweak checkboxes.
function useGroups(): GroupSpec[] {
  const t = useT();
  return [
    { group: "ui_tweaks", label: t("optimization.group_ui_tweaks", "Aplicar tweaks (interfaz)"), icon: Settings2 },
    { group: "visual",    label: t("optimization.group_visual", "Efectos visuales"),              icon: Wand2 },
    { group: "gpu",       label: t("optimization.group_gpu", "GPU por marca"),                    icon: Bolt },
    { group: "network",   label: t("optimization.group_network", "Red TCP/IP"),                   icon: Network },
    { group: "ssd",       label: t("optimization.group_ssd", "Optimización SSD"),                 icon: Database },
    { group: "perf",      label: t("optimization.group_perf", "Tweaks de rendimiento"),           icon: Zap },
    { group: "power",     label: t("optimization.group_power", "Plan de energía"),                icon: Cpu },
  ];
}

export function Optimization() {
  const t = useT();
  const GROUPS = useGroups();
  const [score, setScore] = useState<number | null>(null);
  const [applied, setApplied] = useState(0);
  const [total, setTotal] = useState(0);
  const [cpu, setCpu] = useState(0);
  const [ram, setRam] = useState(0);
  const [disk, setDisk] = useState(0);
  const [log, setLog] = useState<LogLine[]>([]);
  const [showLog, setShowLog] = useState(false);

  const append = (msg: string, level: LogLine["level"] = "info") =>
    setLog((p) => [{ ts: new Date().toLocaleTimeString(), msg, level }, ...p.slice(0, 200)]);

  useEffect(() => {
    api.config()
      .then((c) => setShowLog(c?.ui?.show_activity_log === true))
      .catch(() => { /* keep hidden by default */ });
  }, []);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const h = await api.systemHealth();
        const o = await api.optimizationScore();
        if (!cancelled) {
          setCpu(h.cpu); setRam(h.ram); setDisk(h.disk);
          setScore(o.score); setApplied(o.applied ?? 0); setTotal(o.total ?? 0);
        }
      } catch { /* sidecar offline */ }
    };
    tick();
    const id = setInterval(tick, 2000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const sev = scoreSev(score);

  return (
    <div className="h-full space-y-5 overflow-y-auto p-6">
      <header>
        <h1 className="font-heading text-2xl font-semibold">
          <span className="text-gradient">{t("optimization.heading", "Optimización")}</span>
        </h1>
        <p className="text-sm text-muted-foreground">
          {t("optimization.subheading", "Despliega cada bloque y elige con checkboxes qué aplicar. Reversible.")}
        </p>
      </header>

      <div className="glass glass-glow rounded-2xl p-6">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
          <div className="text-center">
            <div className="text-xs text-muted-foreground">{t("optimization.score_label", "Optimización")}</div>
            <div className="text-5xl font-bold tabular-nums" style={{ color: SEV_COLOR[sev] }}>
              {score ?? "—"}
            </div>
            {total > 0 && (
              <div className="mt-1 text-xs text-muted-foreground">{applied}/{total} tweaks</div>
            )}
          </div>
          <Separator orientation="vertical" className="hidden h-16 sm:block" />
          <div className="flex-1 space-y-3">
            <Metric label="CPU" icon={Cpu} value={cpu} />
            <Metric label="RAM" icon={MemoryStick} value={ram} />
            <Metric label={t("optimization.metric_disk", "Disco")} icon={HardDrive} value={disk} />
          </div>
        </div>
      </div>

      <section className="space-y-3">
        {GROUPS.map((g) => (
          <OptGroupCard key={g.group} spec={g} append={append} />
        ))}
      </section>

      {showLog && (
        <div className="glass rounded-2xl p-6">
          <div className="text-sm font-semibold">{t("optimization.activity_title", "Actividad")}</div>
          <div className="tabular mt-3 h-40 overflow-y-auto rounded-lg bg-background p-3 text-xs">
            {log.length === 0 && <div className="text-muted-foreground">{t("optimization.activity_empty", "Aplica algo para ver el registro.")}</div>}
            {log.map((l, i) => (
              <div key={i} className="py-0.5" style={{ color: logColor(l.level) }}>
                <span className="text-muted-foreground">[{l.ts}]</span> {l.msg}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface GroupPlan {
  title: string;
  subtitle?: string;
  restart?: boolean;
  tweaks: { id: string; label: string; applied?: boolean | null }[];
}

function OptGroupCard({
  spec,
  append,
}: {
  spec: GroupSpec;
  append: (msg: string, level?: LogLine["level"]) => void;
}) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [plan, setPlan] = useState<GroupPlan | null>(null);
  const [sel, setSel] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const p = await api.optGroupPlan(spec.group);
      setPlan(p);
      // Pre-select what's missing (applied !== true) so "Aplicar" fixes the gaps.
      setSel(new Set(p.tweaks.filter((tw) => tw.applied !== true).map((tw) => tw.id)));
    } catch (e: any) {
      append(`Error ${spec.label}: ${e.message}`, "err");
    } finally {
      setLoading(false);
    }
  };

  const toggleOpen = () => {
    const next = !open;
    setOpen(next);
    if (next) load(); // refetch on open to refresh applied-state
  };

  const toggle = (id: string) =>
    setSel((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  const apply = async () => {
    setRunning(true);
    append(`▶ ${plan?.title ?? spec.label}: ` + t("optimization.log_applying", "aplicando") + ` ${sel.size}`);
    try {
      const r: any = await api.optGroupApply(spec.group, [...sel], true);
      const n = r.applied ?? (r.actions?.length ?? 0);
      append(`✓ ${plan?.title ?? spec.label}: ${n} ` + t("optimization.log_applied_count", "aplicados"), "ok");
      await load();
    } catch (e: any) {
      append(`Error: ${e.message}`, "err");
    } finally {
      setRunning(false);
    }
  };

  const Icon = spec.icon;
  const doneCount = plan ? plan.tweaks.filter((tw) => tw.applied === true).length : 0;

  return (
    <div className="glass rounded-2xl p-4">
      <div className="flex items-center gap-4">
        <div className="grid size-10 place-items-center rounded-lg bg-primary/10 text-primary">
          <Icon className="size-5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold">{plan?.title ?? spec.label}</div>
          <div className="truncate text-xs text-muted-foreground">
            {plan?.subtitle
              ?? (plan ? `${doneCount}/${plan.tweaks.length} ` + t("optimization.tweaks_applied_suffix", "aplicados") : t("optimization.expand_hint", "Despliega para elegir qué aplicar"))}
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={toggleOpen}>
          {loading ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <ChevronDown className={"size-3.5 transition-transform " + (open ? "rotate-180" : "")} />
          )}
          {open ? t("optimization.btn_hide", "Ocultar") : t("optimization.btn_choose", "Elegir")}
        </Button>
      </div>

      {open && plan && (
        <div className="mt-3 border-t border-border pt-3">
          {plan.tweaks.length === 0 ? (
            <div className="text-xs text-muted-foreground">{t("optimization.no_options", "Sin opciones detectadas para este bloque.")}</div>
          ) : (
            <>
              <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
                {plan.tweaks.map((tw) => (
                  <label key={tw.id} className="flex cursor-pointer items-center gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={sel.has(tw.id)}
                      onChange={() => toggle(tw.id)}
                      className="size-3.5 shrink-0 accent-primary"
                    />
                    <span className={"flex-1 " + (sel.has(tw.id) ? "" : "text-muted-foreground")}>
                      {tw.label}
                    </span>
                    {tw.applied === true && (
                      <CheckCircle2 className="size-3 shrink-0" style={{ color: "var(--severity-ok)" }} />
                    )}
                  </label>
                ))}
              </div>
              {plan.restart && (
                <div className="mt-2 flex items-center gap-1.5 text-[11px] text-severity-med">
                  <RotateCcw className="size-3 shrink-0" /> {t("optimization.restart_warning", "Reinicia el Explorador de Windows al aplicar.")}
                </div>
              )}
              <div className="mt-3 flex justify-end">
                <Button variant="outline" size="sm" onClick={apply} disabled={running || sel.size === 0}>
                  {running ? <Loader2 className="size-3.5 animate-spin" /> : <Play className="size-3.5" />}
                  {t("optimization.btn_apply", "Aplicar")} {sel.size} {t("optimization.btn_apply_suffix", "seleccionados")}
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function Metric({ label, icon: Icon, value }: { label: string; icon: LucideIcon; value: number }) {
  return (
    <div className="flex items-center gap-3">
      <Icon className="size-3.5 text-muted-foreground" />
      <span className="w-10 text-xs text-muted-foreground">{label}</span>
      <div className="flex-1"><MetricBar pct={value} /></div>
      <span className="tabular w-12 text-right text-xs font-semibold">{value.toFixed(0)}%</span>
    </div>
  );
}

function logColor(level: LogLine["level"]): string {
  return level === "ok" ? "var(--severity-ok)"
    : level === "warn" ? "var(--severity-med)"
    : level === "err" ? "var(--severity-crit)"
    : "var(--muted-foreground)";
}
