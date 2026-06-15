import { useEffect, useState } from "react";
import { Trash2, Search, Loader2, Files } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { api } from "@/lib/api";
import { SEV_COLOR } from "@/lib/severity";
import { useT } from "../lib/i18n";

interface DupGroup { size_bytes: number; hash: string; paths: string[]; waste_bytes: number; }
interface DupResult {
  success: boolean; scanned: number; groups: DupGroup[];
  total_waste_bytes: number; folder?: string;
}

function fmtBytes(n: number): string {
  if (n > 1024 ** 3) return (n / 1024 ** 3).toFixed(1) + " GB";
  if (n > 1024 ** 2) return (n / 1024 ** 2).toFixed(1) + " MB";
  return (n / 1024).toFixed(0) + " KB";
}

interface Location {
  path: string;
  size_bytes: number;
  size_readable: string;
  file_count: number;
}

interface AnalyzeResult {
  total_size: number;
  total_readable: string;
  locations: Location[];
}

interface LogLine { ts: string; msg: string; level: "info" | "ok" | "warn" | "err"; }

export function Cleanup() {
  const t = useT();
  const [data, setData] = useState<AnalyzeResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [log, setLog] = useState<LogLine[]>([]);
  const [showLog, setShowLog] = useState(false);
  const [dupFolder, setDupFolder] = useState("");
  const [dupScanning, setDupScanning] = useState(false);
  const [dups, setDups] = useState<DupResult | null>(null);

  const append = (msg: string, level: LogLine["level"] = "info") =>
    setLog((p) => [{ ts: new Date().toLocaleTimeString(), msg, level }, ...p.slice(0, 200)]);

  useEffect(() => {
    api.config()
      .then((c) => setShowLog(c?.ui?.show_activity_log === true))
      .catch(() => { /* keep hidden by default */ });
  }, []);

  const onAnalyze = async () => {
    setAnalyzing(true);
    append(t("cleanup.log.analyzingStart", "▶ Analizando archivos temporales…"));
    try {
      const r: AnalyzeResult = await api.cleanupAnalyze();
      setData(r);
      (r.locations || []).forEach((loc) =>
        append(`  · ${loc.path}: ${loc.file_count} ${t("cleanup.log.files", "archivos")}, ${loc.size_readable}`));
      append(`━━ ${t("cleanup.log.totalRecoverable", "Total recuperable")}: ${r.total_readable} ━━`,
        (r.total_size / 1024 / 1024) > 100 ? "ok" : "info");
    } catch (e: any) {
      append(`${t("cleanup.log.error", "Error")}: ${e.message}`, "err");
    } finally {
      setAnalyzing(false);
    }
  };

  const onClean = async () => {
    setCleaning(true);
    append(t("cleanup.log.cleaningStart", "▶ Limpiando archivos temporales…"));
    try {
      const r: any = await api.cleanupClean();
      append(`✓ ${r?.files_cleaned ?? 0} ${t("cleanup.log.filesDeleted", "archivos eliminados")}, ${r?.freed_space ?? "?"} ${t("cleanup.log.freed", "liberados")}`, "ok");
      const errors = r?.errors;
      if (typeof errors === "number" && errors > 0) append(`⚠ ${errors} ${t("cleanup.log.nonCriticalErrors", "errores no críticos")}`, "warn");
      else if (Array.isArray(errors)) errors.slice(0, 10).forEach((e: any) => append(`  ⚠ ${e}`, "warn"));
      await onAnalyze();
    } catch (e: any) {
      append(`${t("cleanup.log.error", "Error")}: ${e.message}`, "err");
    } finally {
      setCleaning(false);
    }
  };

  const onFindDuplicates = async () => {
    setDupScanning(true);
    append(`▶ ${t("cleanup.log.searchingDuplicatesIn", "Buscando duplicados en")} ${dupFolder || t("cleanup.log.defaultFolder", "Descargas")}…`);
    try {
      const r: DupResult = await api.cleanupDuplicates(dupFolder);
      setDups(r);
      append(
        `✓ ${r.groups.length} ${t("cleanup.log.groups", "grupos")}, ${fmtBytes(r.total_waste_bytes)} ${t("cleanup.log.recoverable", "recuperables")} (${r.scanned} ${t("cleanup.log.files", "archivos")})`,
        r.groups.length ? "ok" : "info",
      );
    } catch (e: any) {
      append(`${t("cleanup.log.error", "Error")}: ${e.message}`, "err");
    } finally {
      setDupScanning(false);
    }
  };

  const totalMb = data ? data.total_size / (1024 * 1024) : 0;
  const totalColor = totalMb > 500 ? SEV_COLOR.crit : totalMb > 100 ? SEV_COLOR.med : "var(--primary)";

  return (
    <div className="h-full space-y-5 overflow-y-auto p-6">
      <header>
        <h1 className="font-heading text-2xl font-semibold">
          {t("cleanup.title", "Limpieza de")} <span className="text-gradient">{t("cleanup.titleHighlight", "disco")}</span>
        </h1>
        <p className="text-sm text-muted-foreground">{t("cleanup.subtitle", "Temporales, cache, prefetch, Windows Update.")}</p>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-[260px_1fr]">
        <div className="glass glass-glow rounded-2xl p-6">
          <div className="text-sm text-muted-foreground">{t("cleanup.recoverableSpace", "Espacio recuperable")}</div>
          <div className="mt-3 text-4xl font-bold tabular-nums" style={{ color: totalColor }}>
            {data?.total_readable ?? "—"}
          </div>
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="text-sm font-semibold">{t("cleanup.actions", "Acciones")}</div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button variant="outline" onClick={onAnalyze} disabled={analyzing || cleaning}>
              {analyzing ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />}
              {analyzing ? t("cleanup.btn.analyzing", "Analizando…") : t("cleanup.btn.analyze", "Analizar")}
            </Button>
            <Button className="bg-accent-gradient ring-glow text-primary-foreground" onClick={onClean} disabled={analyzing || cleaning}>
              {cleaning ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
              {cleaning ? t("cleanup.btn.cleaning", "Limpiando…") : t("cleanup.btn.cleanAll", "Limpiar todo")}
            </Button>
          </div>
        </div>
      </section>

      {data && data.locations && data.locations.length > 0 && (
        <div className="glass rounded-2xl p-6">
          <div className="text-sm font-semibold">{t("cleanup.scannedLocations", "Ubicaciones escaneadas")}</div>
          <div className="mt-4 max-h-72 overflow-y-auto rounded-xl border border-border bg-card">
            <Table>
              <TableHeader className="sticky top-0 bg-card">
                <TableRow>
                  <TableHead>{t("cleanup.table.path", "Ruta")}</TableHead>
                  <TableHead className="text-right">{t("cleanup.table.files", "Archivos")}</TableHead>
                  <TableHead className="text-right">{t("cleanup.table.size", "Tamaño")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.locations.map((loc) => (
                  <TableRow key={loc.path}>
                    <TableCell className="tabular max-w-0 truncate text-xs" title={loc.path}>{loc.path}</TableCell>
                    <TableCell className="tabular text-right text-muted-foreground">{loc.file_count.toLocaleString()}</TableCell>
                    <TableCell className="tabular text-right font-semibold">{loc.size_readable}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}

      <div className="glass rounded-2xl p-6">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Files className="size-4 text-primary" /> {t("cleanup.duplicates.title", "Archivos duplicados")}
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          {t("cleanup.duplicates.subtitle", "Busca duplicados por hash (SHA-256) en la carpeta que elijas; por defecto, Descargas.")}
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Input
            value={dupFolder}
            onChange={(e) => setDupFolder(e.target.value)}
            placeholder={t("cleanup.duplicates.folderPlaceholder", "C:\\Users\\…\\Descargas (por defecto)")}
            className="max-w-md font-mono text-xs"
          />
          <Button variant="outline" onClick={onFindDuplicates} disabled={dupScanning}>
            {dupScanning ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />}
            {dupScanning ? t("cleanup.btn.searching", "Buscando…") : t("cleanup.btn.findDuplicates", "Buscar duplicados")}
          </Button>
        </div>
        {dups && (
          <div className="mt-4 text-xs">
            <div className="text-muted-foreground">
              {dups.scanned} {t("cleanup.duplicates.filesScanned", "archivos escaneados")} · {dups.groups.length} {t("cleanup.duplicates.groups", "grupos")} ·{" "}
              {fmtBytes(dups.total_waste_bytes)} {t("cleanup.duplicates.recoverable", "recuperables")}
              {dups.folder ? ` · ${dups.folder}` : ""}
            </div>
            {dups.groups.length > 0 ? (
              <div className="mt-3 max-h-72 space-y-2 overflow-y-auto">
                {dups.groups.slice(0, 50).map((g, i) => (
                  <div key={i} className="rounded-lg border border-border bg-card p-2">
                    <div className="font-semibold">
                      {g.paths.length} {t("cleanup.duplicates.copies", "copias")} · {fmtBytes(g.size_bytes)} {t("cleanup.duplicates.each", "c/u")} · {t("cleanup.duplicates.wasted", "sobran")}{" "}
                      {fmtBytes(g.waste_bytes)}
                    </div>
                    {g.paths.map((p, j) => (
                      <div key={j} className="truncate text-muted-foreground" title={p}>
                        · {p}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-2 text-muted-foreground">{t("cleanup.duplicates.noneFound", "No se encontraron duplicados.")}</div>
            )}
          </div>
        )}
      </div>

      {showLog && (
        <div className="glass rounded-2xl p-6">
          <div className="text-sm font-semibold">{t("cleanup.log.title", "Log")}</div>
          <div className="tabular mt-3 h-40 overflow-y-auto rounded-lg bg-background p-3 text-xs">
            {log.length === 0 && <div className="text-muted-foreground">{t("cleanup.log.empty", "Pulsa \"Analizar\" para empezar.")}</div>}
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

function logColor(level: LogLine["level"]): string {
  return level === "ok" ? "var(--severity-ok)"
    : level === "warn" ? "var(--severity-med)"
    : level === "err" ? "var(--severity-crit)"
    : "var(--muted-foreground)";
}
