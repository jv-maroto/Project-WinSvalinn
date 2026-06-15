import { useEffect, useState } from "react";
import { MemoryStick, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { api, type MemoryStats } from "@/lib/api";
import { SEV_COLOR } from "@/lib/severity";
import { useT } from "../lib/i18n";

function memColor(mb: number): string {
  if (mb >= 500) return SEV_COLOR.crit;
  if (mb >= 200) return SEV_COLOR.med;
  if (mb >= 50) return SEV_COLOR.info;
  return "var(--foreground)";
}

export function Memory() {
  const t = useT();
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [freeing, setFreeing] = useState(false);
  const [delta, setDelta] = useState<{ before: number; after: number } | null>(null);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const s = await api.memoryStats();
        if (!cancelled) setStats(s);
      } catch { /* */ }
    };
    tick();
    const id = setInterval(tick, 1500);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const onFree = async () => {
    setFreeing(true);
    try {
      const r: any = await api.memoryFree();
      setDelta({ before: r.before_percent, after: r.after_percent });
    } catch { /* */ } finally {
      setFreeing(false);
    }
  };

  return (
    <div className="h-full space-y-5 overflow-y-auto p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-heading text-2xl font-semibold">
            {t("memory.titlePrefix", "Gestor de")} <span className="text-gradient">{t("memory.titleHighlight", "memoria")}</span>
          </h1>
          <p className="text-sm text-muted-foreground">{t("memory.subtitle", "RAM en vivo + top procesos.")}</p>
        </div>
        <Button onClick={onFree} disabled={freeing} className="bg-accent-gradient ring-glow">
          {freeing ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
          {freeing ? t("memory.buttonFreeing", "Liberando…") : t("memory.buttonFree", "Liberar RAM")}
        </Button>
      </header>

      {delta && (
        <Alert>
          <MemoryStick className="size-4" style={{ color: SEV_COLOR.ok }} />
          <AlertTitle>{t("memory.alertTitle", "RAM liberada")}</AlertTitle>
          <AlertDescription>
            {delta.before}% → {delta.after}% (Δ {(delta.before - delta.after).toFixed(1)}%)
          </AlertDescription>
        </Alert>
      )}

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label={t("memory.statTotal", "Total")} value={stats ? `${stats.total_gb} GB` : "—"} />
        <Stat label={t("memory.statUsed", "Usada")} value={stats ? `${stats.used_gb} GB` : "—"} color={SEV_COLOR.med} />
        <Stat label={t("memory.statAvailable", "Disponible")} value={stats ? `${stats.available_gb} GB` : "—"} color={SEV_COLOR.ok} />
        <Stat label={t("memory.statPercent", "% Uso")} value={stats ? `${stats.percent}%` : "—"} color="var(--primary)" />
      </section>

      <div className="glass overflow-hidden rounded-2xl">
        <h2 className="font-heading p-6 pb-3 text-base font-semibold">{t("memory.tableTitle", "Top procesos por memoria")}</h2>
          <div className="max-h-[420px] overflow-y-auto">
            <Table>
              <TableHeader className="sticky top-0 bg-card">
                <TableRow>
                  <TableHead className="w-28">{t("memory.colRam", "RAM")}</TableHead>
                  <TableHead>{t("memory.colProcess", "Proceso")}</TableHead>
                  <TableHead className="text-right">{t("memory.colPid", "PID")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats?.top_processes.slice(0, 25).map((p) => (
                  <TableRow key={p.pid}>
                    <TableCell className="tabular font-semibold" style={{ color: memColor(p.memory_mb) }}>
                      {p.memory_mb.toFixed(0)} MB
                    </TableCell>
                    <TableCell className="truncate">{p.name}</TableCell>
                    <TableCell className="tabular text-right text-muted-foreground">{p.pid}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
      </div>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="glass space-y-1 rounded-2xl p-4">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <MemoryStick className="size-3.5" /> {label}
      </div>
      <div className="text-2xl font-bold tabular-nums" style={color ? { color } : undefined}>{value}</div>
    </div>
  );
}
