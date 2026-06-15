import { useEffect, useMemo, useState } from "react";
import { ChevronRight, ChevronDown, Activity, RefreshCw, Loader2, Search, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "@/components/ui/tooltip";
import { api } from "@/lib/api";
import { SEV_COLOR } from "@/lib/severity";
import { useT } from "../lib/i18n";

interface ProcNode {
  pid: number; ppid: number; name: string; exe: string; username: string;
  memory_mb: number; cpu_percent: number; status: string; children: ProcNode[];
}

function memColor(mb: number): string {
  if (mb >= 500) return SEV_COLOR.crit;
  if (mb >= 200) return SEV_COLOR.med;
  if (mb >= 50) return SEV_COLOR.info;
  return "var(--foreground)";
}

function totalMem(n: ProcNode): number {
  return (n.memory_mb || 0) + (n.children || []).reduce((s, c) => s + totalMem(c), 0);
}

function ProcessRow({
  node, depth, expanded, toggle, search, kill, killing,
}: {
  node: ProcNode; depth: number;
  expanded: Set<number>; toggle: (pid: number) => void; search: string;
  kill: (node: ProcNode) => void; killing: number | null;
}) {
  const t = useT();
  const hasChildren = node.children && node.children.length > 0;
  const isOpen = expanded.has(node.pid);
  const matches = !search || node.name.toLowerCase().includes(search.toLowerCase());
  const isKilling = killing === node.pid;

  const childRows = hasChildren && (isOpen || search)
    ? node.children.map((c) => (
        <ProcessRow key={c.pid} node={c} depth={depth + 1} expanded={expanded} toggle={toggle} search={search} kill={kill} killing={killing} />
      ))
    : [];

  if (search && !matches) {
    const anyDescMatches = (function check(n: ProcNode): boolean {
      if (n.name.toLowerCase().includes(search.toLowerCase())) return true;
      return (n.children || []).some(check);
    })(node);
    if (!anyDescMatches) return null;
  }

  return (
    <>
      <div
        className="group grid grid-cols-[1fr_80px_90px_40px] items-center rounded px-2 py-1 text-sm transition-colors hover:bg-muted/60"
        style={{ paddingLeft: 8 + depth * 18 }}
      >
        <div className="flex min-w-0 items-center gap-1.5">
          {hasChildren ? (
            <button onClick={() => toggle(node.pid)} className="rounded p-0.5 text-muted-foreground hover:bg-muted">
              {isOpen ? <ChevronDown className="size-3.5" /> : <ChevronRight className="size-3.5" />}
            </button>
          ) : (
            <span className="w-[22px] text-center text-muted-foreground">·</span>
          )}
          <span className="truncate font-medium" style={{ color: memColor(node.memory_mb) }} title={node.exe || node.name}>
            {node.name}
          </span>
        </div>
        <span className="tabular text-right text-xs text-muted-foreground">{node.pid}</span>
        <span className="tabular text-right text-xs font-semibold" style={{ color: memColor(node.memory_mb) }}>
          {node.memory_mb.toFixed(0)} MB
        </span>
        <div className="flex justify-end">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={() => kill(node)}
                disabled={isKilling}
                aria-label={`${t("processes.killAriaLabel", "Terminar")} ${node.name}`}
                className="text-muted-foreground opacity-0 hover:text-[var(--severity-crit)] focus-visible:opacity-100 group-hover:opacity-100"
              >
                {isKilling ? <Loader2 className="size-3 animate-spin" /> : <X className="size-3" />}
              </Button>
            </TooltipTrigger>
            <TooltipContent>{t("processes.killTooltip", "Terminar proceso")}</TooltipContent>
          </Tooltip>
        </div>
      </div>
      {(isOpen || search) && childRows.length > 0 && childRows}
    </>
  );
}

export function Processes() {
  const t = useT();
  const [tree, setTree] = useState<ProcNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [search, setSearch] = useState("");
  const [killing, setKilling] = useState<number | null>(null);

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.processesTree();
      setTree((r.roots || []).slice().sort((a, b) => totalMem(b) - totalMem(a)));
    } catch { /* */ } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const kill = async (node: ProcNode) => {
    if (killing != null) return;
    const confirmed = window.confirm(
      `${t("processes.confirmKill", "¿Terminar el proceso")} "${node.name}" (PID ${node.pid})?\n\n` +
      t("processes.confirmKillWarning", "Se cerrará inmediatamente y podrías perder datos no guardados."),
    );
    if (!confirmed) return;
    setKilling(node.pid);
    try {
      const r = await api.processKill(node.pid);
      if (r.ok) {
        toast.success(`${t("processes.toastKilled", "Proceso terminado")}: ${node.name} (PID ${node.pid})`);
        await refresh();
      } else {
        toast.error(r.error || `${t("processes.toastKillFailed", "No se pudo terminar")} ${node.name} (PID ${node.pid}).`);
      }
    } catch (e: any) {
      const msg = String(e?.message ?? "");
      if (msg.includes("403")) {
        toast.error(t("processes.toastKillAdmin", "Requiere privilegios de administrador. Reinicia WinSvalinn como administrador."));
      } else if (msg.includes("404")) {
        toast.warning(`${t("processes.toastKillGone", "El proceso")} ${node.name} (PID ${node.pid}) ${t("processes.toastKillGoneSuffix", "ya no existe.")}`);
        await refresh();
      } else {
        toast.error(`${t("processes.toastKillError", "Error al terminar el proceso")}: ${msg || t("processes.toastKillErrorUnknown", "desconocido")}`);
      }
    } finally {
      setKilling(null);
    }
  };

  const toggle = (pid: number) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(pid)) next.delete(pid); else next.add(pid);
      return next;
    });

  const expandAll = () => {
    const all = new Set<number>();
    const walk = (n: ProcNode) => { if (n.children?.length) { all.add(n.pid); n.children.forEach(walk); } };
    tree.forEach(walk);
    setExpanded(all);
  };

  const totalProcs = useMemo(() => {
    let n = 0;
    const walk = (node: ProcNode) => { n++; (node.children || []).forEach(walk); };
    tree.forEach(walk);
    return n;
  }, [tree]);

  return (
    <div className="flex h-full flex-col gap-4 overflow-hidden p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-heading text-2xl font-semibold">
            <span className="text-gradient">{t("processes.title", "Procesos")}</span>
          </h1>
          <p className="text-sm text-muted-foreground">{totalProcs} {t("processes.subtitle", "procesos · árbol parent-child")}</p>
        </div>
        <Button variant="outline" onClick={refresh} disabled={loading}>
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          {loading ? t("processes.loading", "Cargando…") : t("processes.refresh", "Refrescar")}
        </Button>
      </header>

      <div className="glass flex min-h-0 flex-1 flex-col gap-3 rounded-2xl p-4">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={t("processes.filterPlaceholder", "Filtrar por nombre…")} className="pl-8" />
            </div>
            <Button variant="ghost" size="sm" onClick={expandAll}>{t("processes.expandAll", "Expandir")}</Button>
            <Button variant="ghost" size="sm" onClick={() => setExpanded(new Set())}>{t("processes.collapseAll", "Colapsar")}</Button>
          </div>

          <TooltipProvider delayDuration={300}>
            <div className="min-h-0 flex-1 overflow-y-auto rounded-lg border border-border">
              <div className="tabular sticky top-0 grid grid-cols-[1fr_80px_90px_40px] border-b border-border bg-card px-3 py-2 text-xs font-semibold text-muted-foreground">
                <span>{t("processes.colProcess", "Proceso")}</span>
                <span className="text-right">PID</span>
                <span className="text-right">{t("processes.colMemory", "Memoria")}</span>
                <span className="text-right">{t("processes.colAction", "Acción")}</span>
              </div>
              <div className="p-1">
                {tree.length === 0 && !loading && (
                  <div className="py-12 text-center text-muted-foreground">
                    <Activity className="mx-auto mb-2 size-8 opacity-50" />
                    <p className="text-sm">{t("processes.empty", "Sin procesos cargados")}</p>
                  </div>
                )}
                {tree.map((root) => (
                  <ProcessRow key={root.pid} node={root} depth={0} expanded={expanded} toggle={toggle} search={search} kill={kill} killing={killing} />
                ))}
              </div>
            </div>
          </TooltipProvider>
      </div>
    </div>
  );
}
