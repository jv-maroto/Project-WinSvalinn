import { useEffect, useState } from "react";
import {
  Gamepad2, Play, Loader2, RefreshCw, ShieldAlert, Sparkles, Lightbulb, CheckCircle2,
  HelpCircle, ChevronRight, ArrowLeft, ShieldCheck, AlertTriangle, Settings2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { api, type DetectedGame, type GameAction, type GameActionResult } from "@/lib/api";
import { useT } from "@/lib/i18n";

/** A "?" that explains why anti-cheat game settings must be applied by hand. */
function WhyManual() {
  const t = useT();
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          aria-label={t("gaming.whyManual.ariaLabel", "Por qué hay que hacerlo a mano")}
          className="inline-flex items-center text-muted-foreground transition-colors hover:text-foreground"
        >
          <HelpCircle className="size-3.5" />
        </button>
      </TooltipTrigger>
      <TooltipContent className="max-w-sm text-left leading-relaxed">
        {t(
          "gaming.whyManual.tooltip",
          "Los juegos con anticheat (Vanguard, Easy Anti-Cheat, BattlEye, VAC) vigilan y firman sus propios archivos de configuración. Si una app externa los edita, el anticheat puede tomarlo como trampa y darte un aviso o un baneo. Por eso WinSvalinn solo automatiza ajustes de Windows (preferencia de GPU, Fullscreen Optimizations, Game Mode) — que el anticheat no toca — y los ajustes internos del juego los aplicas tú dentro del propio juego, que sí es seguro.",
        )}
      </TooltipContent>
    </Tooltip>
  );
}

/** One optimization action: label + badges + apply button + result log. */
function ActionRow({
  action,
  isAdmin,
  running,
  result,
  onRun,
}: {
  action: GameAction;
  isAdmin: boolean;
  running: boolean;
  result?: GameActionResult;
  onRun: () => void;
}) {
  const t = useT();
  const adminBlocked = action.needs_admin && !isAdmin;
  const done = action.applied === true;
  return (
    <div className="glass rounded-2xl p-4">
      <div className="flex items-center gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold">{action.label}</span>
            {done && (
              <span className="inline-flex items-center gap-1 rounded-full bg-severity-ok/15 px-2 py-0.5 text-[10px] font-semibold text-severity-ok">
                <CheckCircle2 className="size-3" /> {t("gaming.badge.alreadyApplied", "Ya aplicado")}
              </span>
            )}
            {action.needs_admin && (
              <span
                className={
                  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold " +
                  (adminBlocked
                    ? "bg-severity-crit/15 text-severity-crit"
                    : "bg-severity-med/15 text-severity-med")
                }
              >
                <ShieldCheck className="size-3" /> Admin
              </span>
            )}
            {action.destructive && (
              <span className="inline-flex items-center gap-1 rounded-full bg-severity-med/15 px-2 py-0.5 text-[10px] font-semibold text-severity-med">
                <AlertTriangle className="size-3" /> {t("gaming.badge.caution", "Cuidado")}
              </span>
            )}
          </div>
          {adminBlocked && (
            <div className="mt-0.5 text-xs text-severity-crit">
              {t("gaming.adminBlocked", "Reinicia la app como Administrador para aplicarla.")}
            </div>
          )}
        </div>
        <Button variant={done ? "ghost" : "outline"} size="sm" onClick={onRun} disabled={running}>
          {running ? <Loader2 className="size-3.5 animate-spin" /> : <Play className="size-3.5" />}
          {done ? t("gaming.btn.reapply", "Reaplicar") : t("gaming.btn.apply", "Aplicar")}
        </Button>
      </div>
      {result && (
        <div className="mt-3 space-y-1 border-t border-border pt-3 text-xs">
          <div
            className={"flex items-center gap-1.5 " + (result.ok ? "text-severity-ok" : "text-severity-med")}
          >
            <CheckCircle2 className="size-3.5" />
            {result.ok ? t("gaming.result.applied", "Aplicado") : t("gaming.result.noChanges", "Sin cambios")} ({result.applied})
          </div>
          {result.log.slice(0, 6).map((l, i) => (
            <div key={i} className="text-muted-foreground">
              · {l.msg}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function Gaming() {
  const t = useT();
  const [games, setGames] = useState<DetectedGame[]>([]);
  const [globalActions, setGlobalActions] = useState<GameAction[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState<DetectedGame | null>(null);
  const [gRunning, setGRunning] = useState<string | null>(null);
  const [gResults, setGResults] = useState<Record<string, GameActionResult>>({});
  const [pickerOpen, setPickerOpen] = useState(false);

  const scan = async () => {
    setLoading(true);
    setError(false);
    try {
      const r = await api.games();
      setGames(r.games);
      setGlobalActions(r.global_actions ?? []);
      setIsAdmin(r.is_admin);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    scan();
  }, []);

  const runGlobal = async (actionId: string) => {
    setGRunning(actionId);
    try {
      const r = await api.gameGlobal(actionId);
      setGResults((p) => ({ ...p, [actionId]: r }));
    } catch {
      /* sidecar offline */
    } finally {
      setGRunning(null);
    }
  };

  // Step 2 — the chosen game's optimization menu.
  if (selected) {
    return <GameDetail game={selected} isAdmin={isAdmin} onBack={() => setSelected(null)} />;
  }

  // Step 1 — global tweaks + pick a game.
  return (
    <TooltipProvider delayDuration={150}>
      <div className="h-full space-y-5 overflow-y-auto p-6">
        <header className="flex items-start justify-between gap-4">
          <div>
            <h1 className="font-heading text-2xl font-semibold">
              <span className="text-gradient">{t("nav.gaming", "Juegos")}</span>
            </h1>
            <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
              {t("gaming.subtitle", "Optimizaciones globales del PC y mejoras específicas por juego.")}
              <WhyManual />
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={scan} disabled={loading}>
            {loading ? <Loader2 className="size-3.5 animate-spin" /> : <RefreshCw className="size-3.5" />}
            {t("gaming.btn.rescan", "Reescanear")}
          </Button>
        </header>

        {!isAdmin && (
          <div className="glass flex items-center gap-3 rounded-xl p-3 text-sm">
            <ShieldAlert className="size-4 shrink-0 text-severity-med" />
            <span className="text-muted-foreground">
              {t(
                "gaming.notAdmin",
                "No estás como Administrador. Algunas optimizaciones (prioridad, red, plan de energía) lo necesitan; se marcan con ",
              )}<b>Admin</b>{t("gaming.notAdmin.suffix", ".")}
            </span>
          </div>
        )}

        {error && (
          <div className="glass rounded-xl p-4 text-sm text-muted-foreground">
            {t("gaming.error.sidecar", "No se pudo contactar con el servicio. ¿Está el sidecar en marcha?")}
          </div>
        )}

        {/* ── Global tweaks (no game needed) ── */}
        {globalActions.length > 0 && (
          <section className="space-y-3">
            <div className="flex items-center gap-2">
              <Settings2 className="size-4 text-primary" />
              <h2 className="text-sm font-semibold">{t("gaming.globalSection.title", "Ajustes globales del sistema")}</h2>
              <span className="text-xs text-muted-foreground">{t("gaming.globalSection.subtitle", "— se aplican a todo el PC, sin elegir juego")}</span>
            </div>
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              {globalActions.map((a) => (
                <ActionRow
                  key={a.id}
                  action={a}
                  isAdmin={isAdmin}
                  running={gRunning === a.id}
                  result={gResults[a.id]}
                  onRun={() => runGlobal(a.id)}
                />
              ))}
            </div>
          </section>
        )}

        {/* ── Per-game (pick from a modal) ── */}
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <Gamepad2 className="size-4 text-primary" />
            <h2 className="text-sm font-semibold">{t("gaming.perGameSection.title", "Optimización por juego")}</h2>
            <span className="text-xs text-muted-foreground">{t("gaming.perGameSection.subtitle", "— elige un juego para sus ajustes específicos")}</span>
          </div>

          <div className="glass flex items-center justify-between gap-3 rounded-2xl p-4">
            <div className="text-sm text-muted-foreground">
              {loading
                ? t("gaming.scanning", "Buscando juegos instalados…")
                : `${games.length} ${games.length === 1 ? t("gaming.gameCount.one", "juego detectado") : t("gaming.gameCount.many", "juegos detectados")}`}
            </div>
            <Dialog open={pickerOpen} onOpenChange={setPickerOpen}>
              <DialogTrigger asChild>
                <Button size="sm" disabled={loading || games.length === 0}>
                  <Gamepad2 className="size-4" /> {t("gaming.btn.pickGame", "Elegir juego")}
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle>{t("gaming.picker.title", "Elige un juego")}</DialogTitle>
                  <DialogDescription>
                    {t("gaming.picker.description", "Selecciona un juego instalado para ver y aplicar sus optimizaciones.")}
                  </DialogDescription>
                </DialogHeader>
                <div className="max-h-[60vh] space-y-2 overflow-y-auto pr-1">
                  {games.map((g) => (
                    <button
                      key={g.id}
                      onClick={() => {
                        setSelected(g);
                        setPickerOpen(false);
                      }}
                      className="glass flex w-full items-center gap-3 rounded-xl p-3 text-left transition-colors hover:border-primary/40"
                    >
                      <div className="grid size-9 place-items-center rounded-lg bg-primary/10 text-primary">
                        <Gamepad2 className="size-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-sm font-semibold">{g.name}</span>
                          {g.curated && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-semibold text-primary">
                              <Sparkles className="size-3" /> {t("gaming.badge.curated", "Curado")}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {g.source}
                          {g.anticheat ? ` · anticheat: ${g.anticheat}` : ""}
                        </div>
                      </div>
                      <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
                    </button>
                  ))}
                  {games.length === 0 && (
                    <div className="text-sm text-muted-foreground">{t("gaming.picker.empty", "No se detectaron juegos.")}</div>
                  )}
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </section>
      </div>
    </TooltipProvider>
  );
}

function GameDetail({
  game,
  isAdmin,
  onBack,
}: {
  game: DetectedGame;
  isAdmin: boolean;
  onBack: () => void;
}) {
  const t = useT();
  const [running, setRunning] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, GameActionResult>>({});

  const run = async (actionId: string) => {
    setRunning(actionId);
    try {
      const r = await api.gameAction(game.id, actionId);
      setResults((p) => ({ ...p, [actionId]: r }));
    } catch {
      /* sidecar offline */
    } finally {
      setRunning(null);
    }
  };

  return (
    <TooltipProvider delayDuration={150}>
      <div className="h-full space-y-5 overflow-y-auto p-6">
        <header className="space-y-2">
          <Button variant="ghost" size="sm" onClick={onBack} className="-ml-2 gap-1">
            <ArrowLeft className="size-4" /> {t("gaming.btn.back", "Volver")}
          </Button>
          <div className="flex items-center gap-2">
            <h1 className="font-heading text-2xl font-semibold">{game.name}</h1>
            {game.curated && (
              <span className="inline-flex items-center gap-1 rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-semibold text-primary">
                <Sparkles className="size-3" /> {t("gaming.badge.curated", "Curado")}
              </span>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            {game.source}
            {game.anticheat ? ` · anticheat: ${game.anticheat}` : ""}
          </p>
        </header>

        {game.anticheat && (
          <div className="glass flex items-start gap-2 rounded-xl p-3 text-sm text-severity-med">
            <ShieldAlert className="mt-0.5 size-4 shrink-0" />
            <span className="inline-flex flex-wrap items-center gap-1">
              <b>{game.anticheat}</b>: {t("gaming.anticheat.warning", "no tocamos sus ficheros (riesgo de baneo). Aplica los ajustes recomendados de abajo a mano dentro del juego.")} <WhyManual />
            </span>
          </div>
        )}

        {(game.tips?.length ?? 0) > 0 && (
          <section className="glass rounded-2xl p-4">
            <div className="mb-2 text-sm font-semibold">{t("gaming.tips.title", "Ajustes recomendados (manuales)")}</div>
            <ul className="space-y-1">
              {game.tips!.map((tip, i) => (
                <li key={i} className="flex items-start gap-1.5 text-sm text-muted-foreground">
                  <Lightbulb className="mt-0.5 size-3.5 shrink-0 text-primary" />
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section className="space-y-3">
          <div className="text-sm font-semibold">{t("gaming.autoSection.title", "Optimizaciones de este juego (automáticas)")}</div>
          {(game.actions ?? []).map((a) => (
            <ActionRow
              key={a.id}
              action={a}
              isAdmin={isAdmin}
              running={running === a.id}
              result={results[a.id]}
              onRun={() => run(a.id)}
            />
          ))}
        </section>
      </div>
    </TooltipProvider>
  );
}
