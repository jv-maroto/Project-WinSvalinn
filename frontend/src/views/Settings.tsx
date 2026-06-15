import { useEffect, useState } from "react";
import {
  Languages, FolderOpen, ShieldAlert, KeyRound, Loader2, Check,
  BadgeCheck, Monitor, CalendarClock, Plus, Trash2, type LucideIcon,
} from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ProBadge } from "@/components/ProBadge";
import { api, type ScheduleTask } from "@/lib/api";
import { hasFeature, useEdition, setLicenseState } from "@/lib/edition";
import { SEV_COLOR } from "@/lib/severity";
import { useT, useLang, setLang, type Lang } from "@/lib/i18n";

interface Cfg {
  ui?: {
    language?: string; theme?: string; auto_elevate?: boolean;
    confirm_destructive_actions?: boolean; dry_run_default?: boolean;
    show_activity_log?: boolean; palette?: string;
  };
  logging?: { folder?: string };
  integrations?: { virustotal_api_key?: string };
  telemetry?: { opt_in?: boolean };
}

export function Settings() {
  const [cfg, setCfg] = useState<Cfg | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState<string | null>(null);
  const [vtKey, setVtKey] = useState("");
  const [vtConfigured, setVtConfigured] = useState<boolean | null>(null);
  const [vtBusy, setVtBusy] = useState(false);
  const [logFolder, setLogFolder] = useState("");
  const [licenseKey, setLicenseKey] = useState("");
  const [licenseBusy, setLicenseBusy] = useState(false);
  const [adminInfo, setAdminInfo] = useState({ is_admin: false, always_admin: false });
  const [adminBusy, setAdminBusy] = useState(false);
  const license = useEdition();
  const t = useT();
  const { lang } = useLang();

  useEffect(() => {
    api.config()
      .then((c) => {
        setCfg(c);
        setLogFolder(c?.logging?.folder ?? "");
      })
      .catch(() => {})
      .finally(() => setLoading(false));
    // VirusTotal key lives server-side (DPAPI); we only ever read its status.
    api.vtStatus()
      .then((s) => setVtConfigured(s.configured))
      .catch(() => setVtConfigured(null));
    api.adminStatus()
      .then((s) => setAdminInfo({ is_admin: s.is_admin, always_admin: s.always_admin }))
      .catch(() => {});
  }, []);

  const toggleAlwaysAdmin = async (enabled: boolean) => {
    setAdminBusy(true);
    try {
      const r = await api.adminAlways(enabled);
      if (r.ok) {
        setAdminInfo((s) => ({ ...s, always_admin: r.always_admin }));
        toast.success(
          enabled ? t("settings.admin.toastEnabled", "Se iniciará como Administrador") : t("settings.admin.toastDisabled", "Inicio normal restaurado"),
          { description: enabled ? t("settings.admin.toastEnabledDesc", "La próxima vez que abras la app, Windows pedirá permiso (UAC).") : undefined },
        );
      } else {
        toast.error(t("settings.admin.toastError", "No se pudo cambiar"), { description: r.error ?? t("settings.admin.toastErrorDesc", "Inténtalo de nuevo.") });
      }
    } catch (e: any) {
      toast.error(t("settings.errorGeneric", "Error"), { description: String(e?.message ?? "") });
    } finally {
      setAdminBusy(false);
    }
  };

  const patch = async (keys: string[], value: unknown) => {
    try {
      const r = await api.configPatch(keys, value);
      setCfg(r.data);
      setSaved(keys.join("."));
      setTimeout(() => setSaved(null), 1500);
    } catch { /* */ }
  };

  const activateLicense = async () => {
    const key = licenseKey.trim();
    if (!key || licenseBusy) return;
    setLicenseBusy(true);
    try {
      const r = await api.licenseActivate(key);
      if (r.ok) {
        setLicenseState(r);
        setLicenseKey("");
        toast.success(t("settings.license.activated", "Licencia activada"), {
          description: r.email ? `${t("settings.license.editionEnterprise", "Empresarial")} · ${r.email}` : t("settings.license.activatedDesc", "Edición Empresarial activada."),
        });
      } else {
        toast.error(t("settings.license.activateError", "No se pudo activar la licencia"), { description: r.error || t("settings.license.activateErrorDesc", "Clave no válida.") });
      }
    } catch (e: any) {
      toast.error(t("settings.license.activateError", "No se pudo activar la licencia"), { description: String(e?.message ?? t("settings.errorConnection", "Error de conexión.")) });
    } finally {
      setLicenseBusy(false);
    }
  };

  const deactivateLicense = async () => {
    if (licenseBusy) return;
    setLicenseBusy(true);
    try {
      const r = await api.licenseDeactivate();
      setLicenseState(r);
      toast.success(t("settings.license.deactivated", "Licencia desactivada"), { description: t("settings.license.deactivatedDesc", "Has vuelto a la edición Free.") });
    } catch (e: any) {
      toast.error(t("settings.license.deactivateError", "No se pudo desactivar la licencia"), { description: String(e?.message ?? t("settings.errorConnection", "Error de conexión.")) });
    } finally {
      setLicenseBusy(false);
    }
  };

  const saveVtKey = async () => {
    const key = vtKey.trim();
    if (!key || vtBusy) return;
    setVtBusy(true);
    try {
      const r = await api.vtKeySet(key);
      setVtConfigured(r.configured);
      setVtKey("");
      toast.success(t("settings.vt.saved"));
    } catch (e: any) {
      const msg = String(e?.message ?? "");
      if (msg.includes("402")) {
        toast.warning(t("options.lockedToast"), { description: t("options.lockedToastAction") });
      } else {
        toast.error(t("settings.vt.saveError"), { description: msg });
      }
    } finally {
      setVtBusy(false);
    }
  };

  const clearVtKey = async () => {
    if (vtBusy) return;
    setVtBusy(true);
    try {
      const r = await api.vtKeyClear();
      setVtConfigured(r.configured);
      setVtKey("");
      toast.success(t("settings.vt.cleared"));
    } catch (e: any) {
      toast.error(t("settings.vt.clearError"), { description: String(e?.message ?? "") });
    } finally {
      setVtBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="grid h-full place-items-center">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> {t("options.loading", "Cargando configuración…")}
        </div>
      </div>
    );
  }

  const vtPro = !hasFeature("advancedPlugins");

  return (
    <div className="h-full max-w-4xl space-y-5 overflow-y-auto p-6">
      <header>
        <h1 className="font-heading text-2xl font-semibold">{t("settings.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("settings.subtitle")}</p>
      </header>

      {saved && (
        <Alert>
          <Check className="size-4" style={{ color: SEV_COLOR.ok }} />
          <AlertDescription>{t("settings.saved")}: <code>{saved}</code></AlertDescription>
        </Alert>
      )}

      <Section icon={Languages} title={t("settings.language")}>
        <div className="flex gap-2">
          {[{ v: "es" as Lang, label: "Español" }, { v: "en" as Lang, label: "English" }].map((opt) => (
            <Button key={opt.v} variant={lang === opt.v ? "default" : "outline"} size="sm"
              onClick={() => {
                setLang(opt.v);                         // live switch + persists ui.language
                setCfg((c) => ({ ...c, ui: { ...c?.ui, language: opt.v } }));
              }}>
              {opt.label}
            </Button>
          ))}
        </div>
      </Section>

      <Section
        icon={ShieldAlert}
        title={t("settings.admin.title", "Administrador")}
        badge={
          <Badge
            variant="outline"
            className="gap-1.5"
            style={{ color: adminInfo.is_admin ? SEV_COLOR.ok : "var(--muted-foreground)" }}
          >
            <ShieldAlert className="size-3" />
            {adminInfo.is_admin ? t("settings.admin.badgeAdmin", "Administrador") : t("settings.admin.badgeUser", "Usuario")}
          </Badge>
        }
      >
        <div className="flex items-center justify-between gap-4">
          <div className="space-y-0.5">
            <Label>{t("settings.admin.alwaysLabel", "Iniciar siempre como Administrador")}</Label>
            <p className="text-xs leading-relaxed text-muted-foreground">
              {t("settings.admin.alwaysDesc", "Algunas optimizaciones y soluciones de seguridad necesitan permisos de Administrador. Si lo activas, Windows pedirá permiso (UAC) cada vez que abras WinSvalinn.")}
            </p>
          </div>
          <Switch
            checked={adminInfo.always_admin}
            disabled={adminBusy}
            onCheckedChange={toggleAlwaysAdmin}
          />
        </div>
      </Section>

      <Section
        icon={BadgeCheck}
        title={t("settings.license")}
        badge={
          <Badge
            variant="outline"
            className="gap-1.5"
            style={{ color: license.edition === "empresarial" ? SEV_COLOR.ok : "var(--muted-foreground)" }}
          >
            <BadgeCheck className="size-3" />
            {license.edition === "empresarial" ? t("settings.license.editionEnterprise", "Empresarial") : t("settings.license.editionFree", "Free")}
          </Badge>
        }
      >
        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-muted/30 p-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">{t("settings.license.currentEdition", "Edición actual")}</span>
              <span className="font-semibold" style={{ color: license.edition === "empresarial" ? SEV_COLOR.ok : undefined }}>
                {license.edition === "empresarial" ? t("settings.license.editionEnterprise", "Empresarial") : t("settings.license.editionFree", "Free")}
                {license.tier ? ` · ${license.tier}` : ""}
              </span>
            </div>
            {license.edition === "empresarial" && (license.email || license.expiry) && (
              <div className="mt-2 space-y-1 text-xs text-muted-foreground">
                {license.email && <div className="flex justify-between gap-3"><span>{t("settings.license.licensedTo", "Licencia de")}</span><span className="tabular">{license.email}</span></div>}
                {license.expiry && <div className="flex justify-between gap-3"><span>{t("settings.license.expires", "Caduca")}</span><span className="tabular">{license.expiry}</span></div>}
              </div>
            )}
          </div>

          {license.edition === "empresarial" && license.valid ? (
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="outline" onClick={deactivateLicense} disabled={licenseBusy}>
                {licenseBusy ? <Loader2 className="size-4 animate-spin" /> : <KeyRound className="size-4" />}
                {t("settings.license.deactivateBtn", "Desactivar")}
              </Button>
              <span className="text-xs text-muted-foreground">{t("settings.license.deactivateHint", "Vuelve a la edición Free en este equipo.")}</span>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-xs leading-relaxed text-muted-foreground">
                {t("settings.license.freeDesc", "Estás en la edición")} <span className="font-semibold text-foreground">{t("settings.license.editionFree", "Free")}</span>. {t("settings.license.freeDescMid", "Introduce una clave de activación para desbloquear la edición")}{" "}
                <span className="font-semibold text-foreground">{t("settings.license.editionEnterprise", "Empresarial")}</span> {t("settings.license.freeDescEnd", "(informes, auditoría CIS completa, inteligencia de amenazas y análisis programados).")}
              </p>
              <Label className="mb-2 block text-xs text-muted-foreground">{t("settings.license.keyLabel", "Clave de licencia")}</Label>
              <div className="flex gap-2">
                <Input
                  value={licenseKey}
                  onChange={(e) => setLicenseKey(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") activateLicense(); }}
                  placeholder={t("settings.license.keyPlaceholder", "Pega tu clave de licencia…")}
                  className="tabular"
                  disabled={licenseBusy}
                />
                <Button onClick={activateLicense} disabled={licenseBusy || !licenseKey.trim()}>
                  {licenseBusy ? <Loader2 className="size-4 animate-spin" /> : <KeyRound className="size-4" />}
                  {t("settings.license.activateBtn", "Activar")}
                </Button>
              </div>
            </div>
          )}
        </div>
      </Section>

      <Section icon={Monitor} title={t("settings.interface")}>
        <div className="space-y-4">
          <Toggle id="show-activity-log" label={t("settings.interface.activityLog", "Mostrar panel de actividad (registro de acciones en Optimización y Limpieza)")}
            value={cfg?.ui?.show_activity_log === true} onChange={(v) => patch(["ui", "show_activity_log"], v)} />
          <div>
            <Label className="mb-2 block text-xs text-muted-foreground">{t("settings.interface.colorTheme", "Tema de color")}</Label>
            <div className="flex flex-wrap gap-2">
              {[
                { id: "neon", label: t("settings.interface.palette.neon", "Neón") },
                { id: "nord", label: t("settings.interface.palette.nord", "Nord") },
                { id: "mono", label: t("settings.interface.palette.mono", "Negro") },
                { id: "forest", label: t("settings.interface.palette.forest", "Verde bosque") },
                { id: "gray", label: t("settings.interface.palette.gray", "Gris") },
                { id: "transparent", label: t("settings.interface.palette.transparent", "Cristal") },
              ].map((p) => (
                <Button key={p.id} size="sm"
                  variant={(cfg?.ui?.palette || "neon") === p.id ? "default" : "outline"}
                  onClick={() => {
                    document.documentElement.dataset.palette = p.id;   // live
                    patch(["ui", "palette"], p.id);                     // persist
                    setCfg((c) => ({ ...c, ui: { ...c?.ui, palette: p.id } }));
                  }}>
                  {p.label}
                </Button>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-muted-foreground">{t("settings.interface.paletteHint", "Disponible en ambas ediciones. \"Neón\" es el aspecto liquid-glass por defecto.")}</p>
          </div>
        </div>
      </Section>

      <Section icon={FolderOpen} title={t("settings.logFolder")}>
        <div className="flex gap-2">
          <Input value={logFolder} onChange={(e) => setLogFolder(e.target.value)}
            placeholder={t("settings.logFolder.placeholder", "C:\\Users\\…\\WinSvalinn\\logs")} className="tabular" />
          <Button onClick={() => patch(["logging", "folder"], logFolder)}>{t("settings.logFolder.save", "Guardar")}</Button>
        </div>
      </Section>

      <Section icon={ShieldAlert} title={t("settings.security")}>
        <div className="space-y-3">
          <Toggle id="dry" label={t("settings.security.dryRun", "Modo dry-run por defecto (preview, no aplica cambios)")}
            value={!!cfg?.ui?.dry_run_default} onChange={(v) => patch(["ui", "dry_run_default"], v)} />
          <Toggle id="confirm" label={t("settings.security.confirmDestructive", "Confirmar acciones destructivas")}
            value={cfg?.ui?.confirm_destructive_actions ?? true} onChange={(v) => patch(["ui", "confirm_destructive_actions"], v)} />
          <Toggle id="elevate" label={t("settings.security.autoElevate", "Pedir elevación admin automáticamente al arrancar")}
            value={!!cfg?.ui?.auto_elevate} onChange={(v) => patch(["ui", "auto_elevate"], v)} />
        </div>
      </Section>

      <Section
        icon={KeyRound}
        title={t("settings.integrations")}
        badge={
          vtPro ? <ProBadge /> : (
            <Badge
              variant="outline"
              className="gap-1.5"
              style={{ color: vtConfigured ? SEV_COLOR.ok : "var(--muted-foreground)" }}
            >
              <BadgeCheck className="size-3" />
              {vtConfigured ? t("settings.vt.configured") : t("settings.vt.notConfigured")}
            </Badge>
          )
        }
      >
        <Label className="mb-2 block text-xs text-muted-foreground">{t("settings.vt.label")}</Label>
        <div className="mb-2 flex gap-2">
          <Input type="password" value={vtKey} onChange={(e) => setVtKey(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") saveVtKey(); }}
            placeholder={t("settings.vt.placeholder")} className="tabular" disabled={vtPro || vtBusy}
            autoComplete="off" />
          <Button onClick={saveVtKey} disabled={vtPro || vtBusy || !vtKey.trim()}>
            {vtBusy ? <Loader2 className="size-4 animate-spin" /> : <KeyRound className="size-4" />}
            {t("settings.vt.save")}
          </Button>
          <Button variant="outline" onClick={clearVtKey} disabled={vtPro || vtBusy || !vtConfigured}>
            <Trash2 className="size-4" /> {t("settings.vt.clear")}
          </Button>
        </div>
        <p className="mb-3 text-xs text-muted-foreground">{t("settings.vt.hint")}</p>
        <Toggle id="telemetry" label={t("settings.integrations.telemetry", "Enviar métricas anónimas (opt-in)")}
          value={!!cfg?.telemetry?.opt_in} onChange={(v) => patch(["telemetry", "opt_in"], v)} />
      </Section>

      <ScheduleSection t={t} pro={hasFeature("continuousMonitoring")} />
    </div>
  );
}

/** Scheduled scans: list / create / delete. Pro-gated visually. */
function ScheduleSection({
  t, pro,
}: { t: (k: string, f?: string) => string; pro: boolean }) {
  const [tasks, setTasks] = useState<ScheduleTask[]>([]);
  const [scan, setScan] = useState("security");
  const [frequency, setFrequency] = useState("daily");
  const [time, setTime] = useState("03:00");
  const [busy, setBusy] = useState(false);

  const load = () => {
    api.scheduleList()
      .then((r) => setTasks(r.items ?? []))
      .catch(() => { /* offline: keep empty */ });
  };

  useEffect(() => {
    if (pro) load();
  }, [pro]);

  const create = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await api.scheduleCreate({ scan, frequency, time: time || undefined });
      toast.success(t("settings.schedule.created"));
      load();
    } catch (e: any) {
      const msg = String(e?.message ?? "");
      if (msg.includes("402")) {
        toast.warning(t("options.lockedToast"), { description: t("options.lockedToastAction") });
      } else {
        toast.error(t("settings.schedule.createError"), { description: msg });
      }
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: string) => {
    setBusy(true);
    try {
      await api.scheduleDelete(id);
      toast.success(t("settings.schedule.deleted"));
      setTasks((p) => p.filter((x) => x.id !== id));
    } catch (e: any) {
      toast.error(t("settings.schedule.deleteError"), { description: String(e?.message ?? "") });
    } finally {
      setBusy(false);
    }
  };

  const SCAN_LABEL = (s: string) =>
    s === "optimization" ? t("settings.schedule.scanOptimization") : t("settings.schedule.scanSecurity");

  const body = (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_1fr_auto_auto] sm:items-end">
        <Field label={t("settings.schedule.scan")}>
          <Select value={scan} onChange={setScan} disabled={pro ? false : true}
            options={[
              { v: "security", label: t("settings.schedule.scanSecurity") },
              { v: "optimization", label: t("settings.schedule.scanOptimization") },
            ]} />
        </Field>
        <Field label={t("settings.schedule.frequency")}>
          <Select value={frequency} onChange={setFrequency} disabled={pro ? false : true}
            options={[
              { v: "daily", label: t("settings.schedule.daily") },
              { v: "weekly", label: t("settings.schedule.weekly") },
              { v: "monthly", label: t("settings.schedule.monthly") },
            ]} />
        </Field>
        <Field label={t("settings.schedule.time")}>
          <Input type="time" value={time} onChange={(e) => setTime(e.target.value)}
            className="tabular" disabled={!pro} />
        </Field>
        <Button onClick={create} disabled={!pro || busy}>
          {busy ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
          {t("settings.schedule.add")}
        </Button>
      </div>

      <div className="space-y-2">
        {tasks.length === 0 ? (
          <p className="text-xs text-muted-foreground">{t("settings.schedule.empty")}</p>
        ) : tasks.map((task) => (
          <div key={task.id}
            className="flex items-center justify-between gap-3 rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">{SCAN_LABEL(task.scan)}</span>
              {task.schedule && task.schedule !== "N/A" && (
                <Badge variant="outline" className="text-[10px]">{task.schedule}</Badge>
              )}
              {task.next_run && task.next_run !== "N/A" && (
                <span className="tabular text-xs text-muted-foreground">{task.next_run}</span>
              )}
            </div>
            <Button variant="ghost" size="icon-sm" onClick={() => remove(task.id)} disabled={busy}>
              <Trash2 className="size-4 text-destructive" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <Section icon={CalendarClock} title={t("settings.schedule")} badge={pro ? undefined : <ProBadge />}>
      {pro ? body : (
        <div className="relative">
          <div className="pointer-events-none select-none opacity-45">{body}</div>
          <div className="absolute inset-0 grid place-items-center">
            <p className="max-w-xs rounded-lg bg-card/80 px-3 py-2 text-center text-xs text-muted-foreground backdrop-blur-sm">
              {t("settings.schedule.locked")}
            </p>
          </div>
        </div>
      )}
    </Section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <Label className="mb-2 block text-xs text-muted-foreground">{label}</Label>
      {children}
    </div>
  );
}

function Select({
  value, onChange, options, disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { v: string; label: string }[];
  disabled?: boolean;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-50 dark:bg-input/30"
    >
      {options.map((o) => (
        <option key={o.v} value={o.v}>{o.label}</option>
      ))}
    </select>
  );
}

function Section({
  icon: Icon, title, children, badge,
}: { icon: LucideIcon; title: string; children: React.ReactNode; badge?: React.ReactNode }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between pb-0">
        <CardTitle className="flex items-center gap-2">
          <Icon className="size-4 text-primary" /> {title}
        </CardTitle>
        {badge}
      </CardHeader>
      <CardContent>
        <Separator className="mb-4" />
        {children}
      </CardContent>
    </Card>
  );
}

function Toggle({
  id, label, value, onChange,
}: { id: string; label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <Label htmlFor={id} className="text-sm font-normal">{label}</Label>
      <Switch id={id} checked={value} onCheckedChange={onChange} />
    </div>
  );
}
