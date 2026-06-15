import { useEffect, useMemo, useRef, useState } from "react";
import {
  Home, Shield, Zap, MemoryStick, Trash2, Activity,
  Network, Settings, Search,
  Gamepad2, SlidersHorizontal, EyeOff,
  ShieldCheck, ScanSearch, Radar,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { goToSection, type Section } from "@/lib/nav";
import { useT } from "@/lib/i18n";

// ─── Shared open/close store (so TopBar can trigger it) ─────────────

let open = false;
const listeners = new Set<(v: boolean) => void>();

function setOpen(v: boolean) {
  open = v;
  listeners.forEach((l) => l(open));
}

export const commandPaletteStore = {
  open: () => setOpen(true),
  close: () => setOpen(false),
  toggle: () => setOpen(!open),
  get: () => open,
  subscribe: (fn: (v: boolean) => void) => {
    listeners.add(fn);
    return () => {
      listeners.delete(fn);
    };
  },
};

function useCommandPaletteOpen(): boolean {
  const [v, setV] = useState(open);
  useEffect(() => commandPaletteStore.subscribe(setV), []);
  return v;
}

// ─── Command list ──────────────────────────────────────────────────

interface Command {
  section: Section;
  /** i18n key resolved via t() at render time. */
  labelKey: string;
  icon: React.ComponentType<{ className?: string }>;
}

const COMMANDS: Command[] = [
  { section: "dashboard", labelKey: "nav.dashboard", icon: Home },
  { section: "security", labelKey: "nav.security", icon: Shield },
  { section: "optimization", labelKey: "nav.optimization", icon: Zap },
  { section: "memory", labelKey: "nav.memory", icon: MemoryStick },
  { section: "cleanup", labelKey: "nav.cleanup", icon: Trash2 },
  { section: "processes", labelKey: "nav.processes", icon: Activity },
  { section: "network", labelKey: "nav.network", icon: Network },
  { section: "gaming", labelKey: "nav.gaming", icon: Gamepad2 },
  { section: "tweaks", labelKey: "nav.tweaks", icon: SlidersHorizontal },
  { section: "privacy", labelKey: "nav.privacy", icon: EyeOff },
  { section: "hardening", labelKey: "nav.hardening", icon: ShieldCheck },
  { section: "audit", labelKey: "nav.audit", icon: ScanSearch },
  { section: "threat", labelKey: "nav.threat", icon: Radar },
  { section: "settings", labelKey: "nav.settings", icon: Settings },
];

function normalize(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

// ─── Component ─────────────────────────────────────────────────────

export function CommandPalette() {
  const isOpen = useCommandPaletteOpen();
  const t = useT();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Global Ctrl/Cmd+K toggles the palette.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        commandPaletteStore.toggle();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Reset query/selection each time it opens, focus the input.
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setActive(0);
      // Defer focus until the dialog content is mounted.
      const id = window.setTimeout(() => inputRef.current?.focus(), 0);
      return () => window.clearTimeout(id);
    }
  }, [isOpen]);

  const results = useMemo(() => {
    const q = normalize(query.trim());
    if (!q) return COMMANDS;
    return COMMANDS.filter((c) => normalize(t(c.labelKey)).includes(q));
  }, [query, t]);

  // Keep selection within bounds when the filtered list shrinks.
  useEffect(() => {
    setActive((a) => (a >= results.length ? 0 : a));
  }, [results.length]);

  const select = (s: Section) => {
    commandPaletteStore.close();
    goToSection(s);
  };

  const onInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => (results.length ? (a + 1) % results.length : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) =>
        results.length ? (a - 1 + results.length) % results.length : 0,
      );
    } else if (e.key === "Enter") {
      e.preventDefault();
      const cmd = results[active];
      if (cmd) select(cmd.section);
    }
  };

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(o) => (o ? commandPaletteStore.open() : commandPaletteStore.close())}
    >
      <DialogContent
        showCloseButton={false}
        className="top-[18%] translate-y-0 gap-0 overflow-hidden p-0 sm:max-w-md"
        onOpenAutoFocus={(e) => {
          e.preventDefault();
          inputRef.current?.focus();
        }}
      >
        <DialogTitle className="sr-only">Paleta de comandos</DialogTitle>
        <DialogDescription className="sr-only">
          Busca y navega entre secciones.
        </DialogDescription>

        <div className="flex items-center gap-2 border-b border-border px-3">
          <Search className="size-4 shrink-0 text-muted-foreground" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onInputKeyDown}
            placeholder={t("palette.placeholder")}
            className="h-11 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
        </div>

        <div className="max-h-72 overflow-y-auto p-1.5">
          {results.length === 0 ? (
            <div className="px-3 py-6 text-center text-sm text-muted-foreground">
              {t("palette.empty")}
            </div>
          ) : (
            results.map((cmd, i) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={cmd.section}
                  onClick={() => select(cmd.section)}
                  onMouseMove={() => setActive(i)}
                  className={cn(
                    "flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-sm transition-colors",
                    i === active
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-accent/60",
                  )}
                >
                  <Icon className="size-4 shrink-0" />
                  {t(cmd.labelKey)}
                </button>
              );
            })
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
