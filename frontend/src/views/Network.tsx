import { useEffect, useMemo, useState } from "react";
import { RefreshCw, Loader2, AlertTriangle, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { api } from "@/lib/api";
import { SEV_COLOR } from "@/lib/severity";
import { useT } from "../lib/i18n";

interface Conn {
  pid: number; process: string; local: string; remote: string;
  status: string; type: string; suspicious: boolean;
}

const statusColor = (s: string) =>
  s === "ESTABLISHED" ? SEV_COLOR.ok :
  s === "LISTEN" ? SEV_COLOR.med :
  "var(--muted-foreground)";

export function Network() {
  const t = useT();
  const [rows, setRows] = useState<Conn[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [onlySuspicious, setOnlySuspicious] = useState(false);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await api.networkConnections();
      setRows(r.connections || []);
      setTotal(r.total || 0);
    } catch (e: any) {
      setError(e.message);
      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const filtered = useMemo(() => {
    let out = rows;
    if (onlySuspicious) out = out.filter((r) => r.suspicious);
    if (search) {
      const q = search.toLowerCase();
      out = out.filter((r) =>
        r.process.toLowerCase().includes(q) ||
        r.remote.toLowerCase().includes(q) ||
        r.local.toLowerCase().includes(q));
    }
    return out;
  }, [rows, onlySuspicious, search]);

  const suspiciousCount = rows.filter((r) => r.suspicious).length;

  return (
    <div className="flex h-full flex-col gap-4 overflow-hidden p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-heading text-2xl font-semibold">
            {t("network.titlePrefix", "Monitor de")} <span className="text-gradient">{t("network.titleHighlight", "red")}</span>
          </h1>
          <p className="text-sm text-muted-foreground">
            {total} {t("network.statActiveConnections", "conexiones activas")} · {suspiciousCount} {t("network.statSuspicious", "sospechosas")} · {t("network.statTop150", "top 150 mostradas")}
          </p>
        </div>
        <Button variant="outline" onClick={refresh} disabled={loading}>
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          {loading ? t("network.btnLoading", "Cargando…") : t("network.btnRefresh", "Refrescar")}
        </Button>
      </header>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="size-4" />
          <AlertTitle>{t("network.errorTitle", "No se pudieron leer todas las conexiones")}</AlertTitle>
          <AlertDescription>{error} — {t("network.errorRunAsAdmin", "ejecuta como Administrador para verlas todas.")}</AlertDescription>
        </Alert>
      )}

      <div className="glass flex min-h-0 flex-1 flex-col gap-3 rounded-2xl p-4">
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t("network.searchPlaceholder", "Filtrar por proceso o IP…")}
                className="pl-8"
              />
            </div>
            <div className="flex items-center gap-2">
              <Switch id="susp" checked={onlySuspicious} onCheckedChange={setOnlySuspicious} />
              <Label htmlFor="susp" className="text-xs">{t("network.filterSuspiciousOnly", "Solo sospechosas")}</Label>
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto rounded-lg border border-border">
            <Table>
              <TableHeader className="sticky top-0 bg-card">
                <TableRow>
                  <TableHead>{t("network.colProcess", "Proceso")}</TableHead>
                  <TableHead>{t("network.colLocal", "Local")}</TableHead>
                  <TableHead>{t("network.colRemote", "Remoto")}</TableHead>
                  <TableHead>{t("network.colStatus", "Estado")}</TableHead>
                  <TableHead className="text-right">PID</TableHead>
                  <TableHead>{t("network.colType", "Tipo")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 && !loading && (
                  <TableRow>
                    <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                      {t("network.emptyState", "Sin conexiones que coincidan")}
                    </TableCell>
                  </TableRow>
                )}
                {filtered.map((c, i) => (
                  <TableRow key={`${c.pid}-${c.local}-${c.remote}-${i}`}
                    style={c.suspicious ? { background: `color-mix(in oklch, ${SEV_COLOR.crit} 10%, transparent)` } : undefined}>
                    <TableCell className="max-w-0 truncate font-medium" title={c.process}>
                      {c.suspicious && <AlertTriangle className="mr-1 inline size-3" style={{ color: SEV_COLOR.crit }} />}
                      {c.process}
                    </TableCell>
                    <TableCell className="tabular max-w-0 truncate text-xs" title={c.local}>{c.local}</TableCell>
                    <TableCell className="tabular max-w-0 truncate text-xs" title={c.remote}>{c.remote}</TableCell>
                    <TableCell className="text-xs font-medium" style={{ color: statusColor(c.status) }}>{c.status}</TableCell>
                    <TableCell className="tabular text-right text-xs text-muted-foreground">{c.pid || "—"}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{c.type}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
      </div>
    </div>
  );
}
