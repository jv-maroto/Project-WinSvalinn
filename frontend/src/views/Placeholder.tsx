import { Construction } from "lucide-react";
import { useT } from "../lib/i18n";

export function Placeholder({ section }: { section: string }) {
  const t = useT();
  return (
    <div className="h-full grid place-items-center p-6">
      <div className="glass rounded-2xl p-10 text-center space-y-3">
        <Construction size={48} className="text-muted-foreground mx-auto" />
        <h2 className="font-heading text-xl font-bold">
          '<span className="text-gradient">{section}</span>' {t("placeholder.comingSoon", "próximamente")}
        </h2>
        <p className="text-sm text-muted-foreground max-w-md">
          {t(
            "placeholder.migrating",
            "Vista en migración. Los endpoints del sidecar ya existen — solo falta el componente React.",
          )}
        </p>
      </div>
    </div>
  );
}
