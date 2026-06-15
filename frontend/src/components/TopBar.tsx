import { ShieldCheck, ShieldX, Search } from "lucide-react";
import { commandPaletteStore } from "@/components/CommandPalette";
import { useT } from "@/lib/i18n";

interface Props {
  title: string;
  isAdmin: boolean;
}

export function TopBar({ title, isAdmin }: Props) {
  const t = useT();
  return (
    <header className="h-14 flex items-center px-6 border-b border-[var(--color-border)] bg-[var(--color-bg-card)]">
      <h1 className="text-base font-semibold">{title}</h1>

      <button
        type="button"
        onClick={() => commandPaletteStore.open()}
        aria-label={t("topbar.searchAria")}
        className="ml-6 flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text-dim)] text-xs w-72 transition-colors hover:text-[var(--color-text)] hover:border-[var(--color-border-strong,var(--color-border))] focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
      >
        <Search size={14} />
        <span>{t("topbar.search")}</span>
        <kbd className="ml-auto rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-1.5 py-0.5 text-[10px] font-medium tracking-wide">
          Ctrl+K
        </kbd>
      </button>

      <div className="ml-auto flex items-center gap-3">
        <div className={`chip ${isAdmin ? "success" : "danger"}`}>
          {isAdmin ? <ShieldCheck size={12} /> : <ShieldX size={12} />}
          {isAdmin ? t("topbar.admin") : t("topbar.user")}
        </div>
      </div>
    </header>
  );
}
