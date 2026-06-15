import { useEffect, useState } from "react";
import { Play, Loader2, AlertTriangle, WifiOff, ListChecks, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ProBadge } from "@/components/ProBadge";
import { api, type OptionMeta } from "@/lib/api";
import { useEdition } from "@/lib/edition";
import { goToSection } from "@/lib/nav";
import { useT } from "@/lib/i18n";

interface Props {
  section: string;
  title: string;
  subtitle?: string;
}

interface LogLine {
  ts: string;
  msg: string;
  level: "info" | "success" | "warning" | "error";
}

type LoadState = "loading" | "ready" | "offline";

export function OptionsSection({ section, title, subtitle }: Props) {
  const t = useT();
  const { edition } = useEdition();
  const isEnterprise = edition === "empresarial";

  const [options, setOptions] = useState<OptionMeta[]>([]);
  const [load, setLoad] = useState<LoadState>("loading");
  const [running, setRunning] = useState<string | null>(null);
  const [showLog, setShowLog] = useState(false);
  const [log, setLog] = useState<LogLine[]>([]);

  const append = (msg: string, level: LogLine["level"] = "info") =>
    setLog((p) => [
      { ts: new Date().toLocaleTimeString(), msg, level },
      ...p.slice(0, 200),
    ]);

  const fetchOptions = () => {
    setLoad("loading");
    api
      .options(section)
      .then((r) => {
        setOptions(r.options ?? []);
        setLoad("ready");
      })
      .catch(() => setLoad("offline"));
  };

  useEffect(() => {
    fetchOptions();
    // Inline activity log is opt-in via ui.show_activity_log.
    api
      .config()
      .then((c) => setShowLog(c?.ui?.show_activity_log === true))
      .catch(() => {
        /* keep hidden by default */
      });
  }, [section]); // eslint-disable-line react-hooks/exhaustive-deps

  const lockedToast = () =>
    toast.warning(t("options.lockedToast"), {
      description: t("options.lockedToastAction"),
      action: {
        label: t("nav.settings"),
        onClick: () => goToSection("settings"),
      },
    });

  const showResultToast = (opt: OptionMeta, r: { ok: boolean; log?: any[] }) => {
    const lines: LogLine[] = Array.isArray(r.log) ? r.log : [];
    lines.forEach((l) => append(l.msg, l.level ?? "info"));
    const summary = lines.length
      ? lines[lines.length - 1].msg
      : opt.label;
    if (r.ok) {
      toast.success(t("options.runOk"), { description: summary });
    } else {
      toast.error(t("options.runFail"), { description: summary });
    }
  };

  const runOption = async (opt: OptionMeta) => {
    const locked = opt.edition === "empresarial" && !isEnterprise;
    if (locked) {
      lockedToast();
      return;
    }
    if (opt.is_destructive && !window.confirm(t("options.confirm"))) return;

    setRunning(opt.id);
    append(`▶ ${opt.label}`);
    try {
      const r = await api.optionRun(opt.id);
      if (r.locked) {
        lockedToast();
        append(t("options.lockedToast"), "warning");
        return;
      }
      showResultToast(opt, r);
    } catch (e: any) {
      const msg = String(e?.message ?? "");
      // 402 -> the option is Enterprise-only and no license is active.
      if (msg.includes("402")) {
        lockedToast();
        append(t("options.lockedToast"), "warning");
      } else {
        toast.error(t("options.runError"), { description: msg });
        append(`${t("options.runError")}: ${msg}`, "error");
      }
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="h-full space-y-5 overflow-y-auto p-6">
      <header>
        <h1 className="font-heading text-2xl font-semibold">{title}</h1>
        {subtitle && (
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        )}
      </header>

      {section === "tweaks" && (
        <div className="glass flex items-start gap-2 rounded-xl p-3 text-sm text-muted-foreground">
          <RotateCcw className="mt-0.5 size-4 shrink-0 text-severity-med" />
          <span>
            Los tweaks de <b>interfaz</b> (Inicio / Taskbar / Explorer) reinician el Explorador de
            Windows al aplicarse — un parpadeo breve. Ese reinicio es justo lo que hace que tengan
            efecto; hasta entonces no se notan.
          </span>
        </div>
      )}

      {load === "loading" && (
        <div className="flex items-center gap-3 py-10 text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> {t("options.loading")}
        </div>
      )}

      {load === "offline" && (
        <div className="glass rounded-2xl p-6">
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <WifiOff className="size-7 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">{t("options.offline")}</p>
            <Button variant="outline" size="sm" onClick={fetchOptions}>
              {t("options.retry")}
            </Button>
          </div>
        </div>
      )}

      {load === "ready" && options.length === 0 && (
        <div className="glass rounded-2xl p-6">
          <div className="grid place-items-center gap-3 py-6 text-center">
            <ListChecks className="size-7 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">{t("options.empty")}</p>
          </div>
        </div>
      )}

      {load === "ready" && options.length > 0 && (
        <TooltipProvider>
          <section className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {options.map((opt) => {
              const locked = opt.edition === "empresarial" && !isEnterprise;
              const isRun = running === opt.id;
              return (
                <div key={opt.id} className="glass rounded-2xl p-4">
                  <div className="flex items-start gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-semibold">{opt.label}</span>
                        {opt.is_destructive && (
                          <Badge variant="destructive" className="gap-1">
                            <AlertTriangle className="size-3" />
                            {t("options.destructive")}
                          </Badge>
                        )}
                        {locked && <ProBadge />}
                      </div>
                      {opt.description && (
                        <p className="mt-1 text-xs text-muted-foreground">
                          {opt.description}
                        </p>
                      )}
                    </div>

                    {locked ? (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          {/* span wrapper: disabled buttons don't fire tooltip/click */}
                          <span tabIndex={0}>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled
                              className="pointer-events-none"
                            >
                              <Play className="size-3.5" />
                              {t("options.run")}
                            </Button>
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>{t("options.lockedTip")}</TooltipContent>
                      </Tooltip>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => runOption(opt)}
                        disabled={!!running}
                      >
                        {isRun ? (
                          <Loader2 className="size-3.5 animate-spin" />
                        ) : (
                          <Play className="size-3.5" />
                        )}
                        {isRun ? t("options.running") : t("options.run")}
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </section>
        </TooltipProvider>
      )}

      {showLog && load === "ready" && (
        <div className="glass rounded-2xl p-6">
          <div className="text-sm font-semibold">{t("options.activity")}</div>
          <div className="tabular mt-3 h-40 overflow-y-auto rounded-lg bg-background p-3 text-xs">
            {log.length === 0 && (
              <div className="text-muted-foreground">
                {t("options.activityEmpty")}
              </div>
            )}
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
  return level === "success"
    ? "var(--severity-ok)"
    : level === "warning"
      ? "var(--severity-med)"
      : level === "error"
        ? "var(--severity-crit)"
        : "var(--muted-foreground)";
}
