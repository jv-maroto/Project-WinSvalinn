import { useEffect, useState } from "react";
import { Sidebar, type Section } from "./components/Sidebar";
import { Titlebar } from "./components/Titlebar";
import { CommandPalette } from "./components/CommandPalette";
import { OptionsSection } from "./components/OptionsSection";
import { Toaster } from "@/components/ui/sonner";
import { initEdition, useEdition } from "./lib/edition";
import { initI18n, useT } from "./lib/i18n";
import { useNav } from "./lib/nav";
import { api } from "./lib/api";
import { Dashboard } from "./views/Dashboard";
import { Optimization } from "./views/Optimization";
import { Memory } from "./views/Memory";
import { Cleanup } from "./views/Cleanup";
import { Processes } from "./views/Processes";
import { Network } from "./views/Network";
import { Gaming } from "./views/Gaming";
import { Settings } from "./views/Settings";
import { Placeholder } from "./views/Placeholder";
import { ProUpsell } from "./views/ProUpsell";

export default function App() {
  const [section, setSection] = useState<Section>("dashboard");
  const [isAdmin, setIsAdmin] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(
    () => localStorage.getItem("wsv.sidebarOpen") !== "0", // default: open
  );
  const nav = useNav();
  const t = useT();
  const { edition } = useEdition();

  const toggleSidebar = () =>
    setSidebarOpen((o) => {
      const next = !o;
      localStorage.setItem("wsv.sidebarOpen", next ? "1" : "0");
      return next;
    });

  useEffect(() => {
    initEdition();
    initI18n();
    // Real elevation status for the title bar (was hardcoded to "user").
    api.systemInfo()
      .then((i) => setIsAdmin(i.is_admin === true))
      .catch(() => setIsAdmin(false));
    // Color theme (neon | nord | mono | forest | gray | transparent), persisted in config.
    // Default "neon": Free shows the neon look, Empresarial falls back to its sober Nord base.
    api.config()
      .then((c) => { document.documentElement.dataset.palette = c?.ui?.palette || "neon"; })
      .catch(() => { document.documentElement.dataset.palette = "neon"; });
  }, []);

  // Visual skin follows the edition: Free → "gamer" (neon), Empresarial → "sober".
  useEffect(() => {
    document.documentElement.dataset.skin = edition === "empresarial" ? "sober" : "gamer";
  }, [edition]);

  const goToSection = (s: Section) => setSection(s);

  // React to navigation requests from the command palette / remediations.
  useEffect(() => {
    goToSection(nav.section);
  }, [nav.nonce]); // eslint-disable-line react-hooks/exhaustive-deps

  const renderView = () => {
    switch (section) {
      case "dashboard":    return <Dashboard />;
      case "optimization": return <Optimization />;
      case "memory":       return <Memory />;
      case "cleanup":      return <Cleanup />;
      case "processes":    return <Processes />;
      case "network":      return <Network />;
      case "gaming":
        return <Gaming />;
      case "tweaks":
        return <OptionsSection section="tweaks" title={t("nav.tweaks")} subtitle={t("subtitle.tweaks")} />;
      case "privacy":
        return <OptionsSection section="privacy" title={t("nav.privacy")} subtitle={t("subtitle.privacy")} />;
      case "security":
      case "hardening":
      case "audit":
      case "threat":
        return <ProUpsell section={t(`nav.${section}`)} />;
      case "settings":     return <Settings />;
      default:             return <Placeholder section={section} />;
    }
  };

  return (
    <div className="relative flex h-screen flex-col overflow-hidden">
      <div className="app-bg" aria-hidden="true" />
      <Titlebar isAdmin={isAdmin} onToggleSidebar={toggleSidebar} sidebarOpen={sidebarOpen} />
      <div className="relative z-10 flex min-h-0 flex-1">
        <div
          className={
            "min-h-0 shrink-0 overflow-hidden transition-[width,opacity] duration-300 ease-out " +
            (sidebarOpen ? "w-[220px] opacity-100" : "pointer-events-none w-0 opacity-0")
          }
        >
          <div
            className={
              "h-full transition-transform duration-300 ease-out " +
              (sidebarOpen ? "translate-x-0" : "-translate-x-full")
            }
          >
            <Sidebar active={section} onChange={goToSection} />
          </div>
        </div>
        <main className="relative min-h-0 min-w-0 flex-1">
          <div key={section} className="h-full animate-in fade-in duration-150">
            {renderView()}
          </div>
        </main>
      </div>
      <CommandPalette />
      <Toaster />
    </div>
  );
}
