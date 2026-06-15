/**
 * Lightweight i18n (es/en) with a live language switch.
 *
 * Same pub/sub store pattern as src/lib/cache.ts / src/lib/edition.ts:
 *   - read synchronously (`getLang`, `t`)
 *   - subscribe reactively (`useLang`, `useT`)
 *
 * The language is resolved from the sidecar config at startup
 * (`initI18n` -> ui.language, default "es"). `setLang(l)` updates the store
 * LIVE (no restart) and persists it via `api.configPatch(["ui","language"], l)`.
 *
 * Only keys present in the dictionary are translated; everything else falls
 * back to the provided `fallback` (or the key). Untranslated views keep their
 * hardcoded Spanish strings and are NOT broken by this system.
 */

import { useEffect, useState } from "react";
import { api } from "./api";

export type Lang = "es" | "en";

// ─── Dictionary ────────────────────────────────────────────────────

type Dict = Record<string, string>;

const ES: Dict = {
  // Sidebar group titles
  "group.audit": "Auditoría",
  "group.system": "Sistema",
  "group.tuning": "Personalización",
  "group.enterprise": "Empresarial",
  "group.general": "General",

  // Navigation / section titles
  "nav.dashboard": "Inicio",
  "nav.security": "Seguridad",
  "nav.optimization": "Optimizar",
  "nav.memory": "Memoria",
  "nav.cleanup": "Limpieza",
  "nav.processes": "Procesos",
  "nav.network": "Red",
  "nav.gaming": "Juegos",
  "nav.tweaks": "Personalización",
  "nav.privacy": "Privacidad",
  "nav.hardening": "Blindaje",
  "nav.audit": "Auditoría",
  "nav.threat": "Amenazas",
  "nav.settings": "Ajustes",

  // Full section titles (TopBar)
  "title.dashboard": "Inicio",
  "title.security": "Seguridad",
  "title.optimization": "Optimización",
  "title.memory": "Memoria",
  "title.cleanup": "Limpieza de disco",
  "title.processes": "Procesos",
  "title.network": "Red",
  "title.gaming": "Juegos",
  "title.tweaks": "Personalización",
  "title.privacy": "Privacidad",
  "title.hardening": "Blindaje",
  "title.audit": "Auditoría avanzada",
  "title.threat": "Inteligencia de amenazas",
  "title.settings": "Ajustes",

  // Section subtitles (OptionsSection)
  "subtitle.gaming": "Modo juego, latencia y rendimiento para gaming.",
  "subtitle.tweaks": "Ajustes finos del sistema y la interfaz de Windows.",
  "subtitle.privacy": "Telemetría, anuncios y recopilación de datos de Windows.",
  "subtitle.hardening": "Blindaje del sistema según buenas prácticas de seguridad.",
  "subtitle.audit": "Auditoría CIS completa y comprobaciones de cumplimiento.",
  "subtitle.threat": "Inteligencia de amenazas y comprobaciones de seguridad avanzadas.",

  // TopBar
  "topbar.admin": "Administrador",
  "topbar.user": "Usuario",
  "topbar.search": "Buscar",
  "topbar.searchAria": "Abrir paleta de comandos",

  // Command palette
  "palette.placeholder": "Ir a una sección…",
  "palette.empty": "Sin resultados",

  // OptionsSection
  "options.run": "Ejecutar",
  "options.running": "Ejecutando…",
  "options.empty": "No hay opciones disponibles en esta sección.",
  "options.loading": "Cargando opciones…",
  "options.offline": "No se pudo conectar con el servicio. ¿Está el sidecar en marcha?",
  "options.destructive": "Destructivo",
  "options.locked": "Empresarial",
  "options.lockedTip": "Disponible en Empresarial",
  "options.lockedToast": "Esta opción requiere la edición Empresarial.",
  "options.lockedToastAction": "Actívala en Ajustes › Licencia.",
  "options.confirm": "Esta acción es destructiva. ¿Quieres continuar?",
  "options.runOk": "Acción completada",
  "options.runFail": "La acción falló",
  "options.runError": "No se pudo ejecutar la acción",
  "options.activity": "Actividad",
  "options.activityEmpty": "Pulsa una opción para ver el registro.",
  "options.retry": "Reintentar",

  // Settings
  "settings.title": "Configuración",
  "settings.subtitle": "Ajustes globales. Los cambios se aplican al instante.",
  "settings.language": "Idioma",
  "settings.license": "Licencia / Edición",
  "settings.theme": "Tema",
  "settings.interface": "Interfaz",
  "settings.logFolder": "Carpeta de logs",
  "settings.security": "Seguridad y reversibilidad",
  "settings.integrations": "Integraciones",
  "settings.saved": "Guardado",

  // Settings · VirusTotal (DPAPI-stored key)
  "settings.vt.label": "Clave de API de VirusTotal",
  "settings.vt.placeholder": "Pega tu clave de API de VirusTotal…",
  "settings.vt.save": "Guardar",
  "settings.vt.clear": "Limpiar",
  "settings.vt.configured": "Configurada",
  "settings.vt.notConfigured": "Sin configurar",
  "settings.vt.hint": "La clave se cifra con DPAPI y nunca sale de este equipo.",
  "settings.vt.saved": "Clave de VirusTotal guardada",
  "settings.vt.cleared": "Clave de VirusTotal eliminada",
  "settings.vt.saveError": "No se pudo guardar la clave",
  "settings.vt.clearError": "No se pudo eliminar la clave",

  // Settings · Scheduled scans
  "settings.schedule": "Monitor de seguridad",
  "settings.schedule.scan": "Análisis",
  "settings.schedule.frequency": "Frecuencia",
  "settings.schedule.time": "Hora",
  "settings.schedule.add": "Programar",
  "settings.schedule.empty": "No hay análisis programados.",
  "settings.schedule.daily": "Diario",
  "settings.schedule.weekly": "Semanal",
  "settings.schedule.monthly": "Mensual",
  "settings.schedule.scanSecurity": "Seguridad",
  "settings.schedule.scanOptimization": "Optimización",
  "settings.schedule.created": "Análisis programado",
  "settings.schedule.createError": "No se pudo programar el análisis",
  "settings.schedule.deleted": "Programación eliminada",
  "settings.schedule.deleteError": "No se pudo eliminar la programación",
  "settings.schedule.locked": "Programa análisis automáticos con la edición Empresarial.",

  // Security · report export
  "security.report.generating": "Generando informe…",
  "security.report.opened": "Informe abierto en una pestaña nueva.",
  "security.report.error": "No se pudo generar el informe",
  "security.report.locked": "Exportar informes requiere la edición Empresarial.",
  "security.report.lockedAction": "Actívala en Ajustes › Licencia.",
  "security.cis": "CIS",

  // Threat intelligence view
  "threat.title": "Inteligencia de amenazas",
  "threat.subtitle": "Inteligencia de amenazas y comprobaciones de seguridad avanzadas.",
  "threat.vt.title": "Búsqueda en VirusTotal",
  "threat.vt.hashLabel": "Hash SHA-256",
  "threat.vt.hashPlaceholder": "Introduce un hash SHA-256…",
  "threat.vt.lookup": "Consultar",
  "threat.vt.fileLabel": "Ruta del fichero",
  "threat.vt.filePlaceholder": "C:\\ruta\\al\\fichero.exe",
  "threat.vt.analyze": "Analizar",
  "threat.vt.malicious": "Malicioso",
  "threat.vt.clean": "Limpio",
  "threat.vt.suspicious": "Sospechoso",
  "threat.vt.notFound": "No encontrado en VirusTotal",
  "threat.vt.detections": "detecciones",
  "threat.vt.openLink": "Ver en VirusTotal",
  "threat.vt.error": "Error en la consulta",
  "threat.vt.needKey": "Configura tu clave de VirusTotal en Ajustes › Integraciones.",
  "threat.vt.locked": "El panel de VirusTotal requiere la edición Empresarial.",
  "threat.vt.lockedCta": "Activar en Ajustes",
  "threat.vt.empty": "Introduce un hash o una ruta para consultar VirusTotal.",
};

const EN: Dict = {
  // Sidebar group titles
  "group.audit": "Audit",
  "group.system": "System",
  "group.tuning": "Tuning",
  "group.enterprise": "Enterprise",
  "group.general": "General",

  // Navigation / section titles
  "nav.dashboard": "Home",
  "nav.security": "Security",
  "nav.optimization": "Optimize",
  "nav.memory": "Memory",
  "nav.cleanup": "Cleanup",
  "nav.processes": "Processes",
  "nav.network": "Network",
  "nav.gaming": "Gaming",
  "nav.tweaks": "Tweaks",
  "nav.privacy": "Privacy",
  "nav.hardening": "Hardening",
  "nav.audit": "Audit",
  "nav.threat": "Threats",
  "nav.settings": "Settings",

  // Full section titles (TopBar)
  "title.dashboard": "Home",
  "title.security": "Security",
  "title.optimization": "Optimization",
  "title.memory": "Memory",
  "title.cleanup": "Disk cleanup",
  "title.processes": "Processes",
  "title.network": "Network",
  "title.gaming": "Gaming",
  "title.tweaks": "Tweaks",
  "title.privacy": "Privacy",
  "title.hardening": "Hardening",
  "title.audit": "Advanced audit",
  "title.threat": "Threat intelligence",
  "title.settings": "Settings",

  // Section subtitles (OptionsSection)
  "subtitle.gaming": "Game mode, latency and performance tuning for gaming.",
  "subtitle.tweaks": "Fine-grained Windows system and interface tweaks.",
  "subtitle.privacy": "Windows telemetry, ads and data collection.",
  "subtitle.hardening": "System hardening following security best practices.",
  "subtitle.audit": "Full CIS audit and compliance checks.",
  "subtitle.threat": "Threat intelligence and advanced security checks.",

  // TopBar
  "topbar.admin": "Administrator",
  "topbar.user": "User",
  "topbar.search": "Search",
  "topbar.searchAria": "Open command palette",

  // Command palette
  "palette.placeholder": "Go to a section…",
  "palette.empty": "No results",

  // OptionsSection
  "options.run": "Run",
  "options.running": "Running…",
  "options.empty": "No options available in this section.",
  "options.loading": "Loading options…",
  "options.offline": "Could not reach the service. Is the sidecar running?",
  "options.destructive": "Destructive",
  "options.locked": "Enterprise",
  "options.lockedTip": "Available in Enterprise",
  "options.lockedToast": "This option requires the Enterprise edition.",
  "options.lockedToastAction": "Activate it in Settings › License.",
  "options.confirm": "This action is destructive. Do you want to continue?",
  "options.runOk": "Action completed",
  "options.runFail": "The action failed",
  "options.runError": "Could not run the action",
  "options.activity": "Activity",
  "options.activityEmpty": "Run an option to see the log.",
  "options.retry": "Retry",

  // Settings
  "settings.title": "Settings",
  "settings.subtitle": "Global settings. Changes apply instantly.",
  "settings.language": "Language",
  "settings.license": "License / Edition",
  "settings.theme": "Theme",
  "settings.interface": "Interface",
  "settings.logFolder": "Logs folder",
  "settings.security": "Safety & reversibility",
  "settings.integrations": "Integrations",
  "settings.saved": "Saved",

  // Settings · VirusTotal (DPAPI-stored key)
  "settings.vt.label": "VirusTotal API key",
  "settings.vt.placeholder": "Paste your VirusTotal API key…",
  "settings.vt.save": "Save",
  "settings.vt.clear": "Clear",
  "settings.vt.configured": "Configured",
  "settings.vt.notConfigured": "Not configured",
  "settings.vt.hint": "The key is encrypted with DPAPI and never leaves this machine.",
  "settings.vt.saved": "VirusTotal key saved",
  "settings.vt.cleared": "VirusTotal key removed",
  "settings.vt.saveError": "Could not save the key",
  "settings.vt.clearError": "Could not remove the key",

  // Settings · Scheduled scans
  "settings.schedule": "Security monitor",
  "settings.schedule.scan": "Scan",
  "settings.schedule.frequency": "Frequency",
  "settings.schedule.time": "Time",
  "settings.schedule.add": "Schedule",
  "settings.schedule.empty": "No scheduled scans.",
  "settings.schedule.daily": "Daily",
  "settings.schedule.weekly": "Weekly",
  "settings.schedule.monthly": "Monthly",
  "settings.schedule.scanSecurity": "Security",
  "settings.schedule.scanOptimization": "Optimization",
  "settings.schedule.created": "Scan scheduled",
  "settings.schedule.createError": "Could not schedule the scan",
  "settings.schedule.deleted": "Schedule removed",
  "settings.schedule.deleteError": "Could not remove the schedule",
  "settings.schedule.locked": "Schedule automatic scans with the Enterprise edition.",

  // Security · report export
  "security.report.generating": "Generating report…",
  "security.report.opened": "Report opened in a new tab.",
  "security.report.error": "Could not generate the report",
  "security.report.locked": "Exporting reports requires the Enterprise edition.",
  "security.report.lockedAction": "Activate it in Settings › License.",
  "security.cis": "CIS",

  // Threat intelligence view
  "threat.title": "Threat intelligence",
  "threat.subtitle": "Threat intelligence and advanced security checks.",
  "threat.vt.title": "VirusTotal lookup",
  "threat.vt.hashLabel": "SHA-256 hash",
  "threat.vt.hashPlaceholder": "Enter a SHA-256 hash…",
  "threat.vt.lookup": "Look up",
  "threat.vt.fileLabel": "File path",
  "threat.vt.filePlaceholder": "C:\\path\\to\\file.exe",
  "threat.vt.analyze": "Analyze",
  "threat.vt.malicious": "Malicious",
  "threat.vt.clean": "Clean",
  "threat.vt.suspicious": "Suspicious",
  "threat.vt.notFound": "Not found on VirusTotal",
  "threat.vt.detections": "detections",
  "threat.vt.openLink": "View on VirusTotal",
  "threat.vt.error": "Lookup error",
  "threat.vt.needKey": "Configure your VirusTotal key in Settings › Integrations.",
  "threat.vt.locked": "The VirusTotal panel requires the Enterprise edition.",
  "threat.vt.lockedCta": "Activate in Settings",
  "threat.vt.empty": "Enter a hash or a path to query VirusTotal.",

  // ─── Dashboard view ──────────────────────────────────────────────
  "dashboard.controlCenterPre": "Control ",
  "dashboard.controlCenterHighlight": "center",
  "dashboard.subtitle": "Health, security and performance in real time.",
  "dashboard.engineActive": "Engine active",
  "dashboard.engineOffline": "Offline",
  "dashboard.securityScore": "Security score",
  "dashboard.scanning": "Scanning security…",
  "dashboard.rescan": "Scan again",
  "dashboard.securityDescription": "Firewall, Defender, hardening, ports and processes analysis.",
  "dashboard.systemHealth": "System health",
  "dashboard.optimization": "Optimization",
  "dashboard.liveResources": "Live resources",
  "dashboard.disk": "Disk",
  "dashboard.connections": "Connections",
  "dashboard.systemInfo": "System information",
  "dashboard.os": "Operating system",
  "dashboard.architecture": "Architecture",
  "dashboard.processor": "Processor",
  "dashboard.logicalCpus": "Logical CPUs",
  "dashboard.totalRam": "Total RAM",
  "dashboard.python": "Python",

  // ─── Security view ───────────────────────────────────────────────
  "security.needsAdmin": "Administrator privileges required. Enable them in Settings → Administrator (or restart the app as Admin) and try again.",
  "security.remediateFailDefault": "Could not apply the fix.",
  "security.remediateOk": "Fix applied successfully.",
  "security.needsAdminShort": "Administrator privileges required.",
  "security.remediateError": "Error applying the fix.",
  "security.goToTool": "Go to tool",
  "security.fix": "Fix",
  "security.titlePrefix": "Security",
  "security.titleHighlight": "audit",
  "security.subtitle": "Firewall, Defender, hardening, open ports and processes · CIS L1/L2 controls.",
  "security.proTooltip": "Available in Pro",
  "security.exportReport": "Export report",
  "security.scoreLabel": "Score",
  "security.actions": "Actions",
  "security.scanning": "Scanning…",
  "security.fullScan": "Full scan",
  "security.ports": "Ports",
  "security.processes": "Processes",
  "security.critCount": "critical",
  "security.warnCount": "warnings",
  "security.okCount": "passed",
  "security.findings": "Findings",
  "security.analyzing": "Analyzing security… this may take a few seconds.",
  "security.colSeverity": "Severity",
  "security.colControl": "Control",
  "security.colFinding": "Finding",
  "security.colRecommendation": "Recommendation",
  "security.colAction": "Action",
  "security.findingsEmpty": "Run \"Full scan\" to audit.",
  "security.colPort": "Port",
  "security.colService": "Service",
  "security.colProcess": "Process",
  "security.colRisk": "Risk",
  "security.portsEmpty": "No data. Click Ports.",
  "security.colPid": "PID",
  "security.colReasons": "Reasons",
  "security.procsEmpty": "No data. Click Processes.",

  // ─── Optimization view ───────────────────────────────────────────
  "optimization.group_ui_tweaks": "Apply UI tweaks",
  "optimization.group_visual": "Visual effects",
  "optimization.group_gpu": "GPU by brand",
  "optimization.group_network": "TCP/IP network",
  "optimization.group_ssd": "SSD optimization",
  "optimization.group_perf": "Performance tweaks",
  "optimization.group_power": "Power plan",
  "optimization.heading": "Optimization",
  "optimization.subheading": "Expand each block and use checkboxes to choose what to apply. Reversible.",
  "optimization.score_label": "Optimization",
  "optimization.metric_disk": "Disk",
  "optimization.activity_title": "Activity",
  "optimization.activity_empty": "Apply something to see the log.",
  "optimization.log_applying": "applying",
  "optimization.log_applied_count": "applied",
  "optimization.tweaks_applied_suffix": "applied",
  "optimization.expand_hint": "Expand to choose what to apply",
  "optimization.btn_hide": "Hide",
  "optimization.btn_choose": "Choose",
  "optimization.no_options": "No options detected for this block.",
  "optimization.restart_warning": "Restarts Windows Explorer when applied.",
  "optimization.btn_apply": "Apply",
  "optimization.btn_apply_suffix": "selected",

  // ─── Memory view ─────────────────────────────────────────────────
  "memory.titlePrefix": "Memory",
  "memory.titleHighlight": "Manager",
  "memory.subtitle": "Live RAM usage + top processes.",
  "memory.buttonFreeing": "Freeing…",
  "memory.buttonFree": "Free RAM",
  "memory.alertTitle": "RAM freed",
  "memory.statTotal": "Total",
  "memory.statUsed": "Used",
  "memory.statAvailable": "Available",
  "memory.statPercent": "% Usage",
  "memory.tableTitle": "Top processes by memory",
  "memory.colRam": "RAM",
  "memory.colProcess": "Process",
  "memory.colPid": "PID",

  // ─── Cleanup view ────────────────────────────────────────────────
  "cleanup.title": "Disk",
  "cleanup.titleHighlight": "cleanup",
  "cleanup.subtitle": "Temp files, cache, prefetch, Windows Update.",
  "cleanup.recoverableSpace": "Recoverable space",
  "cleanup.actions": "Actions",
  "cleanup.btn.analyzing": "Analyzing…",
  "cleanup.btn.analyze": "Analyze",
  "cleanup.btn.cleaning": "Cleaning…",
  "cleanup.btn.cleanAll": "Clean all",
  "cleanup.btn.searching": "Searching…",
  "cleanup.btn.findDuplicates": "Find duplicates",
  "cleanup.scannedLocations": "Scanned locations",
  "cleanup.table.path": "Path",
  "cleanup.table.files": "Files",
  "cleanup.table.size": "Size",
  "cleanup.duplicates.title": "Duplicate files",
  "cleanup.duplicates.subtitle": "Finds duplicates by hash (SHA-256) in the folder you choose; Downloads by default.",
  "cleanup.duplicates.folderPlaceholder": "C:\\Users\\…\\Downloads (default)",
  "cleanup.duplicates.filesScanned": "files scanned",
  "cleanup.duplicates.groups": "groups",
  "cleanup.duplicates.recoverable": "recoverable",
  "cleanup.duplicates.copies": "copies",
  "cleanup.duplicates.each": "each",
  "cleanup.duplicates.wasted": "wasted",
  "cleanup.duplicates.noneFound": "No duplicates found.",
  "cleanup.log.title": "Log",
  "cleanup.log.empty": "Press \"Analyze\" to get started.",
  "cleanup.log.analyzingStart": "▶ Analyzing temporary files…",
  "cleanup.log.files": "files",
  "cleanup.log.totalRecoverable": "Total recoverable",
  "cleanup.log.error": "Error",
  "cleanup.log.cleaningStart": "▶ Cleaning temporary files…",
  "cleanup.log.filesDeleted": "files deleted",
  "cleanup.log.freed": "freed",
  "cleanup.log.nonCriticalErrors": "non-critical errors",
  "cleanup.log.searchingDuplicatesIn": "Searching for duplicates in",
  "cleanup.log.defaultFolder": "Downloads",
  "cleanup.log.groups": "groups",
  "cleanup.log.recoverable": "recoverable",

  // ─── Processes view ──────────────────────────────────────────────
  "processes.killAriaLabel": "Terminate",
  "processes.killTooltip": "Terminate process",
  "processes.confirmKill": "Terminate process",
  "processes.confirmKillWarning": "It will close immediately and you may lose unsaved data.",
  "processes.toastKilled": "Process terminated",
  "processes.toastKillFailed": "Could not terminate",
  "processes.toastKillAdmin": "Administrator privileges required. Restart WinSvalinn as administrator.",
  "processes.toastKillGone": "Process",
  "processes.toastKillGoneSuffix": "no longer exists.",
  "processes.toastKillError": "Error terminating process",
  "processes.toastKillErrorUnknown": "unknown",
  "processes.title": "Processes",
  "processes.subtitle": "processes · parent-child tree",
  "processes.loading": "Loading…",
  "processes.refresh": "Refresh",
  "processes.filterPlaceholder": "Filter by name…",
  "processes.expandAll": "Expand all",
  "processes.collapseAll": "Collapse all",
  "processes.colProcess": "Process",
  "processes.colMemory": "Memory",
  "processes.colAction": "Action",
  "processes.empty": "No processes loaded",

  // ─── Network view ────────────────────────────────────────────────
  "network.titlePrefix": "Network",
  "network.titleHighlight": "monitor",
  "network.statActiveConnections": "active connections",
  "network.statSuspicious": "suspicious",
  "network.statTop150": "top 150 shown",
  "network.btnLoading": "Loading…",
  "network.btnRefresh": "Refresh",
  "network.errorTitle": "Could not read all connections",
  "network.errorRunAsAdmin": "run as Administrator to see them all.",
  "network.searchPlaceholder": "Filter by process or IP…",
  "network.filterSuspiciousOnly": "Suspicious only",
  "network.colProcess": "Process",
  "network.colLocal": "Local",
  "network.colRemote": "Remote",
  "network.colStatus": "Status",
  "network.colType": "Type",
  "network.emptyState": "No matching connections",

  // ─── Gaming view ─────────────────────────────────────────────────
  "gaming.whyManual.ariaLabel": "Why this must be done manually",
  "gaming.whyManual.tooltip": "Games with anti-cheat (Vanguard, Easy Anti-Cheat, BattlEye, VAC) monitor and sign their own configuration files. If an external app edits them, the anti-cheat may flag it as cheating and issue a warning or ban. That's why WinSvalinn only automates Windows-level settings (GPU preference, Fullscreen Optimizations, Game Mode) — which anti-cheat doesn't touch — while in-game settings are applied by you inside the game itself, which is safe.",
  "gaming.badge.alreadyApplied": "Already applied",
  "gaming.badge.caution": "Caution",
  "gaming.adminBlocked": "Restart the app as Administrator to apply this.",
  "gaming.btn.reapply": "Re-apply",
  "gaming.btn.apply": "Apply",
  "gaming.result.applied": "Applied",
  "gaming.result.noChanges": "No changes",
  "gaming.subtitle": "Global PC optimizations and game-specific improvements.",
  "gaming.btn.rescan": "Rescan",
  "gaming.notAdmin": "You are not running as Administrator. Some optimizations (priority, network, power plan) require it; they are marked with ",
  "gaming.notAdmin.suffix": ".",
  "gaming.error.sidecar": "Could not reach the service. Is the sidecar running?",
  "gaming.globalSection.title": "Global system settings",
  "gaming.globalSection.subtitle": "— applied to the whole PC, no game selection needed",
  "gaming.perGameSection.title": "Per-game optimization",
  "gaming.perGameSection.subtitle": "— choose a game to see its specific settings",
  "gaming.scanning": "Searching for installed games…",
  "gaming.gameCount.one": "game detected",
  "gaming.gameCount.many": "games detected",
  "gaming.btn.pickGame": "Choose game",
  "gaming.picker.title": "Choose a game",
  "gaming.picker.description": "Select an installed game to view and apply its optimizations.",
  "gaming.badge.curated": "Curated",
  "gaming.picker.empty": "No games detected.",
  "gaming.btn.back": "Back",
  "gaming.anticheat.warning": "we do not touch its files (ban risk). Apply the recommended settings below manually inside the game.",
  "gaming.tips.title": "Recommended settings (manual)",
  "gaming.autoSection.title": "Automatic optimizations for this game",

  // ─── Settings view (admin / license / interface / security) ──────
  "settings.admin.title": "Administrator",
  "settings.admin.badgeAdmin": "Administrator",
  "settings.admin.badgeUser": "User",
  "settings.admin.alwaysLabel": "Always start as Administrator",
  "settings.admin.alwaysDesc": "Some optimizations and security fixes require Administrator permissions. If enabled, Windows will prompt for permission (UAC) every time you open WinSvalinn.",
  "settings.admin.toastEnabled": "Will start as Administrator",
  "settings.admin.toastDisabled": "Normal startup restored",
  "settings.admin.toastEnabledDesc": "Next time you open the app, Windows will prompt for permission (UAC).",
  "settings.admin.toastError": "Could not change setting",
  "settings.admin.toastErrorDesc": "Please try again.",
  "settings.errorGeneric": "Error",
  "settings.errorConnection": "Connection error.",
  "settings.license.editionEnterprise": "Enterprise",
  "settings.license.editionFree": "Free",
  "settings.license.currentEdition": "Current edition",
  "settings.license.licensedTo": "Licensed to",
  "settings.license.expires": "Expires",
  "settings.license.deactivateBtn": "Deactivate",
  "settings.license.deactivateHint": "Reverts to the Free edition on this machine.",
  "settings.license.freeDesc": "You are on the",
  "settings.license.freeDescMid": "Enter an activation key to unlock the",
  "settings.license.freeDescEnd": "edition (reports, full CIS audit, threat intelligence and scheduled scans).",
  "settings.license.keyLabel": "License key",
  "settings.license.keyPlaceholder": "Paste your license key…",
  "settings.license.activateBtn": "Activate",
  "settings.license.activated": "License activated",
  "settings.license.activatedDesc": "Enterprise edition activated.",
  "settings.license.activateError": "Could not activate the license",
  "settings.license.activateErrorDesc": "Invalid key.",
  "settings.license.deactivated": "License deactivated",
  "settings.license.deactivatedDesc": "You have returned to the Free edition.",
  "settings.license.deactivateError": "Could not deactivate the license",
  "settings.interface.activityLog": "Show activity panel (action log in Optimization and Cleanup)",
  "settings.interface.colorTheme": "Color theme",
  "settings.interface.palette.neon": "Neon",
  "settings.interface.palette.nord": "Nord",
  "settings.interface.palette.mono": "Black",
  "settings.interface.palette.forest": "Forest green",
  "settings.interface.palette.gray": "Gray",
  "settings.interface.palette.transparent": "Glass",
  "settings.interface.paletteHint": "Available in both editions. \"Neon\" is the default liquid-glass look.",
  "settings.logFolder.placeholder": "C:\\Users\\…\\WinSvalinn\\logs",
  "settings.logFolder.save": "Save",
  "settings.security.dryRun": "Dry-run mode by default (preview, no changes applied)",
  "settings.security.confirmDestructive": "Confirm destructive actions",
  "settings.security.autoElevate": "Request admin elevation automatically at startup",
  "settings.integrations.telemetry": "Send anonymous metrics (opt-in)",

  // ─── Titlebar ────────────────────────────────────────────────────
  "titlebar.hideMenu": "Hide menu",
  "titlebar.showMenu": "Show menu",
  "titlebar.searchPlaceholder": "Search…",
  "titlebar.minimize": "Minimize",
  "titlebar.maximize": "Maximize",
  "titlebar.close": "Close",

  // ─── Placeholder view ────────────────────────────────────────────
  "placeholder.comingSoon": "coming soon",
  "placeholder.migrating": "View under migration. The sidecar endpoints already exist — only the React component is missing.",

  // ─── Severity badge + score grades ───────────────────────────────
  "sev.crit": "Critical",
  "sev.high": "High",
  "sev.med": "Medium",
  "sev.ok": "OK",
  "sev.info": "Info",
  "grade.excellent": "EXCELLENT",
  "grade.good": "GOOD",
  "grade.fair": "FAIR",
  "grade.poor": "POOR",
  "grade.critical": "CRITICAL",

  // ─── Sidebar edition blurb ───────────────────────────────────────
  "sidebar.editionEnterprise": "Enterprise edition active: reports, full CIS audit and advanced scans.",
  "sidebar.editionFree": "Free edition. Enterprise adds reports, full CIS audit, threats and scheduled scans.",
};

const DICTS: Record<Lang, Dict> = { es: ES, en: EN };

// ─── Store ─────────────────────────────────────────────────────────

let lang: Lang = "es";
const listeners = new Set<(l: Lang) => void>();

function notify() {
  listeners.forEach((l) => l(lang));
}

function coerce(value: unknown): Lang {
  return value === "en" ? "en" : "es";
}

/** Read the current language synchronously. */
export function getLang(): Lang {
  return lang;
}

/** Translate a key against the active language; falls back to `fallback`/key. */
export function translate(key: string, fallback?: string): string {
  return DICTS[lang][key] ?? fallback ?? key;
}

/**
 * Set the language LIVE (no restart) and persist it to the sidecar config.
 * Persistence failures are tolerated — the live change still applies.
 */
export async function setLang(next: Lang): Promise<void> {
  const l = coerce(next);
  if (l !== lang) {
    lang = l;
    document.documentElement.lang = l;
    notify();
  }
  try {
    await api.configPatch(["ui", "language"], l);
  } catch {
    /* offline — live change already applied */
  }
}

/** Resolve the language from the sidecar config at startup (default "es"). */
export async function initI18n(): Promise<void> {
  try {
    const c = await api.config();
    const next = coerce(c?.ui?.language);
    if (next !== lang) {
      lang = next;
      notify();
    }
    document.documentElement.lang = lang;
  } catch {
    document.documentElement.lang = lang;
  }
}

// ─── Hooks ─────────────────────────────────────────────────────────

/** Subscribe to the active language. Re-renders on change. */
export function useLang(): { lang: Lang } {
  const [l, setL] = useState<Lang>(lang);
  useEffect(() => {
    setL(lang); // sync in case it changed between render and effect
    listeners.add(setL);
    return () => {
      listeners.delete(setL);
    };
  }, []);
  return { lang: l };
}

/**
 * Returns a `t(key, fallback?)` bound to the active language. Re-renders the
 * consuming component whenever the language changes (subscribes via useLang).
 */
export function useT(): (key: string, fallback?: string) => string {
  const { lang: l } = useLang();
  return (key: string, fallback?: string): string =>
    DICTS[l][key] ?? fallback ?? key;
}
