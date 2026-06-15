import { useEffect, useId, useState } from "react";
import {
  Cpu, MemoryStick, HardDrive, Network as NetIcon, Play, Loader2,
  ShieldCheck, Activity, Gauge, Zap, type LucideIcon,
} from "lucide-react";
import { api, type SystemHealth, type SystemInfo } from "@/lib/api";
import { useSecurityState, securityStore } from "@/lib/cache";
import { scoreSev, usageSev, SEV_COLOR, type Sev } from "@/lib/severity";
import { useT } from "../lib/i18n";

/* ─── Neon score ring ─────────────────────────────────────────────────── */
function ScoreRing({
  value, size = 168,
}: { value: number | null; size?: number }) {
  const gid = "ring" + useId().replace(/:/g, "");
  const stroke = 12;
  const r = size / 2 - stroke;
  const c = 2 * Math.PI * r;
  const v = Math.min(100, Math.max(0, value ?? 0));
  const off = c - (v / 100) * c;
  const sev = scoreSev(value);
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--accent-from)" />
            <stop offset="100%" stopColor="var(--accent-to)" />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="color-mix(in oklch, white 8%, transparent)" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={`url(#${gid})`} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={off}
          style={{ transition: "stroke-dashoffset 0.8s cubic-bezier(.4,0,.2,1)", filter: "drop-shadow(0 0 8px color-mix(in oklch, var(--accent-from) 60%, transparent))" }} />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-5xl font-bold tabular-nums" style={{ color: SEV_COLOR[sev] }}>
          {value == null ? "—" : value}
        </span>
        <span className="text-xs text-muted-foreground">/ 100</span>
      </div>
    </div>
  );
}

function MiniScore({
  label, icon: Icon, value,
}: { label: string; icon: LucideIcon; value: number | null }) {
  const sev = scoreSev(value);
  return (
    <div className="glass flex flex-col justify-between rounded-2xl p-4">
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <Icon className="size-3.5" /> {label}
      </div>
      <div className="mt-3 flex items-end justify-between">
        <span className="text-3xl font-bold tabular-nums" style={{ color: SEV_COLOR[sev] }}>
          {value == null ? "—" : value}
        </span>
        <span className="text-[11px] text-muted-foreground">/100</span>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/5">
        <div className="h-full rounded-full bg-accent-gradient transition-all"
          style={{ width: `${value ?? 0}%` }} />
      </div>
    </div>
  );
}

function Kpi({
  label, icon: Icon, pct, display,
}: { label: string; icon: LucideIcon; pct: number | null; display: string }) {
  const sev: Sev = pct == null ? "info" : usageSev(pct);
  return (
    <div className="glass rounded-2xl p-4">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span className="grid size-7 place-items-center rounded-lg bg-white/5 text-[var(--accent-from)]">
          <Icon className="size-3.5" />
        </span>
        {label}
      </div>
      <div className="mt-3 text-2xl font-bold tabular-nums">{display}</div>
      {pct != null && (
        <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/5">
          <div className="h-full rounded-full transition-all"
            style={{ width: `${pct}%`, background: SEV_COLOR[sev] }} />
        </div>
      )}
    </div>
  );
}

export function Dashboard() {
  const t = useT();
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [optScore, setOptScore] = useState<number | null>(null);
  const [online, setOnline] = useState(false);
  const sec = useSecurityState();

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const h = await api.systemHealth();
        if (!cancelled) { setHealth(h); setOnline(true); }
      } catch { if (!cancelled) setOnline(false); }
    };
    tick();
    const id = setInterval(tick, 1500);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  // System info is static — load it as soon as the sidecar answers, retrying
  // until it does (the sidecar can take a few seconds to come up on launch).
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      try {
        const i = await api.systemInfo();
        if (!cancelled) setInfo(i);
      } catch {
        if (!cancelled) timer = setTimeout(load, 1200);
      }
    };
    load();
    return () => { cancelled = true; clearTimeout(timer); };
  }, []);

  // Optimization score — same: keep retrying until the sidecar is reachable.
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      try {
        const s = await api.optimizationScore();
        if (!cancelled) setOptScore(s.score);
      } catch {
        if (!cancelled) timer = setTimeout(load, 1200);
      }
    };
    load();
    return () => { cancelled = true; clearTimeout(timer); };
  }, []);

  const runSecurityScan = async () => {
    const cur = securityStore.get();
    if (cur.running) return;
    securityStore.set({ ...cur, running: true });
    try {
      const r: any = await api.securityAudit();
      securityStore.set({ score: r?.score ?? null, ranAt: Date.now(), running: false });
    } catch {
      securityStore.set({ ...securityStore.get(), running: false });
    }
  };

  // Auto-scan once the sidecar is reachable, retrying the probe until it is, so
  // the score shows up on its own (no need to navigate away and back).
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    const start = async () => {
      const s = securityStore.get();
      if (s.score !== null || s.running) return;
      try {
        await api.systemHealth();
      } catch {
        if (!cancelled) timer = setTimeout(start, 1200);
        return;
      }
      if (!cancelled) runSecurityScan();
    };
    start();
    return () => { cancelled = true; clearTimeout(timer); };
  }, []);

  return (
    <div className="h-full space-y-5 overflow-y-auto p-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-heading text-2xl font-semibold tracking-tight">
            {t("dashboard.controlCenterPre", "Centro de ")} <span className="text-gradient">{t("dashboard.controlCenterHighlight", "control")}</span>
          </h1>
          <p className="text-sm text-muted-foreground">{t("dashboard.subtitle", "Salud, seguridad y rendimiento en tiempo real.")}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs">
            <span className={`size-2 rounded-full ${online ? "bg-[var(--severity-ok)]" : "bg-[var(--severity-crit)]"}`}
              style={online ? { boxShadow: "0 0 8px var(--severity-ok)" } : undefined} />
            {online ? t("dashboard.engineActive", "Motor activo") : t("dashboard.engineOffline", "Sin conexión")}
          </span>
        </div>
      </header>

      {/* Bento: hero score + mini scores */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="glass-glow flex flex-col items-center justify-center gap-3 rounded-3xl p-6 lg:row-span-2">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <ShieldCheck className="size-4 text-[var(--accent-from)]" /> {t("dashboard.securityScore", "Puntuación de seguridad")}
          </div>
          <ScoreRing value={sec.score} />
          {sec.running ? (
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Loader2 className="size-3.5 animate-spin" /> {t("dashboard.scanning", "Analizando seguridad…")}
            </p>
          ) : sec.score == null ? (
            <button
              onClick={runSecurityScan}
              className="flex items-center gap-1.5 rounded-full bg-accent-gradient px-4 py-1.5 text-xs font-semibold text-[#05080d] ring-glow"
            >
              <Play className="size-3.5" /> {t("dashboard.analyze", "Analizar seguridad")}
            </button>
          ) : (
            <button
              onClick={runSecurityScan}
              className="text-xs text-muted-foreground underline-offset-2 transition-colors hover:text-foreground hover:underline"
            >
              {t("dashboard.rescan", "Volver a escanear")}
            </button>
          )}
          <p className="max-w-[14rem] text-center text-xs text-muted-foreground">
            {t("dashboard.securityDescription", "Análisis de firewall, Defender, hardening, puertos y procesos.")}
          </p>
        </div>
        <MiniScore label={t("dashboard.systemHealth", "Salud del sistema")} icon={Activity} value={health?.score ?? null} />
        <MiniScore label={t("dashboard.optimization", "Optimización")} icon={Gauge} value={optScore} />
        <div className="glass rounded-2xl p-4 lg:col-span-2">
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <Zap className="size-3.5 text-[var(--accent-from)]" /> {t("dashboard.liveResources", "Recursos en vivo")}
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Kpi label="CPU" icon={Cpu} pct={health?.cpu ?? null} display={health ? `${health.cpu}%` : "—"} />
            <Kpi label="RAM" icon={MemoryStick} pct={health?.ram ?? null} display={health ? `${health.ram}%` : "—"} />
            <Kpi label={t("dashboard.disk", "Disco")} icon={HardDrive} pct={health?.disk ?? null} display={health ? `${health.disk}%` : "—"} />
            <Kpi label={t("dashboard.connections", "Conexiones")} icon={NetIcon} pct={null} display={`${health?.connections ?? "—"}`} />
          </div>
        </div>
      </section>

      {/* System info */}
      <section className="glass rounded-3xl p-6">
        <h2 className="mb-4 font-heading text-sm font-semibold">{t("dashboard.systemInfo", "Información del sistema")}</h2>
        <dl className="grid grid-cols-1 gap-x-10 gap-y-3 text-sm sm:grid-cols-2">
          <Row k={t("dashboard.os", "Sistema operativo")} v={info?.os ?? "—"} />
          <Row k={t("dashboard.architecture", "Arquitectura")} v={info?.machine ?? "—"} mono />
          <Row k={t("dashboard.processor", "Procesador")} v={info?.processor || "—"} />
          <Row k={t("dashboard.logicalCpus", "CPU lógicos")} v={info?.cpu_logical?.toString() ?? "—"} mono />
          <Row k={t("dashboard.totalRam", "RAM total")} v={info?.ram_total_gb ? `${info.ram_total_gb} GB` : "—"} mono />
          <Row k={t("dashboard.python", "Python")} v={info?.python ?? "—"} mono />
        </dl>
      </section>
    </div>
  );
}

function Row({ k, v, mono }: { k: string; v: string; mono?: boolean }) {
  return (
    <div className="flex justify-between gap-4 border-b border-white/5 pb-2">
      <dt className="text-muted-foreground">{k}</dt>
      <dd className={mono ? "tabular text-right" : "text-right font-medium"}>{v}</dd>
    </div>
  );
}
