/**
 * Thin client for the Python FastAPI sidecar (winsvalinn.sidecar).
 *
 * The sidecar runs at 127.0.0.1:8731. In dev it's started manually
 * (`python -m sidecar`); in production Tauri spawns it on app launch.
 *
 * NOTE: 8731 avoids Windows' Hyper-V/WinNAT excluded port ranges that broke
 * the previous 17893. A fully dynamic port (negotiated with the shell) is the
 * robust long-term fix.
 */

const BASE = "http://127.0.0.1:8731";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      // Custom header: forces a CORS preflight cross-origin, so a malicious web
      // page can't drive the local sidecar (CSRF / DNS-rebinding defense).
      "X-WSV-Client": "winsvalinn",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ─── Types (kept loose; backend is the source of truth) ────────────

export interface SystemHealth {
  cpu: number; ram: number; disk: number;
  score: number; connections: number;
}

export interface SystemInfo {
  os: string; processor: string; machine: string; python: string;
  ram_total_gb?: number; cpu_logical?: number; cpu_physical?: number;
  is_admin?: boolean;
}

export interface OptimizationItem {
  id: string; label: string; applied: boolean;
}

export interface GameAction {
  id: string; label: string; needs_admin: boolean; destructive: boolean; lol_only?: boolean;
  applied?: boolean | null;
}

export interface DetectedGame {
  id: string; name: string; source: string; exes: string[];
  curated: boolean; needs_admin: boolean;
  anticheat?: string | null; tips?: string[]; actions?: GameAction[];
}

export interface GameActionResult {
  ok: boolean; game?: string; action?: string; applied: number;
  is_admin: boolean; log: { msg: string; level: string }[]; error?: string;
}

export interface GamesResponse {
  games: DetectedGame[]; count: number; is_admin: boolean;
  global_actions?: GameAction[];
}

export interface GameOptimizeResult {
  ok: boolean; game?: string; applied: number;
  needs_admin: boolean; is_admin: boolean;
  anticheat?: string | null; tips?: string[];
  log: { msg: string; level: string }[];
  error?: string;
}

export interface OptimizationScore {
  score: number; ram: number; disk: number;
  applied?: number; total?: number; items?: OptimizationItem[];
}

export interface MemoryProcess {
  pid: number; name: string; memory_mb: number;
}

export interface MemoryStats {
  total_gb: number; used_gb: number; available_gb: number;
  percent: number; top_processes: MemoryProcess[];
}

/** Resolved license / edition state from the sidecar. */
export interface LicenseState {
  edition: "free" | "empresarial";
  tier: string | null;
  valid: boolean;
  expiry: string | null;
  email: string | null;
}

/** A remediation action surfaced by the security audit. */
export interface RemediationMeta {
  control: string;
  label: string;
  kind: "fix" | "navigate";
  section?: string;
}

/** A runnable option/tweak exposed by a section (optimization, cleanup, …). */
export interface OptionMeta {
  id: string;
  section: string;
  label: string;
  edition: "free" | "empresarial";
  description: string;
  is_destructive: boolean;
}

/** VirusTotal lookup result (shape kept loose; backend is the source of truth). */
export interface VtResult {
  sha256?: string;
  found?: boolean;
  malicious?: number;
  suspicious?: number;
  harmless?: number;
  undetected?: number;
  link?: string;
  [k: string]: unknown;
}

/** A scheduled scan task (as returned by GET /schedule items[]). */
export interface ScheduleTask {
  id: string;
  scan: string;
  /** Windows Task Scheduler "Schedule Type" (e.g. Daily, Weekly). */
  schedule?: string;
  status?: string;
  next_run?: string;
  last_run?: string;
  [k: string]: unknown;
}

// ─── Endpoints ─────────────────────────────────────────────────────

export const api = {
  health:               () => req<{ ok: boolean; version: string }>("/health"),
  systemHealth:         () => req<SystemHealth>("/system/health"),
  systemInfo:           () => req<SystemInfo>("/system/info"),

  securityAudit:        () => req<any>("/security/audit"),
  securityPorts:        () => req<{ ports: any[] }>("/security/ports"),
  securityProcesses:    () => req<{ processes: any[] }>("/security/processes"),

  optimizationScore:    () => req<OptimizationScore>("/optimization/score"),
  optimizationApply:    (action: string) =>
                          req<any>(`/optimization/${action}`, { method: "POST" }),
  optimizationUiTweaks: (ids: string[], restart: boolean) =>
                          req<any>("/optimization/uitweaks", {
                            method: "POST",
                            body: JSON.stringify({ ids, restart }),
                          }),
  optGroupPlan:         (group: string) =>
                          req<{
                            title: string; subtitle?: string; restart?: boolean;
                            tweaks: { id: string; label: string; applied?: boolean | null }[];
                          }>(`/optimization/plan/${group}`),
  optGroupApply:        (group: string, selected: string[] | null, restart = true) =>
                          req<any>(`/optimization/apply/${group}`, {
                            method: "POST",
                            body: JSON.stringify({ selected, restart }),
                          }),

  adminStatus:          () =>
                          req<{ is_admin: boolean; always_admin: boolean; exe: string | null }>(
                            "/admin/status",
                          ),
  adminAlways:          (enabled: boolean) =>
                          req<{ ok: boolean; always_admin: boolean; error?: string }>(
                            "/admin/always",
                            { method: "POST", body: JSON.stringify({ enabled }) },
                          ),

  games:                () => req<GamesResponse>("/games"),
  gameOptimize:         (gameId: string) =>
                          req<GameOptimizeResult>("/games/optimize", {
                            method: "POST",
                            body: JSON.stringify({ game_id: gameId }),
                          }),
  gameAction:           (gameId: string, action: string) =>
                          req<GameActionResult>("/games/action", {
                            method: "POST",
                            body: JSON.stringify({ game_id: gameId, action }),
                          }),
  gameGlobal:           (action: string) =>
                          req<GameActionResult>("/games/global", {
                            method: "POST",
                            body: JSON.stringify({ action }),
                          }),

  memoryStats:          () => req<MemoryStats>("/memory/stats"),
  memoryFree:           () =>
                          req<any>("/memory/free", { method: "POST" }),

  processesTree:        () => req<{ roots: any[] }>("/processes/tree"),

  networkConnections:   () => req<{ total: number; connections: any[] }>("/network/connections"),

  cleanupAnalyze:       () => req<any>("/cleanup/analyze"),
  cleanupClean:         () => req<any>("/cleanup/clean", { method: "POST" }),
  cleanupDuplicates:    (folder: string, minMb = 1) =>
                          req<any>("/cleanup/duplicates", {
                            method: "POST",
                            body: JSON.stringify({ folder, min_mb: minMb }),
                          }),

  config:               () => req<any>("/config"),
  configPatch:          (keys: string[], value: unknown) =>
                          req<any>("/config", {
                            method: "PATCH",
                            body: JSON.stringify({ keys, value }),
                          }),

  // ── License / edition ────────────────────────────────────────────
  license:              () => req<LicenseState>("/license"),
  licenseActivate:      (key: string) =>
                          req<LicenseState & { ok: boolean; error?: string }>(
                            "/license/activate",
                            { method: "POST", body: JSON.stringify({ key }) },
                          ),
  licenseDeactivate:    () =>
                          req<LicenseState & { ok: boolean }>(
                            "/license/deactivate",
                            { method: "POST" },
                          ),

  // ── Processes ────────────────────────────────────────────────────
  processKill:          (pid: number) =>
                          req<{ ok: boolean; pid: number; error?: string }>(
                            "/processes/" + pid + "/kill",
                            { method: "POST" },
                          ),

  // ── Security remediations ────────────────────────────────────────
  securityRemediations: () =>
                          req<{ items: RemediationMeta[] }>("/security/remediations"),
  securityRemediate:    (control: string) =>
                          req<{
                            ok: boolean;
                            control: string;
                            log: any[];
                            navigate?: string;
                            error?: string;
                          }>(
                            "/security/remediate/" + encodeURIComponent(control),
                            { method: "POST" },
                          ),

  // ── Section options / tweaks ─────────────────────────────────────
  options:              (section: string) =>
                          req<{ options: OptionMeta[] }>(
                            "/options?section=" + encodeURIComponent(section),
                          ),
  optionRun:            (id: string) =>
                          req<{
                            ok: boolean;
                            log: any[];
                            result?: any;
                            error?: string;
                            locked?: boolean;
                          }>(
                            "/options/" + id + "/run",
                            { method: "POST" },
                          ),

  // ── Threat intelligence / VirusTotal ─────────────────────────────
  // VT key is stored server-side via DPAPI; the UI only ever sees status.
  vtStatus:             () => req<{ configured: boolean }>("/threat/vt/status"),
  vtKeySet:             (key: string) =>
                          req<{ ok: boolean; configured: boolean }>("/threat/vt/key", {
                            method: "POST",
                            body: JSON.stringify({ key }),
                          }),
  vtKeyClear:           () =>
                          req<{ ok: boolean; configured: false }>("/threat/vt/key", {
                            method: "DELETE",
                          }),
  vtHash:               (sha256: string) =>
                          req<VtResult>("/threat/vt/hash/" + encodeURIComponent(sha256)),
  vtFile:               (path: string) =>
                          req<VtResult>("/threat/vt/file", {
                            method: "POST",
                            body: JSON.stringify({ path }),
                          }),

  // ── Scheduled scans ──────────────────────────────────────────────
  scheduleList:         () => req<{ ok: boolean; items: ScheduleTask[] }>("/schedule"),
  scheduleCreate:       (body: { scan: string; frequency: string; time?: string }) =>
                          req<{ ok: boolean; id: string }>("/schedule", {
                            method: "POST",
                            body: JSON.stringify(body),
                          }),
  scheduleDelete:       (id: string) =>
                          req<{ ok: boolean }>("/schedule/" + encodeURIComponent(id), {
                            method: "DELETE",
                          }),

  // ── Security report (HTML, not JSON) ─────────────────────────────
  // Raw fetch: the endpoint returns text/html, so we bypass req() and
  // surface the body as a string. Throws "HTTP <status>: ..." on error
  // so callers can detect 402 (Pro-gated) the same way as the JSON path.
  securityReportHtml:   async (): Promise<string> => {
                          const res = await fetch(BASE + "/security/report");
                          if (!res.ok) {
                            const text = await res.text().catch(() => res.statusText);
                            throw new Error(`HTTP ${res.status}: ${text}`);
                          }
                          return res.text();
                        },
};
