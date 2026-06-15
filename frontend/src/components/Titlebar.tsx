import {
  Search, Minus, Square, X, ShieldCheck, ShieldX, PanelLeft, PanelLeftClose,
} from "lucide-react";
import { commandPaletteStore } from "@/components/CommandPalette";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";

/**
 * Custom glass window title bar (the window runs `decorations: false`).
 * Tauri window calls are loaded lazily + guarded so the bar can never crash
 * the app (e.g. in plain browser dev). Provides drag region, search trigger,
 * admin chip and minimize / maximize / close controls.
 */
async function winCall(method: "minimize" | "toggleMaximize" | "close") {
  try {
    const { getCurrentWindow } = await import("@tauri-apps/api/window");
    await getCurrentWindow()[method]();
  } catch {
    /* not running inside Tauri */
  }
}

interface TitlebarProps {
  isAdmin: boolean;
  onToggleSidebar: () => void;
  sidebarOpen: boolean;
}

export function Titlebar({ isAdmin, onToggleSidebar, sidebarOpen }: TitlebarProps) {
  const t = useT();
  return (
    <header
      data-tauri-drag-region
      className="glass z-20 flex h-11 shrink-0 items-center gap-3 px-3"
    >
      <button
        type="button"
        onClick={onToggleSidebar}
        aria-label={sidebarOpen ? t("titlebar.hideMenu", "Ocultar menú") : t("titlebar.showMenu", "Mostrar menú")}
        title={sidebarOpen ? t("titlebar.hideMenu", "Ocultar menú") : t("titlebar.showMenu", "Mostrar menú")}
        className="grid size-7 shrink-0 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-white/10 hover:text-foreground"
      >
        {sidebarOpen ? <PanelLeftClose className="size-4" /> : <PanelLeft className="size-4" />}
      </button>

      <div data-tauri-drag-region className="flex items-center gap-2 pl-1">
        <img src="/logo.png" alt="WinSvalinn" className="size-6 shrink-0" />
        <span className="font-heading text-sm font-semibold tracking-tight">WinSvalinn</span>
      </div>

      <button
        type="button"
        onClick={() => commandPaletteStore.open()}
        aria-label={t("topbar.search", "Buscar")}
        className="ml-3 flex h-7 max-w-80 flex-1 items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 text-xs text-muted-foreground transition-colors hover:border-white/20 hover:text-foreground"
      >
        <Search className="size-3.5 shrink-0" />
        <span className="truncate">{t("titlebar.searchPlaceholder", "Buscar…")}</span>
        <kbd className="ml-auto rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px]">Ctrl+K</kbd>
      </button>

      <div className="ml-auto flex items-center gap-2">
        <div className={cn("chip", isAdmin ? "success" : "danger")}>
          {isAdmin ? <ShieldCheck size={12} /> : <ShieldX size={12} />}
          {isAdmin ? t("topbar.admin", "Administrador") : t("topbar.user", "Usuario")}
        </div>

        <div className="flex items-center gap-0.5">
          <WinBtn onClick={() => winCall("minimize")} label={t("titlebar.minimize", "Minimizar")}>
            <Minus className="size-3.5" />
          </WinBtn>
          <WinBtn onClick={() => winCall("toggleMaximize")} label={t("titlebar.maximize", "Maximizar")}>
            <Square className="size-3" />
          </WinBtn>
          <WinBtn onClick={() => winCall("close")} label={t("titlebar.close", "Cerrar")} danger>
            <X className="size-3.5" />
          </WinBtn>
        </div>
      </div>
    </header>
  );
}

function WinBtn({
  onClick, label, danger, children,
}: { onClick: () => void; label: string; danger?: boolean; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className={cn(
        "grid size-7 place-items-center rounded-md text-muted-foreground transition-colors",
        danger ? "hover:bg-destructive hover:text-white" : "hover:bg-white/10 hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}
