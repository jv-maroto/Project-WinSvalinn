import { Lock, Building2 } from "lucide-react";
import { useT } from "../lib/i18n";

export function ProUpsell({ section }: { section: string }) {
  const t = useT();
  return (
    <div className="h-full grid place-items-center p-6">
      <div className="glass max-w-md rounded-2xl p-10 text-center space-y-4">
        <div className="relative mx-auto w-fit">
          <Building2 size={48} className="text-[var(--accent-from)] mx-auto" />
          <Lock size={20} className="absolute -bottom-1 -right-1 text-muted-foreground" />
        </div>
        <h2 className="font-heading text-xl font-bold">
          <span className="text-gradient capitalize">{section}</span>
        </h2>
        <p className="text-sm text-muted-foreground">
          {t(
            "upsell.proFeature",
            "Esta función forma parte de la edición Empresarial: hardening guiado, auditoría CIS completa, inteligencia de amenazas e informes.",
          )}
        </p>
        <a
          href="https://github.com/jv-maroto/Project-WinSvalinn"
          target="_blank"
          rel="noreferrer"
          className="inline-block rounded-xl bg-accent-gradient px-4 py-2 text-sm font-semibold text-[#05080d]"
        >
          {t("upsell.learnMore", "Conocer Empresarial")}
        </a>
      </div>
    </div>
  );
}
