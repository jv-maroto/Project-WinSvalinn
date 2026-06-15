"""
Internationalization Module - WinSvalinn
Supports English (en) and Spanish (es).
"""


class I18n:
    """Language manager with English and Spanish support."""

    def __init__(self, lang="es"):
        self._lang = lang
        self._strings = {
            # ─── General ────────────────────────────────────────────
            "app_title": {
                "en": "WinSvalinn - System Security & Optimization",
                "es": "WinSvalinn - Seguridad y Optimizacion del Sistema",
            },
            "version": {"en": "v2.0.0", "es": "v2.0.0"},
            "optimizer_suite": {"en": "Optimizer Suite", "es": "Suite de Optimizacion"},
            # ─── Dock Categories ───────────────────────────────────
            "dock_home": {"en": "Home", "es": "Inicio"},
            "dock_security": {"en": "Security", "es": "Seguridad"},
            "dock_network": {"en": "Network", "es": "Red"},
            "dock_optimize": {"en": "Optimize", "es": "Optimizar"},
            "dock_cleanup": {"en": "Cleanup", "es": "Limpieza"},
            "dock_memory": {"en": "Memory", "es": "Memoria"},
            "dock_diagnose": {"en": "Diagnose", "es": "Diagnostico"},
            "dock_history": {"en": "History", "es": "Historial"},
            "dock_advanced": {"en": "Advanced", "es": "Avanzado"},
            "dock_plugins": {"en": "Plugins", "es": "Plugins"},
            # ─── Navigation Labels ─────────────────────────────────
            "nav_dashboard": {"en": "Dashboard", "es": "Panel Principal"},
            "nav_security": {"en": "Security Analysis", "es": "Analisis de Seguridad"},
            "nav_port_scan": {"en": "Port Scanner", "es": "Escaner de Puertos"},
            "nav_network": {"en": "Network Monitor", "es": "Monitor de Red"},
            "nav_processes": {"en": "Process Analyzer", "es": "Analizador de Procesos"},
            "nav_optimization": {"en": "System Optimization", "es": "Optimizacion del Sistema"},
            "nav_cleanup": {"en": "Disk Cleanup", "es": "Limpieza de Disco"},
            "nav_memory": {"en": "Memory Manager", "es": "Gestor de Memoria"},
            "nav_gpu": {"en": "GPU & Graphics", "es": "GPU y Graficos"},
            "nav_tweaks": {"en": "Performance Tweaks", "es": "Ajustes de Rendimiento"},
            "nav_services": {"en": "Service Manager", "es": "Gestor de Servicios"},
            "section_security": {"en": "SECURITY", "es": "SEGURIDAD"},
            "section_optimization": {"en": "OPTIMIZATION", "es": "OPTIMIZACION"},
            # ─── Dashboard ──────────────────────────────────────────
            "dashboard_title": {"en": "System Dashboard", "es": "Panel del Sistema"},
            "dashboard_subtitle": {
                "en": "Real-time system overview and health scores",
                "es": "Vista general del sistema en tiempo real y puntuaciones de salud",
            },
            "re_analyze": {"en": "Re-Analyze System", "es": "Re-Analizar Sistema"},
            "analyzing": {"en": "Analyzing...", "es": "Analizando..."},
            "analyzing_system": {
                "en": "Analyzing system... please wait",
                "es": "Analizando sistema... por favor espere",
            },
            "analysis_complete": {"en": "Analysis complete", "es": "Analisis completado"},
            "security_level": {"en": "Security Level", "es": "Nivel de Seguridad"},
            "overall_health": {"en": "Overall Health", "es": "Salud General"},
            "optimization_level": {"en": "Optimization Level", "es": "Nivel de Optimizacion"},
            "recommendations": {"en": "Recommendations", "es": "Recomendaciones"},
            "quick_actions": {"en": "Quick Actions", "es": "Acciones Rapidas"},
            "system_info": {"en": "System Information", "es": "Informacion del Sistema"},
            "cpu_usage": {"en": "CPU Usage", "es": "Uso de CPU"},
            "ram_usage": {"en": "RAM Usage", "es": "Uso de RAM"},
            "disk_usage": {"en": "Disk Usage", "es": "Uso de Disco"},
            "connections": {"en": "Connections", "es": "Conexiones"},
            "waiting_analysis": {
                "en": "Waiting for analysis to complete...",
                "es": "Esperando a que se complete el analisis...",
            },
            # ─── Score Grades ───────────────────────────────────────
            "grade_excellent": {"en": "Excellent", "es": "Excelente"},
            "grade_good": {"en": "Good", "es": "Bueno"},
            "grade_fair": {"en": "Fair", "es": "Regular"},
            "grade_poor": {"en": "Poor", "es": "Deficiente"},
            "grade_critical": {"en": "Critical", "es": "Critico"},
            # ─── Post-Analysis Summary ──────────────────────────────
            "summary_title": {
                "en": "System Status Summary",
                "es": "Resumen del Estado del Sistema",
            },
            "summary_maxed": {"en": "Things at maximum / OK", "es": "Cosas al maximo / OK"},
            "summary_missing": {"en": "Things to improve", "es": "Cosas por mejorar"},
            "summary_all_good": {
                "en": "Your system is fully optimized and secure!",
                "es": "Tu sistema esta completamente optimizado y seguro!",
            },
            "summary_issues_found": {
                "en": "issues found that need attention",
                "es": "problemas encontrados que necesitan atencion",
            },
            # ─── Security ───────────────────────────────────────────
            "full_security_scan": {
                "en": "Full Security Scan",
                "es": "Escaneo Completo de Seguridad",
            },
            "start_full_scan": {"en": "Start Full Scan", "es": "Iniciar Escaneo Completo"},
            "scanning": {"en": "Scanning...", "es": "Escaneando..."},
            "export_report": {"en": "Export Report", "es": "Exportar Informe"},
            "ready_to_scan": {
                "en": "Ready to scan. Click 'Start Full Scan' to begin.",
                "es": "Listo para escanear. Haga clic en 'Iniciar Escaneo Completo' para comenzar.",
            },
            "scan_complete": {
                "en": "SCAN COMPLETE - RESULTS SUMMARY",
                "es": "ESCANEO COMPLETO - RESUMEN DE RESULTADOS",
            },
            "no_suspicious_ips": {
                "en": "No suspicious IPs detected",
                "es": "No se detectaron IPs sospechosas",
            },
            "no_suspicious_procs": {
                "en": "No suspicious processes detected",
                "es": "No se detectaron procesos sospechosos",
            },
            "no_arp_spoofing": {
                "en": "No ARP spoofing detected",
                "es": "No se detecto suplantacion ARP",
            },
            "no_suspicious_tasks": {
                "en": "No suspicious scheduled tasks",
                "es": "No se detectaron tareas programadas sospechosas",
            },
            # ─── Port Scanner ───────────────────────────────────────
            "port_scanner": {"en": "Port Scanner", "es": "Escaner de Puertos"},
            "start_port": {"en": "Start Port:", "es": "Puerto Inicio:"},
            "end_port": {"en": "End Port:", "es": "Puerto Fin:"},
            "scan_ports": {"en": "Scan Ports", "es": "Escanear Puertos"},
            "stop": {"en": "Stop", "es": "Detener"},
            "port_scan_help": {
                "en": "Configure port range and click 'Scan Ports' to begin.",
                "es": "Configure el rango de puertos y haga clic en 'Escanear Puertos' para comenzar.",
            },
            "port_scan_desc": {
                "en": "Scans your local machine for open network ports. Open ports are entry points - close unused ones.",
                "es": "Escanea puertos de red abiertos en tu maquina. Los puertos abiertos son puntos de entrada - cierra los que no uses.",
            },
            # ─── Network ────────────────────────────────────────────
            "network_monitor": {"en": "Network Monitor", "es": "Monitor de Red"},
            "refresh": {"en": "Refresh", "es": "Actualizar"},
            "process": {"en": "Process", "es": "Proceso"},
            "local_address": {"en": "Local Address", "es": "Direccion Local"},
            "remote_address": {"en": "Remote Address", "es": "Direccion Remota"},
            "status": {"en": "Status", "es": "Estado"},
            "network_desc": {
                "en": "Shows all active network connections, which programs are connecting and where.",
                "es": "Muestra todas las conexiones de red activas, que programas se conectan y a donde.",
            },
            # ─── Processes ──────────────────────────────────────────
            "process_analyzer": {"en": "Process Analyzer", "es": "Analizador de Procesos"},
            "analyze_processes": {"en": "Analyze Processes", "es": "Analizar Procesos"},
            "process_desc": {
                "en": "Detects suspicious processes that could be malware, cryptominers, or unwanted software.",
                "es": "Detecta procesos sospechosos que podrian ser malware, criptomineros o software no deseado.",
            },
            # ─── Optimization ───────────────────────────────────────
            "system_optimization": {"en": "System Optimization", "es": "Optimizacion del Sistema"},
            "opt_subtitle": {
                "en": "One-click optimization tools for maximum performance",
                "es": "Herramientas de optimizacion con un clic para maximo rendimiento",
            },
            "optimize": {"en": "Optimize", "es": "Optimizar"},
            "enable": {"en": "Enable", "es": "Activar"},
            "apply_all": {"en": "Apply All", "es": "Aplicar Todo"},
            "optimization_log": {"en": "Optimization Log", "es": "Registro de Optimizacion"},
            "select_optimization": {
                "en": "Select an optimization to apply.",
                "es": "Seleccione una optimizacion para aplicar.",
            },
            # Visual effects
            "opt_visual_title": {
                "en": "Visual Effects - Performance Mode",
                "es": "Efectos Visuales - Modo Rendimiento",
            },
            "opt_visual_desc": {
                "en": "Disables animations, transparency, shadows and visual effects. Frees CPU/GPU resources for apps.",
                "es": "Desactiva animaciones, transparencia, sombras y efectos visuales. Libera recursos de CPU/GPU para aplicaciones.",
            },
            # GPU
            "opt_gpu_title": {
                "en": "GPU & Graphics Optimization",
                "es": "Optimizacion GPU y Graficos",
            },
            "opt_gpu_desc": {
                "en": "Disables Game DVR, enables hardware GPU scheduling, optimizes fullscreen and DirectX. Detects your GPU brand.",
                "es": "Desactiva Game DVR, activa aceleracion GPU por hardware, optimiza pantalla completa y DirectX. Detecta la marca de tu GPU.",
            },
            # Network
            "opt_net_title": {"en": "Network Optimization", "es": "Optimizacion de Red"},
            "opt_net_desc": {
                "en": "Flushes DNS cache, resets Winsock catalog, optimizes TCP settings, disables Nagle's algorithm for lower latency.",
                "es": "Limpia cache DNS, reinicia catalogo Winsock, optimiza configuracion TCP, desactiva algoritmo de Nagle para menor latencia.",
            },
            # Power
            "opt_power_title": {
                "en": "Ultimate Performance Power Plan",
                "es": "Plan de Energia Rendimiento Maximo",
            },
            "opt_power_desc": {
                "en": "Enables the hidden 'Ultimate Performance' power plan. CPU never throttles down, max clock speed always.",
                "es": "Activa el plan de energia oculto 'Rendimiento Maximo'. La CPU nunca reduce velocidad, siempre al maximo reloj.",
            },
            # SSD
            "opt_ssd_title": {"en": "SSD Optimization", "es": "Optimizacion SSD"},
            "opt_ssd_desc": {
                "en": "Disables Superfetch (unnecessary on SSD), enables TRIM for longevity, disables last-access timestamps.",
                "es": "Desactiva Superfetch (innecesario en SSD), activa TRIM para durabilidad, desactiva timestamps de ultimo acceso.",
            },
            # Full tweaks
            "opt_tweaks_title": {
                "en": "Full Performance Tweaks",
                "es": "Ajustes de Rendimiento Completos",
            },
            "opt_tweaks_desc": {
                "en": "Applies ALL tweaks: disables Cortana, background apps, mouse acceleration, optimizes GPU priorities, game scheduling.",
                "es": "Aplica TODOS los ajustes: desactiva Cortana, apps en segundo plano, aceleracion del raton, prioridades GPU, programacion de juegos.",
            },
            # ─── Disk Cleanup ───────────────────────────────────────
            "disk_cleanup": {"en": "Disk Cleanup", "es": "Limpieza de Disco"},
            "analyze": {"en": "Analyze", "es": "Analizar"},
            "clean_all": {"en": "Clean All", "es": "Limpiar Todo"},
            "cleaning": {"en": "Cleaning...", "es": "Limpiando..."},
            "cleanup_help": {
                "en": "Click 'Analyze' to scan for cleanable files",
                "es": "Haga clic en 'Analizar' para buscar archivos limpiables",
            },
            "cleanup_desc": {
                "en": "Removes temp files, cache, thumbnails, Windows Update leftovers and more. Frees disk space safely.",
                "es": "Elimina archivos temporales, cache, miniaturas, restos de Windows Update y mas. Libera espacio en disco de forma segura.",
            },
            # ─── Memory ─────────────────────────────────────────────
            "memory_manager": {"en": "Memory Manager", "es": "Gestor de Memoria"},
            "optimize_ram": {"en": "Optimize RAM", "es": "Optimizar RAM"},
            "free_ram": {"en": "Free RAM Now", "es": "Liberar RAM Ahora"},
            "total_ram": {"en": "Total RAM", "es": "RAM Total"},
            "used": {"en": "Used", "es": "Usado"},
            "available": {"en": "Available", "es": "Disponible"},
            "usage": {"en": "Usage", "es": "Uso"},
            "memory_desc": {
                "en": "Shows RAM usage by process. Optimize frees cached memory, flushes DNS and triggers garbage collection.",
                "es": "Muestra uso de RAM por proceso. Optimizar libera memoria cacheada, limpia DNS y activa recoleccion de basura.",
            },
            "ram_freed": {
                "en": "RAM freed successfully. Working set trimmed for all processes.",
                "es": "RAM liberada exitosamente. Conjunto de trabajo recortado para todos los procesos.",
            },
            # ─── GPU ────────────────────────────────────────────────
            "gpu_graphics": {"en": "GPU & Graphics", "es": "GPU y Graficos"},
            "gpu_info": {"en": "GPU Information", "es": "Informacion de GPU"},
            "gpu_detected": {"en": "Detected GPU Brand", "es": "Marca de GPU Detectada"},
            "visual_effects": {"en": "Visual Effects", "es": "Efectos Visuales"},
            "best_performance": {"en": "Best Performance", "es": "Mejor Rendimiento"},
            "balanced": {"en": "Balanced", "es": "Equilibrado"},
            "optimize_gpu": {"en": "Optimize GPU", "es": "Optimizar GPU"},
            "gpu_perf_opt": {
                "en": "GPU Performance Optimization",
                "es": "Optimizacion de Rendimiento GPU",
            },
            "gpu_brand_opt": {"en": "Brand-Specific Optimization", "es": "Optimizacion por Marca"},
            "nvidia_opt_desc": {
                "en": "NVIDIA: Maximize performance in NVIDIA Control Panel, disable shader cache cleanup, optimize for compute.",
                "es": "NVIDIA: Maximizar rendimiento en Panel de Control NVIDIA, desactivar limpieza de shader cache, optimizar para computo.",
            },
            "amd_opt_desc": {
                "en": "AMD: Set Radeon profile to performance, disable Radeon overlay, optimize shader cache.",
                "es": "AMD: Establecer perfil Radeon a rendimiento, desactivar overlay de Radeon, optimizar shader cache.",
            },
            "intel_opt_desc": {
                "en": "Intel: Set graphics profile to maximum performance, disable power-saving features.",
                "es": "Intel: Establecer perfil grafico a rendimiento maximo, desactivar funciones de ahorro de energia.",
            },
            # ─── Tweaks ─────────────────────────────────────────────
            "performance_tweaks": {"en": "Performance Tweaks", "es": "Ajustes de Rendimiento"},
            "tweaks_subtitle": {
                "en": "Advanced Windows tweaks for gaming and productivity",
                "es": "Ajustes avanzados de Windows para juegos y productividad",
            },
            "power_plans": {"en": "Power Plans", "es": "Planes de Energia"},
            "activate": {"en": "Activate", "es": "Activar"},
            "create_ultimate": {
                "en": "Create Ultimate Performance Plan",
                "es": "Crear Plan Rendimiento Maximo",
            },
            "apply_all_tweaks": {
                "en": "Apply All Performance Tweaks",
                "es": "Aplicar Todos los Ajustes de Rendimiento",
            },
            "system_tweaks": {"en": "System Tweaks", "es": "Ajustes del Sistema"},
            "gaming_tweaks": {"en": "Gaming Tweaks", "es": "Ajustes para Juegos"},
            "storage_tweaks": {"en": "Storage Tweaks", "es": "Ajustes de Almacenamiento"},
            # ─── Services ───────────────────────────────────────────
            "service_manager": {"en": "Service Manager", "es": "Gestor de Servicios"},
            "scan_services": {"en": "Scan Services", "es": "Escanear Servicios"},
            "services_desc": {
                "en": "Identifies Windows services that can be safely disabled to save CPU, RAM and boot time.",
                "es": "Identifica servicios de Windows que se pueden desactivar con seguridad para ahorrar CPU, RAM y tiempo de arranque.",
            },
            # ─── Common ─────────────────────────────────────────────
            "ok": {"en": "OK", "es": "Aceptar"},
            "cancel": {"en": "Cancel", "es": "Cancelar"},
            "close": {"en": "Close", "es": "Cerrar"},
            "language": {"en": "Language", "es": "Idioma"},
            "english": {"en": "English", "es": "Ingles"},
            "spanish": {"en": "Spanish", "es": "Espanol"},
            "admin_required": {
                "en": "Some features require Administrator privileges. Run as Admin for full functionality.",
                "es": "Algunas funciones requieren privilegios de Administrador. Ejecuta como Admin para funcionalidad completa.",
            },
            "restart_required": {
                "en": "Some changes require a system restart to take effect.",
                "es": "Algunos cambios requieren reiniciar el sistema para tomar efecto.",
            },
            # ─── Descriptions for each feature ─────────────────────
            "desc_firewall": {
                "en": "Firewall: Blocks unauthorized incoming/outgoing network traffic. All 3 profiles should be ON.",
                "es": "Firewall: Bloquea trafico de red entrante/saliente no autorizado. Los 3 perfiles deben estar ACTIVADOS.",
            },
            "desc_defender": {
                "en": "Windows Defender: Built-in antivirus protection. Real-time scanning should always be enabled.",
                "es": "Windows Defender: Proteccion antivirus integrada. El escaneo en tiempo real siempre debe estar activado.",
            },
            "desc_suspicious_ips": {
                "en": "Suspicious IPs: Connections to unusual ports or known-malicious port ranges detected.",
                "es": "IPs Sospechosas: Conexiones a puertos inusuales o rangos de puertos conocidos como maliciosos.",
            },
            "desc_arp": {
                "en": "ARP Table: Checks for duplicate MAC addresses which indicate ARP spoofing (man-in-the-middle attacks).",
                "es": "Tabla ARP: Busca direcciones MAC duplicadas que indican suplantacion ARP (ataques man-in-the-middle).",
            },
            "desc_startup": {
                "en": "Startup Programs: Programs that auto-run at boot. Too many slow down your PC startup.",
                "es": "Programas de Inicio: Programas que se ejecutan al arrancar. Demasiados ralentizan el inicio del PC.",
            },
            "desc_dns": {
                "en": "DNS Cache: Stores recent domain lookups. Suspicious TLDs (.ru, .tk, .cn) may indicate malware.",
                "es": "Cache DNS: Almacena busquedas de dominio recientes. TLDs sospechosos (.ru, .tk, .cn) pueden indicar malware.",
            },
            "desc_temp": {
                "en": "Temp Files: Accumulated junk files from apps, Windows updates, and browsing. Safe to clean.",
                "es": "Archivos Temporales: Archivos basura acumulados de apps, actualizaciones de Windows y navegacion. Seguros de limpiar.",
            },
            "desc_visual": {
                "en": "Visual Effects: Windows animations and transparency consume GPU/CPU. Disabling them gives free performance.",
                "es": "Efectos Visuales: Las animaciones y transparencia de Windows consumen GPU/CPU. Desactivarlos da rendimiento gratis.",
            },
            "desc_power": {
                "en": "Power Plan: Controls CPU throttling. 'Ultimate Performance' keeps CPU at max frequency always.",
                "es": "Plan de Energia: Controla la limitacion de la CPU. 'Rendimiento Maximo' mantiene la CPU a maxima frecuencia siempre.",
            },
            "desc_security_scan": {
                "en": "Runs a comprehensive security analysis: firewall, Defender, suspicious IPs, ARP spoofing, "
                "processes, DNS cache, scheduled tasks, shared resources, and user accounts.",
                "es": "Ejecuta un analisis de seguridad completo: firewall, Defender, IPs sospechosas, suplantacion ARP, "
                "procesos, cache DNS, tareas programadas, recursos compartidos y cuentas de usuario.",
            },
            "desc_network": {
                "en": "Monitors all active TCP/UDP connections in real-time. Shows which programs connect to the internet and where.",
                "es": "Monitorea todas las conexiones TCP/UDP activas en tiempo real. Muestra que programas se conectan a internet y a donde.",
            },
            "desc_processes": {
                "en": "Analyzes running processes for suspicious behavior: hidden windows, no company info, unusual CPU usage, "
                "known malware names. Flags HIGH and MEDIUM risk processes.",
                "es": "Analiza procesos en ejecucion buscando comportamiento sospechoso: ventanas ocultas, sin info de empresa, "
                "uso inusual de CPU, nombres de malware conocidos. Marca procesos de riesgo ALTO y MEDIO.",
            },
            "desc_optimization": {
                "en": "One-click optimizations: visual effects, GPU settings, network tuning, power plans, SSD tweaks, "
                "and performance registry tweaks. Each button applies a specific category.",
                "es": "Optimizaciones con un clic: efectos visuales, configuracion GPU, ajuste de red, planes de energia, "
                "ajustes SSD y ajustes de registro de rendimiento. Cada boton aplica una categoria especifica.",
            },
            "desc_cleanup": {
                "en": "Scans and removes temporary files, browser cache, Windows Update leftovers, thumbnail cache, "
                "and other junk. Frees disk space without affecting your files.",
                "es": "Escanea y elimina archivos temporales, cache del navegador, restos de Windows Update, cache de miniaturas "
                "y otros archivos basura. Libera espacio en disco sin afectar tus archivos.",
            },
            "desc_memory": {
                "en": "Advanced RAM optimizer: trims working sets of all processes, flushes DNS cache, triggers .NET garbage "
                "collection, clears font/thumbnail caches. Shows RAM usage by category (browsers, games, system, etc).",
                "es": "Optimizador avanzado de RAM: recorta conjuntos de trabajo de todos los procesos, limpia cache DNS, activa "
                "recoleccion de basura .NET, limpia caches de fuentes/miniaturas. Muestra uso de RAM por categoria (navegadores, juegos, sistema, etc).",
            },
            "desc_tweaks": {
                "en": "Advanced Windows registry tweaks: power plans, disable Cortana/tips/background apps, optimize GPU/game "
                "priority, disable mouse acceleration, SSD tweaks (hibernation, TRIM, Superfetch).",
                "es": "Ajustes avanzados del registro de Windows: planes de energia, desactivar Cortana/sugerencias/apps en segundo plano, "
                "optimizar prioridad GPU/juegos, desactivar aceleracion del raton, ajustes SSD (hibernacion, TRIM, Superfetch).",
            },
            "desc_services": {
                "en": "Scans Windows services and identifies which can be safely disabled: Xbox services, Fax, telemetry, "
                "print spooler (if no printer), etc. Saves CPU, RAM and boot time.",
                "es": "Escanea servicios de Windows e identifica cuales se pueden desactivar con seguridad: servicios Xbox, Fax, telemetria, "
                "cola de impresion (si no hay impresora), etc. Ahorra CPU, RAM y tiempo de arranque.",
            },
            "ram_categories": {"en": "RAM Usage by Category", "es": "Uso de RAM por Categoria"},
            "top_processes": {
                "en": "Top Processes by Memory",
                "es": "Procesos Principales por Memoria",
            },
            "active": {"en": "ACTIVE", "es": "ACTIVO"},
            "optimizing_ram": {"en": "Optimizing RAM...", "es": "Optimizando RAM..."},
            "no_report": {
                "en": "No scan results to export. Run a scan first.",
                "es": "No hay resultados para exportar. Ejecute un escaneo primero.",
            },
            "report_saved": {"en": "Report saved to:", "es": "Informe guardado en:"},
            "click_scan_services": {
                "en": "Click 'Scan Services' to analyze Windows services.",
                "es": "Haga clic en 'Escanear Servicios' para analizar los servicios de Windows.",
            },
            "click_analyze_processes": {
                "en": "Click 'Analyze Processes' to detect suspicious activity.",
                "es": "Haga clic en 'Analizar Procesos' para detectar actividad sospechosa.",
            },
            "system_clean": {
                "en": "No suspicious processes detected. System looks clean.",
                "es": "No se detectaron procesos sospechosos. El sistema esta limpio.",
            },
            "swap": {"en": "Swap", "es": "Swap"},
            # ─── Auto-fix & new features ─────────────────────
            "fix": {"en": "Fix", "es": "Reparar"},
            "fix_all": {"en": "Fix All Issues", "es": "Reparar Todos los Problemas"},
            "fixing": {"en": "Fixing...", "es": "Reparando..."},
            "fix_firewall": {"en": "Enable Firewall", "es": "Activar Firewall"},
            "fix_defender": {"en": "Enable Defender", "es": "Activar Defender"},
            "fix_dns": {"en": "Flush DNS", "es": "Limpiar DNS"},
            "fix_shares": {"en": "Remove Shares", "es": "Eliminar Compartidos"},
            "fix_success": {"en": "Fixed successfully", "es": "Reparado exitosamente"},
            "fix_need_admin": {
                "en": "Fix failed - run as Administrator",
                "es": "Reparacion fallida - ejecutar como Administrador",
            },
            "auto_fix_desc": {
                "en": "Automatically fix detected security issues. Some fixes require Administrator privileges.",
                "es": "Repara automaticamente los problemas de seguridad detectados. Algunas reparaciones requieren Administrador.",
            },
            # External ports
            "external_ports": {"en": "External Ports", "es": "Puertos Externos"},
            "scan_external": {"en": "Scan External Ports", "es": "Escanear Puertos Externos"},
            "external_ports_desc": {
                "en": "Ports open to outside connections (listening on 0.0.0.0). These are accessible from other devices on your network.",
                "es": "Puertos abiertos a conexiones externas (escuchando en 0.0.0.0). Estos son accesibles desde otros dispositivos en tu red.",
            },
            "no_external_ports": {
                "en": "No externally exposed ports found. Your system is well protected.",
                "es": "No se encontraron puertos expuestos externamente. Tu sistema esta bien protegido.",
            },
            # Antivirus
            "antivirus_status": {"en": "Antivirus Status", "es": "Estado del Antivirus"},
            "installed_av": {
                "en": "Installed Antivirus Products",
                "es": "Productos Antivirus Instalados",
            },
            "av_active": {"en": "Active", "es": "Activo"},
            "av_inactive": {"en": "Inactive", "es": "Inactivo"},
            "av_updated": {"en": "Up to date", "es": "Actualizado"},
            "av_outdated": {"en": "Outdated", "es": "Desactualizado"},
            "defender_off_but_av": {
                "en": "Windows Defender is OFF but you have another antivirus active - this is normal.",
                "es": "Windows Defender esta APAGADO pero tienes otro antivirus activo - esto es normal.",
            },
            "no_av_detected": {
                "en": "No antivirus detected! Install one immediately.",
                "es": "No se detecto ningun antivirus! Instala uno inmediatamente.",
            },
            # ─── ARP Fix ──────────────────────────────────────────
            "fix_arp": {"en": "Flush ARP", "es": "Limpiar ARP"},
            "fix_arp_desc": {
                "en": "Flush ARP cache to clear duplicate/spoofed MAC entries.",
                "es": "Limpiar cache ARP para eliminar entradas MAC duplicadas/suplantadas.",
            },
            # ─── Block Port ───────────────────────────────────────
            "block_port": {"en": "Block Port", "es": "Bloquear Puerto"},
            "close_port": {"en": "Close Port", "es": "Cerrar Puerto"},
            "block_port_desc": {
                "en": "Block this port via Windows Firewall rule.",
                "es": "Bloquear este puerto mediante regla del Firewall de Windows.",
            },
            "port_blocked": {
                "en": "Port blocked successfully",
                "es": "Puerto bloqueado exitosamente",
            },
            # ─── Exposed Ports UI ─────────────────────────────────
            "exposed_ports_title": {
                "en": "Exposed Ports - Currently Listening",
                "es": "Puertos Expuestos - Escuchando Actualmente",
            },
            "exposed_ports_subtitle": {
                "en": "Ports open to external connections. Close unused ones to reduce attack surface.",
                "es": "Puertos abiertos a conexiones externas. Cierra los que no uses para reducir la superficie de ataque.",
            },
            "no_exposed_ports": {
                "en": "No externally exposed ports found. Your system is well protected.",
                "es": "No se encontraron puertos expuestos externamente. Tu sistema esta bien protegido.",
            },
            "advanced_scan": {"en": "Advanced Scan", "es": "Escaneo Avanzado"},
            "advanced_scan_desc": {
                "en": "Manually scan a custom port range on localhost.",
                "es": "Escanear manualmente un rango personalizado de puertos en localhost.",
            },
            "refresh_ports": {"en": "Refresh Ports", "es": "Actualizar Puertos"},
            "scanning_ports": {
                "en": "Scanning exposed ports...",
                "es": "Escaneando puertos expuestos...",
            },
            "port_col": {"en": "Port", "es": "Puerto"},
            "service_col": {"en": "Service", "es": "Servicio"},
            "process_col": {"en": "Process", "es": "Proceso"},
            "risk_col": {"en": "Risk", "es": "Riesgo"},
            "action_col": {"en": "Action", "es": "Accion"},
            # ─── Startup Score ────────────────────────────────────
            "startup_score": {"en": "Startup", "es": "Inicio"},
            "startup_score_desc": {
                "en": "Score based on startup program impact. Fewer heavy startup programs = higher score.",
                "es": "Puntuacion basada en el impacto de programas de inicio. Menos programas pesados = mayor puntuacion.",
            },
            # ─── Rescan ───────────────────────────────────────────
            "rescanning": {"en": "Re-scanning...", "es": "Re-escaneando..."},
            "rescan_complete": {"en": "Re-scan complete", "es": "Re-escaneo completado"},
            # ─── RAM Optimization Card ──────────────────────────
            "opt_ram_title": {"en": "RAM Optimization", "es": "Optimizacion de RAM"},
            "opt_ram_desc": {
                "en": "Frees RAM by trimming working sets, flushing DNS cache, clearing font/thumbnail caches, and triggering .NET garbage collection.",
                "es": "Libera RAM recortando conjuntos de trabajo, limpiando cache DNS, caches de fuentes/miniaturas y activando recoleccion de basura .NET.",
            },
            # ─── GPU Brand-Specific Optimization Card ───────────
            "opt_gpu_brand_title": {
                "en": "GPU Brand Optimization (Auto-Detect)",
                "es": "Optimizacion GPU por Marca (Auto-Detectar)",
            },
            "opt_gpu_brand_desc": {
                "en": "Auto-detects your GPU brand (NVIDIA/AMD/Intel) and applies brand-specific registry tweaks: max performance, disable overlays, shader cache, telemetry.",
                "es": "Auto-detecta tu marca de GPU (NVIDIA/AMD/Intel) y aplica ajustes de registro especificos: rendimiento maximo, desactivar overlays, shader cache, telemetria.",
            },
            # ─── UAC Elevation ──────────────────────────────────
            "requesting_admin": {
                "en": "Requesting administrator privileges...",
                "es": "Solicitando privilegios de administrador...",
            },
            "elevation_cancelled": {
                "en": "Elevation cancelled or failed",
                "es": "Elevacion cancelada o fallida",
            },
            # ─── Startup Manager ────────────────────────────────
            "startup_manager_title": {"en": "Startup Programs", "es": "Programas de Inicio"},
            "startup_manager_desc": {
                "en": "Disable startup programs to speed up boot time and free resources. Each disabled program improves your Startup score.",
                "es": "Desactiva programas de inicio para acelerar el arranque y liberar recursos. Cada programa desactivado mejora tu puntuacion de Inicio.",
            },
            "no_startup_programs": {
                "en": "No startup programs found",
                "es": "No se encontraron programas de inicio",
            },
            "startup_location": {"en": "Location", "es": "Ubicacion"},
            "name_col": {"en": "Name", "es": "Nombre"},
            "disable": {"en": "Disable", "es": "Desactivar"},
            "startup_programs_count": {
                "en": "startup programs found",
                "es": "programas de inicio encontrados",
            },
            # ─── System Port Protection ───────────────────────
            "system_port_tag": {"en": "SYSTEM", "es": "SISTEMA"},
            "system_port_tooltip": {
                "en": "System-critical port - cannot be blocked (may crash Windows)",
                "es": "Puerto critico del sistema - no se puede bloquear (puede colapsar Windows)",
            },
            # ─── AV Configuration ─────────────────────────────
            "av_config_title": {
                "en": "Antivirus Configuration",
                "es": "Configuracion del Antivirus",
            },
            "av_component_running": {"en": "Running", "es": "Ejecutandose"},
            "av_component_stopped": {"en": "Stopped", "es": "Detenido"},
            # ─── Navigation (new entries) ─────────────────────
            "nav_startup": {"en": "Startup Manager", "es": "Gestor de Inicio"},
            "nav_terminology": {"en": "Terminology", "es": "Terminologia"},
            "section_info": {"en": "INFO", "es": "INFO"},
            # ─── Dashboard split recommendations ──────────────
            "security_recs_title": {
                "en": "Security Recommendations",
                "es": "Recomendaciones de Seguridad",
            },
            "optimization_recs_title": {
                "en": "Optimization Recommendations",
                "es": "Recomendaciones de Optimizacion",
            },
            # ─── Startup classification ───────────────────────
            "startup_type_col": {"en": "Type", "es": "Tipo"},
            "startup_type_system": {"en": "System", "es": "Sistema"},
            "startup_type_driver": {"en": "Driver", "es": "Controlador"},
            "startup_type_external": {"en": "External", "es": "Externo"},
            "startup_system_warning": {
                "en": "Essential for Windows - do not disable",
                "es": "Esencial para Windows - no desactivar",
            },
            "startup_driver_warning": {
                "en": "Hardware driver - disabling may cause issues",
                "es": "Controlador de hardware - desactivar puede causar problemas",
            },
            # ─── Boot speed tweaks ────────────────────────────
            "boot_speed_title": {"en": "Boot Speed Tweaks", "es": "Mejoras de Velocidad de Inicio"},
            "boot_speed_desc": {
                "en": "System-level tweaks to reduce Windows boot time without removing startup programs.",
                "es": "Ajustes a nivel de sistema para reducir el tiempo de arranque de Windows sin quitar programas de inicio.",
            },
            "boot_timeout_title": {"en": "Reduce Boot Timeout", "es": "Reducir Tiempo de Arranque"},
            "boot_timeout_desc": {
                "en": "Reduces the OS selection screen timeout from 30s to 3s.",
                "es": "Reduce el tiempo de espera de seleccion de SO de 30s a 3s.",
            },
            "boot_fast_startup_title": {"en": "Enable Fast Startup", "es": "Activar Inicio Rapido"},
            "boot_fast_startup_desc": {
                "en": "Enables Windows Fast Startup (hybrid shutdown) for quicker boot.",
                "es": "Activa el Inicio Rapido de Windows (apagado hibrido) para un arranque mas rapido.",
            },
            "boot_disable_log_title": {
                "en": "Disable Boot Log",
                "es": "Desactivar Registro de Arranque",
            },
            "boot_disable_log_desc": {
                "en": "Disables boot logging to skip unnecessary disk writes during startup.",
                "es": "Desactiva el registro de arranque para evitar escrituras innecesarias en disco durante el inicio.",
            },
            "boot_prefetch_title": {"en": "Optimize Prefetch", "es": "Optimizar Prefetch"},
            "boot_prefetch_desc": {
                "en": "Optimizes Windows Prefetch to preload boot files and applications faster.",
                "es": "Optimiza Windows Prefetch para precargar archivos de arranque y aplicaciones mas rapido.",
            },
            "apply": {"en": "Apply", "es": "Aplicar"},
            # ─── Terminology section ──────────────────────────
            "terminology_title": {"en": "Terminology", "es": "Terminologia"},
            "terminology_subtitle": {
                "en": "Explanations of the tools and protections used by WinSvalinn.",
                "es": "Explicaciones de las herramientas y protecciones usadas por WinSvalinn.",
            },
            "term_tab_security": {"en": "Security", "es": "Seguridad"},
            "term_tab_optimization": {"en": "Optimization", "es": "Optimizacion"},
            # Security terms
            "term_firewall_title": {"en": "Firewall", "es": "Firewall"},
            "term_firewall_desc": {
                "en": "A firewall controls incoming and outgoing network traffic. Windows Firewall has 3 profiles: Domain (corporate networks), Private (home/trusted), and Public (cafes, airports). Each can be ON or OFF independently. If you use a third-party security suite like Kaspersky, it manages its own firewall and disables Windows Firewall — this is normal and expected.",
                "es": "Un firewall controla el trafico de red entrante y saliente. El Firewall de Windows tiene 3 perfiles: Dominio (redes corporativas), Privado (hogar/confianza) y Publico (cafeterias, aeropuertos). Cada uno puede estar ON u OFF independientemente. Si usas una suite de seguridad como Kaspersky, esta gestiona su propio firewall y desactiva el de Windows — esto es normal y esperado.",
            },
            "term_defender_title": {"en": "Windows Defender", "es": "Windows Defender"},
            "term_defender_desc": {
                "en": "Windows Defender is the built-in antivirus. It provides real-time protection (scans files as you open them) and virus definitions (database of known threats). When you install a third-party antivirus like Kaspersky, Norton, or Bitdefender, Defender automatically disables itself to avoid conflicts. This is normal — your third-party antivirus takes over protection.",
                "es": "Windows Defender es el antivirus integrado. Proporciona proteccion en tiempo real (escanea archivos al abrirlos) y definiciones de virus (base de datos de amenazas conocidas). Cuando instalas un antivirus como Kaspersky, Norton o Bitdefender, Defender se desactiva automaticamente para evitar conflictos. Esto es normal — tu antivirus de terceros asume la proteccion.",
            },
            "term_arp_title": {"en": "ARP Spoofing", "es": "ARP Spoofing"},
            "term_arp_desc": {
                "en": "ARP (Address Resolution Protocol) maps IP addresses to hardware (MAC) addresses on your local network. In ARP spoofing, an attacker sends fake ARP messages to associate their MAC address with your router's IP, allowing them to intercept your traffic (man-in-the-middle attack). Flushing the ARP cache removes potentially poisoned entries.",
                "es": "ARP (Address Resolution Protocol) asocia direcciones IP con direcciones hardware (MAC) en tu red local. En ARP spoofing, un atacante envia mensajes ARP falsos para asociar su direccion MAC con la IP de tu router, permitiendole interceptar tu trafico (ataque man-in-the-middle). Limpiar la cache ARP elimina entradas potencialmente envenenadas.",
            },
            "term_dns_title": {"en": "DNS Cache", "es": "Cache DNS"},
            "term_dns_desc": {
                "en": "DNS (Domain Name System) translates website names (e.g. google.com) to IP addresses. Your system caches these translations for speed. Flushing the DNS cache forces your system to re-resolve all domain names, which can fix connectivity issues and remove any poisoned entries that redirect you to malicious sites.",
                "es": "DNS (Domain Name System) traduce nombres de sitios web (ej. google.com) a direcciones IP. Tu sistema almacena estas traducciones en cache para mayor velocidad. Limpiar la cache DNS fuerza a tu sistema a resolver todos los dominios de nuevo, lo que puede arreglar problemas de conectividad y eliminar entradas envenenadas que te redirigen a sitios maliciosos.",
            },
            "term_ports_title": {"en": "Network Ports", "es": "Puertos de Red"},
            "term_ports_desc": {
                "en": "Ports are virtual endpoints for network communication. A port in LISTEN state accepts incoming connections. SYSTEM ports (53-DNS, 135-RPC, 445-SMB) are essential for Windows and cannot be blocked without causing crashes. HIGH risk ports (like RDP-3389, database ports) can be exploited by attackers. Blocking unused ports reduces your attack surface.",
                "es": "Los puertos son puntos de acceso virtuales para comunicacion de red. Un puerto en estado LISTEN acepta conexiones entrantes. Los puertos SYSTEM (53-DNS, 135-RPC, 445-SMB) son esenciales para Windows y no se pueden bloquear sin causar fallos. Los puertos de riesgo ALTO (como RDP-3389, puertos de base de datos) pueden ser explotados por atacantes. Bloquear puertos no usados reduce tu superficie de ataque.",
            },
            "term_antivirus_title": {"en": "Antivirus Status", "es": "Estado del Antivirus"},
            "term_antivirus_desc": {
                "en": "WinSvalinn reads the antivirus status from Windows Security Center (WMI). The productState code indicates if the antivirus is enabled and if its definitions are up to date. When Kaspersky or another suite is active, it takes over firewall and real-time protection from Windows Defender. WinSvalinn detects this and adjusts its recommendations accordingly.",
                "es": "WinSvalinn lee el estado del antivirus desde el Centro de Seguridad de Windows (WMI). El codigo productState indica si el antivirus esta activo y si sus definiciones estan actualizadas. Cuando Kaspersky u otra suite esta activa, asume el control del firewall y la proteccion en tiempo real de Windows Defender. WinSvalinn detecta esto y ajusta sus recomendaciones.",
            },
            "term_processes_title": {"en": "Process Analysis", "es": "Analisis de Procesos"},
            "term_processes_desc": {
                "en": "WinSvalinn analyzes running processes for suspicious behavior: hidden windows, high CPU usage, unusual file locations (like Temp folders), processes mimicking system names, or processes with no visible window running from unusual paths. HIGH risk means multiple red flags; MEDIUM means some suspicious characteristics. Windows system processes (svchost, csrss, lsass, etc.) are automatically whitelisted.",
                "es": "WinSvalinn analiza procesos en ejecucion buscando comportamiento sospechoso: ventanas ocultas, alto uso de CPU, ubicaciones inusuales (como carpetas Temp), procesos que imitan nombres del sistema, o procesos sin ventana visible ejecutandose desde rutas inusuales. Riesgo ALTO significa multiples indicadores; MEDIO significa algunas caracteristicas sospechosas. Los procesos del sistema Windows (svchost, csrss, lsass, etc.) se excluyen automaticamente.",
            },
            "term_tasks_title": {"en": "Scheduled Tasks", "es": "Tareas Programadas"},
            "term_tasks_desc": {
                "en": "Windows Task Scheduler runs programs at specific times or events. Malware often creates scheduled tasks to persist after reboot. WinSvalinn flags tasks that run from suspicious locations (Temp, AppData), have obfuscated commands, or were recently created by unknown publishers.",
                "es": "El Programador de Tareas de Windows ejecuta programas en momentos o eventos especificos. El malware a menudo crea tareas programadas para persistir despues de reiniciar. WinSvalinn marca tareas que se ejecutan desde ubicaciones sospechosas (Temp, AppData), tienen comandos ofuscados, o fueron creadas recientemente por editores desconocidos.",
            },
            # Optimization terms
            "term_ram_trim_title": {
                "en": "RAM Working Set Trim",
                "es": "Recorte de Working Set RAM",
            },
            "term_ram_trim_desc": {
                "en": "Each process has a 'working set' — the RAM pages it's actively using. Trimming forces processes to release RAM they allocated but aren't actively using. Windows can reclaim this memory for other applications. This also flushes DNS cache, thumbnail cache, and font cache to free additional memory.",
                "es": "Cada proceso tiene un 'working set' — las paginas de RAM que esta usando activamente. El recorte fuerza a los procesos a liberar RAM que reservaron pero no estan usando activamente. Windows puede recuperar esta memoria para otras aplicaciones. Tambien limpia cache DNS, cache de miniaturas y cache de fuentes para liberar memoria adicional.",
            },
            "term_gc_title": {"en": ".NET Garbage Collection", "es": "Recoleccion de Basura .NET"},
            "term_gc_desc": {
                "en": "Many Windows applications use .NET framework, which manages memory automatically. Garbage Collection (GC) finds and frees memory that applications allocated but no longer reference. Triggering GC system-wide can reclaim memory from .NET applications that haven't cleaned up after themselves.",
                "es": "Muchas aplicaciones de Windows usan el framework .NET, que gestiona la memoria automaticamente. La Recoleccion de Basura (GC) encuentra y libera memoria que las aplicaciones reservaron pero ya no referencian. Activar GC a nivel de sistema puede recuperar memoria de aplicaciones .NET que no han limpiado despues de usarla.",
            },
            "term_gpu_tweaks_title": {"en": "GPU Registry Tweaks", "es": "Ajustes de Registro GPU"},
            "term_gpu_tweaks_desc": {
                "en": "GPU drivers store performance settings in the Windows Registry. WinSvalinn auto-detects your GPU brand (NVIDIA, AMD, or Intel) and applies brand-specific tweaks: maximum performance mode, larger shader cache, disabled overlays and telemetry, optimized power management, and threaded optimization. These changes prioritize performance over power saving.",
                "es": "Los drivers de GPU almacenan configuraciones de rendimiento en el Registro de Windows. WinSvalinn auto-detecta tu marca de GPU (NVIDIA, AMD o Intel) y aplica ajustes especificos: modo de rendimiento maximo, cache de shaders mayor, overlays y telemetria desactivados, gestion de energia optimizada y optimizacion multihilo. Estos cambios priorizan el rendimiento sobre el ahorro de energia.",
            },
            "term_visual_title": {"en": "Visual Effects", "es": "Efectos Visuales"},
            "term_visual_desc": {
                "en": "Windows uses animations, shadows, transparency, and smooth scrolling for visual appeal. Switching to 'Performance' mode disables these effects, freeing CPU and GPU resources. The visual difference is minimal on modern hardware, but it can help on older systems or when gaming.",
                "es": "Windows usa animaciones, sombras, transparencia y scroll suave para un aspecto visual atractivo. Cambiar al modo 'Rendimiento' desactiva estos efectos, liberando recursos de CPU y GPU. La diferencia visual es minima en hardware moderno, pero puede ayudar en sistemas antiguos o al jugar.",
            },
            "term_power_title": {"en": "Power Plan", "es": "Plan de Energia"},
            "term_power_desc": {
                "en": "Windows power plans control how your CPU, disk, and display balance performance vs energy savings. 'Balanced' throttles CPU when idle; 'High Performance' keeps CPU at full speed; 'Ultimate Performance' (Windows 10 Pro/Enterprise) eliminates all power-saving delays for maximum responsiveness.",
                "es": "Los planes de energia de Windows controlan como tu CPU, disco y pantalla equilibran rendimiento vs ahorro de energia. 'Equilibrado' reduce la CPU en reposo; 'Alto Rendimiento' mantiene la CPU a maxima velocidad; 'Maximo Rendimiento' (Windows 10 Pro/Enterprise) elimina todos los retrasos de ahorro de energia para maxima capacidad de respuesta.",
            },
            "term_ssd_title": {"en": "SSD Optimization", "es": "Optimizacion SSD"},
            "term_ssd_desc": {
                "en": "SSDs (Solid State Drives) work differently from HDDs. TRIM tells the SSD which blocks are no longer in use, maintaining write performance. Superfetch (SysMain) pre-loads programs into RAM — useful for HDDs but unnecessary for SSDs since they're already fast. Disabling last-access timestamps reduces unnecessary writes, extending SSD lifespan.",
                "es": "Los SSD (Unidades de Estado Solido) funcionan diferente a los HDD. TRIM indica al SSD que bloques ya no se usan, manteniendo el rendimiento de escritura. Superfetch (SysMain) pre-carga programas en RAM — util para HDD pero innecesario para SSD ya que son rapidos. Desactivar timestamps de ultimo acceso reduce escrituras innecesarias, alargando la vida del SSD.",
            },
            "term_prefetch_title": {"en": "Prefetch / Superfetch", "es": "Prefetch / Superfetch"},
            "term_prefetch_desc": {
                "en": "Prefetch monitors which files are loaded at boot and during app launches, then pre-reads them in subsequent boots for faster loading. Superfetch (SysMain) extends this by preloading frequently used apps into RAM. Setting Prefetch to level 3 enables both boot and application prefetching for optimal performance.",
                "es": "Prefetch monitoriza que archivos se cargan al arrancar y al iniciar apps, y luego los pre-lee en arranques posteriores para carga mas rapida. Superfetch (SysMain) extiende esto precargando apps frecuentes en RAM. Establecer Prefetch en nivel 3 activa tanto prefetching de arranque como de aplicaciones para rendimiento optimo.",
            },
            "term_startup_title": {"en": "Startup Programs", "es": "Programas de Inicio"},
            "term_startup_desc": {
                "en": "Programs registered in the Windows Registry or Startup folders auto-run when you log in. Each program adds seconds to your boot time and consumes RAM. System programs (Windows Security, ctfmon) are essential and should not be disabled. Hardware drivers (NVIDIA, Realtek) may need to run for proper device function. External apps (Spotify, Discord, Steam) can safely be disabled — they'll still work when launched manually.",
                "es": "Los programas registrados en el Registro de Windows o carpetas de Inicio se ejecutan automaticamente al iniciar sesion. Cada programa agrega segundos al tiempo de arranque y consume RAM. Los programas del sistema (Windows Security, ctfmon) son esenciales y no deben desactivarse. Los controladores de hardware (NVIDIA, Realtek) pueden necesitar ejecutarse para el funcionamiento correcto del dispositivo. Las apps externas (Spotify, Discord, Steam) se pueden desactivar sin problema — seguiran funcionando al abrirlas manualmente.",
            },
            # ── Plugins ──────────────────────────────────────────────
            "section_plugins": {"en": "PLUGINS", "es": "PLUGINS"},
            "nav_plugins_home": {"en": "Plugins Panel", "es": "Panel Plugins"},
            "select_plugin_file": {
                "en": "Select plugin file (.py)",
                "es": "Seleccionar archivo de plugin (.py)",
            },
            "loading_plugin": {"en": "Loading plugin...", "es": "Cargando plugin..."},
            "plugin_loaded_ok": {
                "en": "Plugin loaded successfully",
                "es": "Plugin cargado exitosamente",
            },
            "plugin_load_error": {"en": "Error loading plugin", "es": "Error al cargar plugin"},
            "plugin_removed": {"en": "Plugin removed", "es": "Plugin eliminado"},
            "plugin_remove": {"en": "Remove", "es": "Eliminar"},
            "plugin_apply_all": {
                "en": "Apply All Optimizations",
                "es": "Aplicar Todas las Optimizaciones",
            },
            "plugin_recommended_settings": {
                "en": "Recommended Settings",
                "es": "Ajustes Recomendados",
            },
            "plugins_home_title": {"en": "Plugins", "es": "Plugins"},
            "plugins_home_subtitle": {
                "en": "Extend WinSvalinn with custom optimization plugins",
                "es": "Extiende WinSvalinn con plugins de optimizacion personalizados",
            },
            "plugins_none_loaded": {
                "en": "No plugins loaded yet. Click the button below to add one.",
                "es": "No hay plugins cargados. Haz clic en el boton de abajo para agregar uno.",
            },
            "plugins_add_new": {"en": "Add Plugin", "es": "Agregar Plugin"},
            "plugins_open": {"en": "Open", "es": "Abrir"},
            "plugins_loaded_section": {"en": "Active Plugins", "es": "Plugins Activos"},
            "plugins_active_badge": {"en": "ACTIVE", "es": "ACTIVO"},
            "plugins_available_section": {
                "en": "Available Plugins (auto-detected)",
                "es": "Plugins Disponibles (auto-detectados)",
            },
            "plugins_available_desc": {
                "en": "These plugins were found in the plugins/ folder. Click Install to activate.",
                "es": "Estos plugins se encontraron en la carpeta plugins/. Haz clic en Instalar para activar.",
            },
            "plugins_install": {"en": "Install", "es": "Instalar"},
            "plugins_add_external": {
                "en": "Browse for external plugin file...",
                "es": "Buscar archivo de plugin externo...",
            },
            "plugins_how_title": {"en": "How to use plugins", "es": "Como usar plugins"},
            "plugins_how_desc": {
                "en": "Plugins are .py files that add new optimization panels to WinSvalinn. Click 'Add Plugin' and select a plugin file (e.g. plugin_lol.py or plugin_streaming.py). Each plugin provides its own set of optimisation cards. Loaded plugins are remembered between sessions.",
                "es": "Los plugins son archivos .py que agregan nuevos paneles de optimizacion a WinSvalinn. Haz clic en 'Agregar Plugin' y selecciona un archivo de plugin (ej. plugin_lol.py o plugin_streaming.py). Cada plugin proporciona su propio conjunto de tarjetas de optimizacion. Los plugins cargados se recuerdan entre sesiones.",
            },
            # ── AI Windows Removal ───────────────────────────────────
            "nav_ai_windows": {"en": "AI Windows Removal", "es": "Eliminar IA de Windows"},
            "ai_windows_title": {"en": "AI Windows Removal", "es": "Eliminacion de IA de Windows"},
            "ai_windows_subtitle": {
                "en": "Detect and remove ALL Windows AI features (Copilot, Recall, etc.)",
                "es": "Detecta y elimina TODAS las caracteristicas de IA de Windows (Copilot, Recall, etc.)",
            },
            "ai_windows_warning": {
                "en": "This will disable Windows Copilot, Recall, AI Search, and all AI telemetry. Some features require administrator privileges. Changes can affect system functionality.",
                "es": "Esto desactivara Windows Copilot, Recall, Busqueda IA, y toda la telemetria de IA. Algunas funciones requieren privilegios de administrador. Los cambios pueden afectar la funcionalidad del sistema.",
            },
            "scan_ai_features": {"en": "Scan AI Features", "es": "Escanear IA"},
            "remove_all_ai": {"en": "Remove ALL AI", "es": "Eliminar TODA la IA"},
            "ai_scan_results": {"en": "Scan Results", "es": "Resultados del Escaneo"},
            "ai_activity_log": {"en": "Activity Log", "es": "Registro de Actividad"},
            "ai_ready_to_scan": {
                "en": "Ready. Click 'Scan AI Features' to detect Windows AI.",
                "es": "Listo. Haz clic en 'Escanear IA' para detectar IA de Windows.",
            },
            "ai_scanning": {
                "en": "Scanning for AI features...",
                "es": "Escaneando caracteristicas de IA...",
            },
            "ai_removing": {
                "en": "Removing AI features...",
                "es": "Eliminando caracteristicas de IA...",
            },
            "ai_remove_individual": {"en": "Remove", "es": "Eliminar"},
            # Individual AI features
            "ai_copilot_name": {"en": "Windows Copilot", "es": "Windows Copilot"},
            "ai_copilot_desc": {
                "en": "Microsoft's AI assistant integrated into Windows 11. Uses cloud services and telemetry.",
                "es": "Asistente de IA de Microsoft integrado en Windows 11. Usa servicios en la nube y telemetria.",
            },
            "ai_recall_name": {"en": "Windows Recall", "es": "Windows Recall"},
            "ai_recall_desc": {
                "en": "AI feature that takes screenshots of everything you do. Major privacy concern.",
                "es": "Caracteristica de IA que toma capturas de todo lo que haces. Gran problema de privacidad.",
            },
            "ai_suggested_actions_name": {"en": "Suggested Actions", "es": "Acciones Sugeridas"},
            "ai_suggested_actions_desc": {
                "en": "AI-powered suggestions when copying phone numbers, dates, etc. Sends data to cloud.",
                "es": "Sugerencias basadas en IA al copiar numeros de telefono, fechas, etc. Envia datos a la nube.",
            },
            "ai_live_captions_name": {"en": "Live Captions", "es": "Subtitulos en Vivo"},
            "ai_live_captions_desc": {
                "en": "AI transcription of system audio. Constantly monitors all audio output.",
                "es": "Transcripcion de IA del audio del sistema. Monitorea constantemente toda la salida de audio.",
            },
            "ai_voice_access_name": {"en": "Voice Access", "es": "Acceso por Voz"},
            "ai_voice_access_desc": {
                "en": "Voice control for Windows. Requires constant microphone access.",
                "es": "Control por voz para Windows. Requiere acceso constante al microfono.",
            },
            "ai_widgets_name": {"en": "AI Widgets", "es": "Widgets de IA"},
            "ai_widgets_desc": {
                "en": "Windows 11 widget panel with AI-powered news and recommendations. Uses telemetry.",
                "es": "Panel de widgets de Windows 11 con noticias y recomendaciones basadas en IA. Usa telemetria.",
            },
            "ai_search_name": {"en": "AI Search", "es": "Busqueda IA"},
            "ai_search_desc": {
                "en": "AI-enhanced search in Windows. Sends search queries to Microsoft servers.",
                "es": "Busqueda mejorada con IA en Windows. Envia consultas de busqueda a servidores de Microsoft.",
            },
            "ai_telemetry_name": {"en": "AI Telemetry", "es": "Telemetria de IA"},
            "ai_telemetry_desc": {
                "en": "Data collection for AI feature improvement. Continuously sends usage data to Microsoft.",
                "es": "Recoleccion de datos para mejorar caracteristicas de IA. Envia continuamente datos de uso a Microsoft.",
            },
            "ai_cortana_name": {"en": "Cortana", "es": "Cortana"},
            "ai_cortana_desc": {
                "en": "Microsoft's legacy AI assistant. Still runs background processes even when 'disabled'.",
                "es": "Asistente de IA legacy de Microsoft. Aun ejecuta procesos en segundo plano aunque este 'desactivado'.",
            },
            # AI Status indicators
            "ai_status_active": {"en": "ACTIVE", "es": "ACTIVO"},
            "ai_status_inactive": {"en": "INACTIVE", "es": "INACTIVO"},
            "ai_removal_success": {
                "en": "AI feature removed successfully",
                "es": "Caracteristica de IA eliminada exitosamente",
            },
            "ai_removal_failed": {
                "en": "Failed to remove AI feature",
                "es": "Fallo al eliminar caracteristica de IA",
            },
            "ai_features_found": {
                "en": "AI features found",
                "es": "caracteristicas de IA encontradas",
            },
            "ai_no_features": {
                "en": "No active AI features detected. Your system is AI-free!",
                "es": "No se detectaron caracteristicas de IA activas. Tu sistema esta libre de IA!",
            },
            "ai_warning_admin": {
                "en": "Some AI removal operations require Administrator privileges",
                "es": "Algunas operaciones de eliminacion de IA requieren privilegios de Administrador",
            },
            "ai_confirm_remove_all": {
                "en": "Are you sure you want to remove ALL Windows AI features? This action requires administrator privileges and cannot be easily undone.",
                "es": "Estas seguro de que quieres eliminar TODAS las caracteristicas de IA de Windows? Esta accion requiere privilegios de administrador y no se puede deshacer facilmente.",
            },
            # ── Advanced Privacy & Optimization ──────────────────────
            "section_advanced": {"en": "ADVANCED", "es": "AVANZADO"},
            "nav_advanced_privacy": {"en": "Advanced Privacy", "es": "Privacidad Avanzada"},
            "nav_advanced_security": {"en": "Advanced Security", "es": "Seguridad Avanzada"},
            "advanced_privacy_title": {
                "en": "Advanced Privacy & Optimization",
                "es": "Privacidad y Optimizacion Avanzada",
            },
            "advanced_privacy_subtitle": {
                "en": "Advanced tools for telemetry blocking, bloatware removal, and system control",
                "es": "Herramientas avanzadas para bloquear telemetria, eliminar bloatware y controlar el sistema",
            },
            "advanced_security_title": {"en": "Advanced Security", "es": "Seguridad Avanzada"},
            "advanced_security_subtitle": {
                "en": "Advanced Windows Defender, Firewall, Hardening, and Security Audit tools",
                "es": "Herramientas avanzadas de Windows Defender, Firewall, Hardening y Auditoria de Seguridad",
            },
            # ── Defender Control ──────────────────────────────────────
            "defender_title": {
                "en": "Windows Defender Control",
                "es": "Control de Windows Defender",
            },
            "defender_desc": {
                "en": "Monitor and manage Windows Defender settings",
                "es": "Monitorea y gestiona la configuracion de Windows Defender",
            },
            "defender_status": {"en": "Defender Status", "es": "Estado de Defender"},
            "defender_toggle_realtime": {
                "en": "Toggle Real-time Protection",
                "es": "Alternar Proteccion en Tiempo Real",
            },
            "defender_quick_scan": {"en": "Quick Scan", "es": "Escaneo Rapido"},
            "defender_update_defs": {"en": "Update Definitions", "es": "Actualizar Definiciones"},
            # ── Firewall Manager ──────────────────────────────────────
            "firewall_title": {"en": "Firewall Manager", "es": "Gestor de Firewall"},
            "firewall_desc": {
                "en": "Manage Windows Firewall profiles and rules",
                "es": "Gestiona perfiles y reglas del Firewall de Windows",
            },
            "firewall_status": {"en": "Firewall Status", "es": "Estado del Firewall"},
            "firewall_enable": {"en": "Enable Firewall", "es": "Habilitar Firewall"},
            "firewall_disable": {"en": "Disable Firewall", "es": "Deshabilitar Firewall"},
            "firewall_rules": {"en": "Firewall Rules", "es": "Reglas del Firewall"},
            # ── Security Hardening ────────────────────────────────────
            "hardening_title": {"en": "Security Hardening", "es": "Hardening de Seguridad"},
            "hardening_desc": {
                "en": "Disable risky Windows features (AutoRun, RDP, SMBv1, etc.)",
                "es": "Deshabilita caracteristicas riesgosas de Windows (AutoRun, RDP, SMBv1, etc.)",
            },
            "hardening_scan": {"en": "Scan Settings", "es": "Escanear Configuracion"},
            "hardening_apply": {"en": "Apply Hardening", "es": "Aplicar Hardening"},
            # ── Security Audit ────────────────────────────────────────
            "audit_title": {"en": "Security Audit", "es": "Auditoria de Seguridad"},
            "audit_desc": {
                "en": "Comprehensive security audit (Defender, Firewall, BitLocker, TPM, etc.)",
                "es": "Auditoria de seguridad completa (Defender, Firewall, BitLocker, TPM, etc.)",
            },
            "audit_run": {"en": "Run Audit", "es": "Ejecutar Auditoria"},
            "audit_results": {"en": "Audit Results", "es": "Resultados de Auditoria"},
            # ── Telemetry Blocker ────────────────────────────────────
            "telemetry_title": {
                "en": "Windows Telemetry Blocker",
                "es": "Bloqueador de Telemetria de Windows",
            },
            "telemetry_desc": {
                "en": "Block Microsoft telemetry and tracking services",
                "es": "Bloquea servicios de telemetria y seguimiento de Microsoft",
            },
            "telemetry_scan": {"en": "Scan Telemetry", "es": "Escanear Telemetria"},
            "telemetry_block_all": {
                "en": "Block All Telemetry",
                "es": "Bloquear Toda la Telemetria",
            },
            "telemetry_active": {"en": "Active", "es": "Activo"},
            "telemetry_blocked": {"en": "Blocked", "es": "Bloqueado"},
            "telemetry_components": {
                "en": "Telemetry Components",
                "es": "Componentes de Telemetria",
            },
            # ── Bloatware Remover ────────────────────────────────────
            "bloatware_title": {"en": "Bloatware Remover", "es": "Removedor de Bloatware"},
            "bloatware_desc": {
                "en": "Remove pre-installed bloatware and UWP apps",
                "es": "Elimina bloatware preinstalado y aplicaciones UWP",
            },
            "bloatware_scan": {"en": "Scan Apps", "es": "Escanear Apps"},
            "bloatware_remove_safe": {"en": "Remove Safe Apps", "es": "Eliminar Apps Seguras"},
            "bloatware_remove_all": {"en": "Remove All", "es": "Eliminar Todas"},
            "bloatware_detected": {"en": "Bloatware Detected", "es": "Bloatware Detectado"},
            "bloatware_safe": {"en": "Safe to remove", "es": "Seguro eliminar"},
            # ── Hosts Manager ────────────────────────────────────────
            "hosts_title": {"en": "Hosts File Manager", "es": "Gestor de Archivo Hosts"},
            "hosts_desc": {
                "en": "Block ads and tracking at DNS level using hosts file",
                "es": "Bloquea anuncios y seguimiento a nivel DNS usando el archivo hosts",
            },
            "hosts_backup": {"en": "Backup Hosts", "es": "Backup del Hosts"},
            "hosts_block_telemetry": {"en": "Block Telemetry", "es": "Bloquear Telemetria"},
            "hosts_block_ads": {"en": "Block Ads", "es": "Bloquear Ads"},
            "hosts_block_all": {"en": "Block All", "es": "Bloquear Todo"},
            "hosts_restore": {"en": "Restore Backup", "es": "Restaurar Backup"},
            "hosts_entries": {"en": "Hosts Entries", "es": "Entradas del Hosts"},
            # ── DNS Manager ──────────────────────────────────────────
            "dns_title": {"en": "DNS Manager", "es": "Gestor de DNS"},
            "dns_desc": {
                "en": "Configure DNS servers for privacy and performance",
                "es": "Configura servidores DNS para privacidad y rendimiento",
            },
            "dns_current": {"en": "Current DNS", "es": "DNS Actual"},
            "dns_presets": {"en": "DNS Presets", "es": "DNS Preconfigurados"},
            "dns_cloudflare": {"en": "Cloudflare (1.1.1.1)", "es": "Cloudflare (1.1.1.1)"},
            "dns_google": {"en": "Google (8.8.8.8)", "es": "Google (8.8.8.8)"},
            "dns_quad9": {"en": "Quad9 (9.9.9.9)", "es": "Quad9 (9.9.9.9)"},
            "dns_adguard": {"en": "AdGuard DNS", "es": "AdGuard DNS"},
            "dns_auto": {"en": "Automatic (DHCP)", "es": "Automatico (DHCP)"},
            "dns_flush": {"en": "Flush DNS Cache", "es": "Limpiar Cache DNS"},
            # ── Package Manager ──────────────────────────────────────
            "packages_title": {
                "en": "Package Manager (winget)",
                "es": "Gestor de Paquetes (winget)",
            },
            "packages_desc": {
                "en": "Install, update, and remove software packages",
                "es": "Instala, actualiza y elimina paquetes de software",
            },
            "packages_check_winget": {"en": "Check winget", "es": "Verificar winget"},
            "packages_list": {"en": "List Installed", "es": "Listar Instalados"},
            "packages_updates": {"en": "Check Updates", "es": "Ver Actualizaciones"},
            "packages_update_all": {"en": "Update All", "es": "Actualizar Todo"},
            "packages_search": {"en": "Search Packages", "es": "Buscar Paquetes"},
            "packages_install": {"en": "Install", "es": "Instalar"},
            "packages_uninstall": {"en": "Uninstall", "es": "Desinstalar"},
            # ── Update Control ───────────────────────────────────────
            "updates_title": {"en": "Windows Update Control", "es": "Control de Windows Update"},
            "updates_desc": {
                "en": "Manage Windows Update settings and behavior",
                "es": "Gestiona configuracion y comportamiento de Windows Update",
            },
            "updates_status": {"en": "Update Status", "es": "Estado de Updates"},
            "updates_pause": {"en": "Pause Updates", "es": "Pausar Updates"},
            "updates_resume": {"en": "Resume Updates", "es": "Reanudar Updates"},
            "updates_disable": {"en": "Disable Auto Updates", "es": "Deshabilitar Updates Auto"},
            "updates_enable": {"en": "Enable Auto Updates", "es": "Habilitar Updates Auto"},
            "updates_check": {"en": "Check for Updates", "es": "Buscar Updates"},
            "updates_paused": {"en": "Paused", "es": "Pausado"},
            "updates_active": {"en": "Active", "es": "Activo"},
            # ── Features Manager ─────────────────────────────────────
            "features_title": {
                "en": "Windows Features Manager",
                "es": "Gestor de Caracteristicas de Windows",
            },
            "features_desc": {
                "en": "Enable or disable Windows optional features",
                "es": "Habilita o deshabilita caracteristicas opcionales de Windows",
            },
            "features_list": {"en": "List Features", "es": "Listar Caracteristicas"},
            "features_enable": {"en": "Enable", "es": "Habilitar"},
            "features_disable": {"en": "Disable", "es": "Deshabilitar"},
            "features_wsl2": {"en": "Enable WSL2", "es": "Habilitar WSL2"},
            "features_hyperv": {"en": "Enable Hyper-V", "es": "Habilitar Hyper-V"},
            "features_sandbox": {"en": "Enable Windows Sandbox", "es": "Habilitar Windows Sandbox"},
            "features_restart_required": {"en": "Restart Required", "es": "Reinicio Requerido"},
            # ── Common Actions ───────────────────────────────────────
            "action_scan": {"en": "Scan", "es": "Escanear"},
            "action_apply": {"en": "Apply", "es": "Aplicar"},
            "action_fix": {"en": "Fix", "es": "Reparar"},
            "action_block": {"en": "Block", "es": "Bloquear"},
            "action_remove": {"en": "Remove", "es": "Eliminar"},
            "action_enable": {"en": "Enable", "es": "Habilitar"},
            "action_disable": {"en": "Disable", "es": "Deshabilitar"},
            "action_backup": {"en": "Backup", "es": "Backup"},
            "action_restore": {"en": "Restore", "es": "Restaurar"},
            # ── Status Messages ──────────────────────────────────────
            "status_scanning": {"en": "Scanning...", "es": "Escaneando..."},
            "status_applying": {"en": "Applying...", "es": "Aplicando..."},
            "status_success": {"en": "Success", "es": "Exito"},
            "status_error": {"en": "Error", "es": "Error"},
            "status_warning": {"en": "Warning", "es": "Advertencia"},
            "status_complete": {"en": "Complete", "es": "Completado"},
            "status_failed": {"en": "Failed", "es": "Fallido"},
            # ── Confirmations ────────────────────────────────────────
            "confirm_block_telemetry": {
                "en": "Block all Windows telemetry?",
                "es": "Bloquear toda la telemetria de Windows?",
            },
            "confirm_remove_bloatware": {
                "en": "Remove all bloatware apps?",
                "es": "Eliminar todas las apps de bloatware?",
            },
            "confirm_disable_updates": {
                "en": "Disable automatic Windows Updates? This prevents security updates!",
                "es": "Deshabilitar Windows Updates automaticos? Esto previene actualizaciones de seguridad!",
            },
            "confirm_restart": {
                "en": "Some changes require a restart. Restart now?",
                "es": "Algunos cambios requieren reinicio. Reiniciar ahora?",
            },
            # ══════════════════════════════════════════════════════════
            #  ADVANCED SECURITY (advsec_*) — prefixed keys
            # ══════════════════════════════════════════════════════════
            # -- Main view ---------------------------------------------------
            "advsec_title": {"en": "Advanced Security", "es": "Seguridad Avanzada"},
            "advsec_subtitle": {
                "en": "Windows Defender, Firewall, Hardening and Security Audit",
                "es": "Windows Defender, Firewall, Hardening y Auditoria de Seguridad",
            },
            "advsec_activity_log": {"en": "Activity Log", "es": "Registro de Actividad"},
            # -- Tabs --------------------------------------------------------
            "advsec_tab_defender": {"en": "Defender", "es": "Defender"},
            "advsec_tab_firewall": {"en": "Firewall", "es": "Firewall"},
            "advsec_tab_hardening": {"en": "Hardening", "es": "Hardening"},
            "advsec_tab_audit": {"en": "Audit", "es": "Auditoria"},
            # -- Status labels -----------------------------------------------
            "advsec_active": {"en": "ACTIVE", "es": "ACTIVO"},
            "advsec_inactive": {"en": "INACTIVE", "es": "INACTIVO"},
            "advsec_warning": {"en": "Warning", "es": "Advertencia"},
            "advsec_confirm": {"en": "Confirm", "es": "Confirmar"},
            "advsec_critical_warning": {"en": "Critical Warning", "es": "Advertencia Critica"},
            # -- Defender section --------------------------------------------
            "advsec_defender_title": {
                "en": "Windows Defender Control",
                "es": "Control de Windows Defender",
            },
            "advsec_defender_desc": {
                "en": "Monitor and manage Windows Defender real-time protection, virus scanning, and definitions.",
                "es": "Monitorea y gestiona la proteccion en tiempo real, escaneo de virus y definiciones de Windows Defender.",
            },
            "advsec_check_status": {"en": "Check Status", "es": "Verificar Estado"},
            "advsec_quick_scan": {"en": "Quick Scan", "es": "Escaneo Rapido"},
            "advsec_update_defs": {"en": "Update Definitions", "es": "Actualizar Definiciones"},
            "advsec_enable_rt": {
                "en": "Enable Real-Time Protection",
                "es": "Activar Proteccion en Tiempo Real",
            },
            "advsec_disable_rt": {"en": "Disable Real-Time", "es": "Desactivar Tiempo Real"},
            "advsec_ransomware": {
                "en": "Toggle Ransomware Prot.",
                "es": "Alternar Prot. Ransomware",
            },
            "advsec_real_time": {"en": "Real-Time Protection", "es": "Proteccion en Tiempo Real"},
            "advsec_av_enabled": {"en": "Antivirus Enabled", "es": "Antivirus Habilitado"},
            "advsec_ransomware_prot": {
                "en": "Ransomware Protection",
                "es": "Proteccion Ransomware",
            },
            "advsec_smartscreen": {"en": "SmartScreen", "es": "SmartScreen"},
            "advsec_tamper_prot": {
                "en": "Tamper Protection",
                "es": "Proteccion contra Manipulacion",
            },
            "advsec_confirm_quick_scan": {
                "en": "Run a quick Windows Defender scan now?",
                "es": "Ejecutar un escaneo rapido de Windows Defender ahora?",
            },
            "advsec_warn_disable_rt": {
                "en": "Disabling real-time protection leaves your system vulnerable to threats. Are you sure?",
                "es": "Desactivar la proteccion en tiempo real deja tu sistema vulnerable a amenazas. Estas seguro?",
            },
            # -- Firewall section --------------------------------------------
            "advsec_firewall_title": {"en": "Firewall Management", "es": "Gestion de Firewall"},
            "advsec_firewall_desc": {
                "en": "View and manage Windows Firewall profiles and rules for all network types.",
                "es": "Visualiza y gestiona los perfiles y reglas del Firewall de Windows para todos los tipos de red.",
            },
            "advsec_enable_firewall": {"en": "Enable Firewall", "es": "Activar Firewall"},
            "advsec_disable_firewall": {"en": "Disable Firewall", "es": "Desactivar Firewall"},
            "advsec_list_rules": {"en": "List Rules", "es": "Listar Reglas"},
            "advsec_profile_domain": {"en": "Domain Profile", "es": "Perfil de Dominio"},
            "advsec_profile_private": {"en": "Private Profile", "es": "Perfil Privado"},
            "advsec_profile_public": {"en": "Public Profile", "es": "Perfil Publico"},
            "advsec_warn_disable_fw": {
                "en": "Disabling the firewall removes all network protection. Your system will be exposed to attacks. Are you sure?",
                "es": "Desactivar el firewall elimina toda la proteccion de red. Tu sistema quedara expuesto a ataques. Estas seguro?",
            },
            # -- Hardening section -------------------------------------------
            "advsec_hardening_title": {"en": "Security Hardening", "es": "Hardening de Seguridad"},
            "advsec_hardening_desc": {
                "en": "Harden Windows by disabling risky features like AutoRun, RDP, SMBv1, and adjusting UAC levels.",
                "es": "Fortalece Windows desactivando caracteristicas riesgosas como AutoRun, RDP, SMBv1, y ajustando niveles de UAC.",
            },
            "advsec_autorun_label": {"en": "AutoRun / AutoPlay:", "es": "AutoRun / AutoPlay:"},
            "advsec_rdp_label": {"en": "Remote Desktop (RDP):", "es": "Escritorio Remoto (RDP):"},
            "advsec_smbv1_label": {"en": "SMBv1 Protocol:", "es": "Protocolo SMBv1:"},
            "advsec_smbv1_hint": {
                "en": "(used by WannaCry ransomware)",
                "es": "(usado por el ransomware WannaCry)",
            },
            "advsec_uac_label": {"en": "UAC Level:", "es": "Nivel de UAC:"},
            "advsec_disable_secure": {"en": "Disable (Secure)", "es": "Desactivar (Seguro)"},
            "advsec_enable_risky": {"en": "Enable (Risky)", "es": "Activar (Riesgoso)"},
            "advsec_disable_smbv1": {
                "en": "Disable SMBv1 Protocol",
                "es": "Desactivar Protocolo SMBv1",
            },
            "advsec_uac_max": {"en": "Maximum", "es": "Maximo"},
            "advsec_uac_normal": {"en": "Normal", "es": "Normal"},
            "advsec_uac_off": {"en": "Off (Unsafe)", "es": "Apagado (Inseguro)"},
            "advsec_uac_level_0": {
                "en": "Never notify - No UAC prompts (UNSAFE)",
                "es": "Nunca notificar - Sin avisos UAC (INSEGURO)",
            },
            "advsec_uac_level_1": {
                "en": "Notify only when apps make changes (no dim)",
                "es": "Notificar solo cuando las apps hacen cambios (sin oscurecer)",
            },
            "advsec_uac_level_2": {
                "en": "Notify only when apps make changes (default)",
                "es": "Notificar solo cuando las apps hacen cambios (por defecto)",
            },
            "advsec_uac_level_5": {
                "en": "Always notify - Maximum protection",
                "es": "Siempre notificar - Proteccion maxima",
            },
            "advsec_confirm_disable_smbv1": {
                "en": "Disable SMBv1 protocol? This may require a system restart. SMBv1 is a security risk used by WannaCry ransomware.",
                "es": "Desactivar protocolo SMBv1? Esto puede requerir reiniciar el sistema. SMBv1 es un riesgo de seguridad usado por el ransomware WannaCry.",
            },
            "advsec_warn_enable_autorun": {
                "en": "Enabling AutoRun allows programs on USB drives and CDs to run automatically. This is a security risk. Are you sure?",
                "es": "Activar AutoRun permite que los programas en unidades USB y CDs se ejecuten automaticamente. Esto es un riesgo de seguridad. Estas seguro?",
            },
            "advsec_warn_enable_rdp": {
                "en": "Enabling Remote Desktop allows remote connections to your PC. This can be exploited by attackers. Are you sure?",
                "es": "Activar Escritorio Remoto permite conexiones remotas a tu PC. Esto puede ser explotado por atacantes. Estas seguro?",
            },
            "advsec_warn_uac_off": {
                "en": "Disabling UAC completely removes all permission prompts. Malware can make system changes silently. This is extremely dangerous!",
                "es": "Desactivar UAC completamente elimina todos los avisos de permisos. El malware puede hacer cambios al sistema silenciosamente. Esto es extremadamente peligroso!",
            },
            "advsec_restart_required": {
                "en": "A system restart is required for changes to take effect.",
                "es": "Se requiere reiniciar el sistema para que los cambios surtan efecto.",
            },
            "advsec_restart_title": {"en": "Restart Required", "es": "Reinicio Requerido"},
            "advsec_restart_body": {
                "en": "A system restart is needed to complete this operation. Please save your work and restart Windows.",
                "es": "Se necesita reiniciar el sistema para completar esta operacion. Guarda tu trabajo y reinicia Windows.",
            },
            # -- Audit section -----------------------------------------------
            "advsec_audit_title": {"en": "Security Audit", "es": "Auditoria de Seguridad"},
            "advsec_audit_desc": {
                "en": "Run a comprehensive security scan covering Defender, Firewall, BitLocker, TPM, and more.",
                "es": "Ejecuta un escaneo de seguridad completo que cubre Defender, Firewall, BitLocker, TPM y mas.",
            },
            "advsec_run_scan": {"en": "Run Security Scan", "es": "Ejecutar Escaneo de Seguridad"},
            "advsec_bitlocker_status": {"en": "BitLocker Status", "es": "Estado de BitLocker"},
            "advsec_bitlocker_na": {
                "en": "BitLocker is not available or not supported on this system.",
                "es": "BitLocker no esta disponible o no es compatible con este sistema.",
            },
            "advsec_tpm_status": {"en": "TPM Status", "es": "Estado de TPM"},
            "advsec_tpm_absent": {
                "en": "No TPM module detected in this system.",
                "es": "No se detecto modulo TPM en este sistema.",
            },
            "advsec_tpm_not_ready": {
                "en": "TPM is present but not ready for use.",
                "es": "TPM esta presente pero no esta listo para usar.",
            },
            "advsec_critical_issues": {"en": "Critical Issues", "es": "Problemas Criticos"},
            "advsec_warnings": {"en": "Warnings", "es": "Advertencias"},
            "advsec_passed_checks": {"en": "Passed Checks", "es": "Verificaciones Aprobadas"},
            # -- Audit log messages ------------------------------------------
            "advsec_log_checking_defender": {
                "en": "Checking Windows Defender status...",
                "es": "Verificando estado de Windows Defender...",
            },
            "advsec_log_status_ok": {
                "en": "Defender status retrieved successfully.",
                "es": "Estado de Defender obtenido exitosamente.",
            },
            "advsec_log_quick_scan": {
                "en": "Starting quick scan with Windows Defender...",
                "es": "Iniciando escaneo rapido con Windows Defender...",
            },
            "advsec_log_updating_defs": {
                "en": "Updating virus definitions...",
                "es": "Actualizando definiciones de virus...",
            },
            "advsec_log_checking_firewall": {
                "en": "Checking firewall status...",
                "es": "Verificando estado del firewall...",
            },
            "advsec_log_fw_status_ok": {
                "en": "Firewall status retrieved successfully.",
                "es": "Estado del firewall obtenido exitosamente.",
            },
            "advsec_log_listing_rules": {
                "en": "Listing firewall rules...",
                "es": "Listando reglas del firewall...",
            },
            "advsec_log_no_rules": {
                "en": "No firewall rules found or unable to retrieve rules.",
                "es": "No se encontraron reglas de firewall o no se pudieron obtener.",
            },
            "advsec_log_disabling_smbv1": {
                "en": "Disabling SMBv1 protocol...",
                "es": "Desactivando protocolo SMBv1...",
            },
            "advsec_log_running_scan": {
                "en": "Running comprehensive security scan...",
                "es": "Ejecutando escaneo de seguridad completo...",
            },
            "advsec_log_checking_bitlocker": {
                "en": "Checking BitLocker encryption status...",
                "es": "Verificando estado de cifrado BitLocker...",
            },
            "advsec_log_checking_tpm": {
                "en": "Checking TPM module status...",
                "es": "Verificando estado del modulo TPM...",
            },
            # ══════════════════════════════════════════════════════════
            #  ADVANCED PRIVACY (advpriv_*) — prefixed keys
            # ══════════════════════════════════════════════════════════
            # -- Main view ---------------------------------------------------
            "advpriv_title": {
                "en": "Advanced Privacy & Optimization",
                "es": "Privacidad y Optimizacion Avanzada",
            },
            "advpriv_subtitle": {
                "en": "Telemetry blocking, bloatware removal, hosts, DNS, packages, updates and features management",
                "es": "Bloqueo de telemetria, eliminacion de bloatware, hosts, DNS, paquetes, actualizaciones y gestion de caracteristicas",
            },
            "advpriv_activity_log": {"en": "Activity Log", "es": "Registro de Actividad"},
            "advpriv_warning": {"en": "Warning", "es": "Advertencia"},
            "advpriv_confirm": {"en": "Confirm", "es": "Confirmar"},
            # -- Tabs --------------------------------------------------------
            "advpriv_tab_telemetry": {"en": "Telemetry", "es": "Telemetria"},
            "advpriv_tab_bloatware": {"en": "Bloatware", "es": "Bloatware"},
            "advpriv_tab_hosts": {"en": "Hosts", "es": "Hosts"},
            "advpriv_tab_dns": {"en": "DNS", "es": "DNS"},
            "advpriv_tab_packages": {"en": "Packages", "es": "Paquetes"},
            "advpriv_tab_updates": {"en": "Updates", "es": "Actualizaciones"},
            "advpriv_tab_features": {"en": "Features", "es": "Caracteristicas"},
            # -- Admin -------------------------------------------------------
            "advpriv_admin_required_title": {
                "en": "Administrator Required",
                "es": "Se Requiere Administrador",
            },
            "advpriv_admin_required_msg": {
                "en": "This operation requires administrator privileges. Please run WinSvalinn as Administrator.",
                "es": "Esta operacion requiere privilegios de administrador. Por favor ejecuta WinSvalinn como Administrador.",
            },
            # -- Telemetry section -------------------------------------------
            "advpriv_telemetry_title": {
                "en": "Windows Telemetry Blocker",
                "es": "Bloqueador de Telemetria de Windows",
            },
            "advpriv_telemetry_desc": {
                "en": "Scan and block Microsoft telemetry services, registry entries, and scheduled tasks.",
                "es": "Escanea y bloquea servicios de telemetria de Microsoft, entradas de registro y tareas programadas.",
            },
            "advpriv_scan_telemetry": {
                "en": "Scan Telemetry Status",
                "es": "Escanear Estado de Telemetria",
            },
            "advpriv_block_all_telemetry": {
                "en": "Block All Telemetry",
                "es": "Bloquear Toda la Telemetria",
            },
            "advpriv_telemetry_placeholder": {
                "en": "Click 'Scan Telemetry Status' to check current telemetry state.",
                "es": "Haz clic en 'Escanear Estado de Telemetria' para verificar el estado actual.",
            },
            "advpriv_telemetry_summary": {
                "en": "Telemetry: {active} active out of {total} components",
                "es": "Telemetria: {active} activos de {total} componentes",
            },
            "advpriv_telemetry_active": {"en": "Active", "es": "Activo"},
            "advpriv_telemetry_blocked": {"en": "Blocked", "es": "Bloqueado"},
            "advpriv_confirm_block_telemetry": {
                "en": "Block all Windows telemetry? This disables tracking services, registry entries, and scheduled tasks.",
                "es": "Bloquear toda la telemetria de Windows? Esto desactiva servicios de seguimiento, entradas de registro y tareas programadas.",
            },
            # -- Bloatware section -------------------------------------------
            "advpriv_bloatware_title": {"en": "Bloatware Remover", "es": "Removedor de Bloatware"},
            "advpriv_bloatware_desc": {
                "en": "Detect and remove pre-installed Windows bloatware and UWP apps.",
                "es": "Detecta y elimina bloatware preinstalado de Windows y aplicaciones UWP.",
            },
            "advpriv_bloatware_summary": {
                "en": "Found {total} bloatware apps ({safe} safe to remove)",
                "es": "Encontradas {total} apps de bloatware ({safe} seguras de eliminar)",
            },
            "advpriv_scan_apps": {"en": "Scan Apps", "es": "Escanear Apps"},
            "advpriv_remove_selected": {
                "en": "Remove Selected ({count})",
                "es": "Eliminar Seleccionadas ({count})",
            },
            "advpriv_remove_safe": {"en": "Remove Safe Only", "es": "Eliminar Solo Seguras"},
            "advpriv_remove_all_bloatware": {
                "en": "Remove All Bloatware",
                "es": "Eliminar Todo el Bloatware",
            },
            "advpriv_safe_tag": {"en": "SAFE", "es": "SEGURO"},
            "advpriv_no_selection_title": {"en": "No Selection", "es": "Sin Seleccion"},
            "advpriv_no_selection_msg": {
                "en": "No apps selected. Please check the apps you want to remove.",
                "es": "No hay apps seleccionadas. Marca las apps que quieres eliminar.",
            },
            "advpriv_confirm_remove_selected": {
                "en": "Remove {count} selected app(s)?\n\n{names}",
                "es": "Eliminar {count} app(s) seleccionada(s)?\n\n{names}",
            },
            # -- Hosts section -----------------------------------------------
            "advpriv_hosts_title": {"en": "Hosts File Manager", "es": "Gestor de Archivo Hosts"},
            "advpriv_hosts_desc": {
                "en": "Block ads, telemetry, and tracking domains at the DNS level using the Windows hosts file.",
                "es": "Bloquea anuncios, telemetria y dominios de seguimiento a nivel DNS usando el archivo hosts de Windows.",
            },
            "advpriv_hosts_backup": {"en": "Backup Hosts", "es": "Backup del Hosts"},
            "advpriv_hosts_block_telemetry": {"en": "Block Telemetry", "es": "Bloquear Telemetria"},
            "advpriv_hosts_block_ads": {"en": "Block Ads", "es": "Bloquear Anuncios"},
            "advpriv_hosts_block_all": {"en": "Block All", "es": "Bloquear Todo"},
            "advpriv_hosts_no_admin": {
                "en": "Administrator privileges required to modify the hosts file.",
                "es": "Se requieren privilegios de administrador para modificar el archivo hosts.",
            },
            "advpriv_confirm_hosts_block_all": {
                "en": "Block ALL known tracking, advertising, and telemetry domains in the hosts file? This adds thousands of entries.",
                "es": "Bloquear TODOS los dominios conocidos de seguimiento, publicidad y telemetria en el archivo hosts? Esto agrega miles de entradas.",
            },
            # -- DNS section -------------------------------------------------
            "advpriv_dns_title": {"en": "DNS Manager", "es": "Gestor de DNS"},
            "advpriv_dns_desc": {
                "en": "Configure DNS servers for improved privacy, speed, and ad-blocking.",
                "es": "Configura servidores DNS para mejor privacidad, velocidad y bloqueo de anuncios.",
            },
            "advpriv_dns_cloudflare": {
                "en": "Cloudflare (1.1.1.1) - Fast & Private",
                "es": "Cloudflare (1.1.1.1) - Rapido y Privado",
            },
            "advpriv_dns_google": {
                "en": "Google (8.8.8.8) - Reliable",
                "es": "Google (8.8.8.8) - Confiable",
            },
            "advpriv_dns_quad9": {
                "en": "Quad9 (9.9.9.9) - Security Focused",
                "es": "Quad9 (9.9.9.9) - Enfocado en Seguridad",
            },
            "advpriv_dns_adguard": {
                "en": "AdGuard DNS - Ad Blocking",
                "es": "AdGuard DNS - Bloqueo de Anuncios",
            },
            "advpriv_dns_dhcp": {
                "en": "Automatic (DHCP) - Reset to Default",
                "es": "Automatico (DHCP) - Restablecer por Defecto",
            },
            # -- Packages section --------------------------------------------
            "advpriv_packages_title": {
                "en": "Package Manager (winget)",
                "es": "Gestor de Paquetes (winget)",
            },
            "advpriv_packages_desc": {
                "en": "Manage installed software packages using Windows Package Manager (winget).",
                "es": "Gestiona paquetes de software instalados usando el Gestor de Paquetes de Windows (winget).",
            },
            "advpriv_check_winget": {"en": "Check winget", "es": "Verificar winget"},
            "advpriv_list_installed": {"en": "List Installed", "es": "Listar Instalados"},
            "advpriv_list_upgrades": {"en": "Check Upgrades", "es": "Ver Actualizaciones"},
            "advpriv_update_all": {"en": "Update All", "es": "Actualizar Todo"},
            "advpriv_confirm_update_all": {
                "en": "Update all packages via winget? This may take several minutes.",
                "es": "Actualizar todos los paquetes via winget? Esto puede tardar varios minutos.",
            },
            # -- Updates section ---------------------------------------------
            "advpriv_updates_title": {
                "en": "Windows Update Control",
                "es": "Control de Windows Update",
            },
            "advpriv_updates_desc": {
                "en": "Manage Windows Update behavior: check status, pause, resume, or disable automatic updates.",
                "es": "Gestiona el comportamiento de Windows Update: verificar estado, pausar, reanudar o desactivar actualizaciones automaticas.",
            },
            "advpriv_updates_loading": {
                "en": "Loading update status...",
                "es": "Cargando estado de actualizaciones...",
            },
            "advpriv_check_update_status": {"en": "Check Status", "es": "Verificar Estado"},
            "advpriv_pause_updates": {"en": "Pause Updates", "es": "Pausar Actualizaciones"},
            "advpriv_resume_updates": {"en": "Resume Updates", "es": "Reanudar Actualizaciones"},
            "advpriv_disable_updates": {
                "en": "Disable Updates",
                "es": "Desactivar Actualizaciones",
            },
            "advpriv_update_active": {"en": "Active", "es": "Activo"},
            "advpriv_update_paused": {"en": "Paused", "es": "Pausado"},
            "advpriv_update_disabled": {"en": "Disabled", "es": "Desactivado"},
            "advpriv_update_status_fmt": {
                "en": "Windows Update: {status}",
                "es": "Windows Update: {status}",
            },
            "advpriv_confirm_disable_updates": {
                "en": "Disable automatic Windows Updates? This prevents security patches from being installed automatically. Not recommended!",
                "es": "Desactivar las actualizaciones automaticas de Windows? Esto evita que los parches de seguridad se instalen automaticamente. No recomendado!",
            },
            # -- Features section --------------------------------------------
            "advpriv_features_title": {
                "en": "Windows Features Manager",
                "es": "Gestor de Caracteristicas de Windows",
            },
            "advpriv_features_desc": {
                "en": "Enable or disable optional Windows features like WSL2, Hyper-V, Sandbox, and more.",
                "es": "Habilita o deshabilita caracteristicas opcionales de Windows como WSL2, Hyper-V, Sandbox y mas.",
            },
            "advpriv_enable_wsl2": {"en": "Enable WSL2", "es": "Habilitar WSL2"},
            "advpriv_list_features": {
                "en": "List All Features",
                "es": "Listar Todas las Caracteristicas",
            },
            "advpriv_confirm_enable_wsl2": {
                "en": "Enable Windows Subsystem for Linux 2 (WSL2)? A system restart may be required.",
                "es": "Habilitar el Subsistema de Windows para Linux 2 (WSL2)? Puede requerirse reiniciar el sistema.",
            },
            "advpriv_feat_restart": {"en": "Restart required", "es": "Reinicio requerido"},
            "advpriv_feat_unknown": {"en": "Unknown", "es": "Desconocido"},
            "advpriv_restart_title": {"en": "Restart Required", "es": "Reinicio Requerido"},
            "advpriv_restart_msg": {
                "en": "A system restart is required for the changes to take effect. Please save your work and restart Windows.",
                "es": "Se requiere reiniciar el sistema para que los cambios surtan efecto. Guarda tu trabajo y reinicia Windows.",
            },
            # -- Privacy log messages ----------------------------------------
            "advpriv_log_scanning_telemetry": {
                "en": "Scanning telemetry status...",
                "es": "Escaneando estado de telemetria...",
            },
            "advpriv_log_scan_complete": {
                "en": "Telemetry scan complete.",
                "es": "Escaneo de telemetria completado.",
            },
            "advpriv_log_blocking_telemetry": {
                "en": "Blocking all telemetry...",
                "es": "Bloqueando toda la telemetria...",
            },
            "advpriv_log_telemetry_blocked": {
                "en": "All telemetry blocked successfully.",
                "es": "Toda la telemetria bloqueada exitosamente.",
            },
            "advpriv_log_changes_summary": {"en": "Changes summary:", "es": "Resumen de cambios:"},
            "advpriv_log_services_disabled": {
                "en": "  Services disabled: {count}",
                "es": "  Servicios desactivados: {count}",
            },
            "advpriv_log_registry_tweaks": {
                "en": "  Registry tweaks applied: {count}",
                "es": "  Ajustes de registro aplicados: {count}",
            },
            "advpriv_log_tasks_disabled": {
                "en": "  Scheduled tasks disabled: {count}",
                "es": "  Tareas programadas desactivadas: {count}",
            },
            "advpriv_log_rescan_pending": {
                "en": "Re-scanning to verify changes...",
                "es": "Re-escaneando para verificar cambios...",
            },
            "advpriv_log_scanning_bloatware": {
                "en": "Scanning for installed bloatware...",
                "es": "Escaneando bloatware instalado...",
            },
            "advpriv_log_bloatware_found": {
                "en": "Found {count} bloatware app(s).",
                "es": "Encontradas {count} app(s) de bloatware.",
            },
            "advpriv_log_removing_bloatware": {
                "en": "Removing bloatware...",
                "es": "Eliminando bloatware...",
            },
            "advpriv_log_removed": {
                "en": "Successfully removed {count} app(s).",
                "es": "Se eliminaron exitosamente {count} app(s).",
            },
            "advpriv_log_failed": {
                "en": "Failed to remove {count} app(s).",
                "es": "Fallo al eliminar {count} app(s).",
            },
            "advpriv_log_removing_selected": {
                "en": "Removing {count} selected app(s)...",
                "es": "Eliminando {count} app(s) seleccionada(s)...",
            },
            "advpriv_log_app_removed": {"en": "Removed: {name}", "es": "Eliminada: {name}"},
            "advpriv_log_app_failed": {
                "en": "Failed to remove: {name}",
                "es": "Fallo al eliminar: {name}",
            },
            "advpriv_log_removal_summary": {
                "en": "Removal complete: {removed} removed, {failed} failed.",
                "es": "Eliminacion completa: {removed} eliminadas, {failed} fallidas.",
            },
            "advpriv_log_blocking_hosts_telemetry": {
                "en": "Blocking telemetry domains in hosts file...",
                "es": "Bloqueando dominios de telemetria en archivo hosts...",
            },
            "advpriv_log_blocking_hosts_ads": {
                "en": "Blocking ad-network domains in hosts file...",
                "es": "Bloqueando dominios de redes de anuncios en archivo hosts...",
            },
            "advpriv_log_blocking_hosts_all": {
                "en": "Blocking all known tracking/ad/telemetry domains...",
                "es": "Bloqueando todos los dominios conocidos de seguimiento/anuncios/telemetria...",
            },
            "advpriv_log_hosts_telemetry_done": {
                "en": "Telemetry domains blocked: {count} entries added.",
                "es": "Dominios de telemetria bloqueados: {count} entradas agregadas.",
            },
            "advpriv_log_hosts_ads_done": {
                "en": "Ad-network domains blocked: {count} entries added.",
                "es": "Dominios de anuncios bloqueados: {count} entradas agregadas.",
            },
            "advpriv_log_hosts_all_done": {
                "en": "All domains blocked: {count} entries added.",
                "es": "Todos los dominios bloqueados: {count} entradas agregadas.",
            },
            "advpriv_log_hosts_error": {
                "en": "Error modifying hosts file: {error}",
                "es": "Error al modificar archivo hosts: {error}",
            },
            "advpriv_log_dns_reset": {
                "en": "Resetting DNS to automatic (DHCP)...",
                "es": "Restableciendo DNS a automatico (DHCP)...",
            },
            "advpriv_log_dns_setting": {
                "en": "Setting DNS to {preset}...",
                "es": "Configurando DNS a {preset}...",
            },
            "advpriv_log_checking_winget": {
                "en": "Checking if winget is available...",
                "es": "Verificando si winget esta disponible...",
            },
            "advpriv_log_listing_packages": {
                "en": "Listing installed packages...",
                "es": "Listando paquetes instalados...",
            },
            "advpriv_log_packages_found": {
                "en": "Found {count} installed package(s).",
                "es": "Encontrados {count} paquete(s) instalado(s).",
            },
            "advpriv_log_checking_upgrades": {
                "en": "Checking for available upgrades...",
                "es": "Buscando actualizaciones disponibles...",
            },
            "advpriv_log_upgrades_found": {
                "en": "Found {count} package(s) with available upgrades.",
                "es": "Encontrados {count} paquete(s) con actualizaciones disponibles.",
            },
            "advpriv_log_updating_all": {
                "en": "Updating all packages...",
                "es": "Actualizando todos los paquetes...",
            },
            "advpriv_log_checking_update_status": {
                "en": "Checking Windows Update status...",
                "es": "Verificando estado de Windows Update...",
            },
            "advpriv_log_update_status": {
                "en": "Windows Update status: {status}",
                "es": "Estado de Windows Update: {status}",
            },
            "advpriv_log_paused_until": {
                "en": "  Updates paused until: {until}",
                "es": "  Actualizaciones pausadas hasta: {until}",
            },
            "advpriv_log_pausing_updates": {
                "en": "Pausing Windows Updates for 35 days...",
                "es": "Pausando Windows Updates por 35 dias...",
            },
            "advpriv_log_resuming_updates": {
                "en": "Resuming Windows Updates...",
                "es": "Reanudando Windows Updates...",
            },
            "advpriv_log_disabling_updates": {
                "en": "Disabling automatic Windows Updates...",
                "es": "Desactivando actualizaciones automaticas de Windows...",
            },
            "advpriv_log_error": {"en": "Error: {error}", "es": "Error: {error}"},
            "advpriv_log_enabling_wsl2": {"en": "Enabling WSL2...", "es": "Habilitando WSL2..."},
            "advpriv_log_listing_features": {
                "en": "Listing Windows features...",
                "es": "Listando caracteristicas de Windows...",
            },
            "advpriv_log_features_error": {
                "en": "Error retrieving Windows features.",
                "es": "Error al obtener caracteristicas de Windows.",
            },
            "advpriv_log_features_shown": {
                "en": "Showing {count} popular Windows features.",
                "es": "Mostrando {count} caracteristicas populares de Windows.",
            },
            "advpriv_log_restart_required": {
                "en": "A system restart is required for the changes to take effect.",
                "es": "Se requiere reiniciar el sistema para que los cambios surtan efecto.",
            },
            # ─── History & Rollback ────────────────────────────────
            "nav_history": {"en": "History & Rollback", "es": "Historial y Rollback"},
            "history_title": {"en": "History & Rollback", "es": "Historial y Rollback"},
            "history_subtitle": {
                "en": "View all changes made by WinSvalinn, restore points, and registry backups. You can undo reversible changes.",
                "es": "Ver todos los cambios realizados por WinSvalinn, puntos de restauracion y backups de registro. Puedes deshacer cambios reversibles.",
            },
            "history_refresh": {"en": "Refresh", "es": "Actualizar"},
            "history_export": {"en": "Export Report", "es": "Exportar Informe"},
            "history_loading": {"en": "Loading history...", "es": "Cargando historial..."},
            "history_empty": {
                "en": "No changes recorded yet. Changes will appear here when you use WinSvalinn to modify your system.",
                "es": "No hay cambios registrados. Los cambios apareceran aqui cuando uses WinSvalinn para modificar el sistema.",
            },
            "history_tab_changes": {"en": "Changes", "es": "Cambios"},
            "history_tab_restore": {"en": "Restore Points", "es": "Puntos de Restauracion"},
            "history_tab_registry": {"en": "Registry Backups", "es": "Backups de Registro"},
            "history_total": {"en": "Total entries", "es": "Total de entradas"},
            "history_reversible": {"en": "Reversible", "es": "Reversibles"},
            "history_reverted": {"en": "Reverted", "es": "Revertidos"},
            "history_size": {"en": "File size", "es": "Tamano archivo"},
            "history_can_undo": {"en": "Can be undone", "es": "Se puede deshacer"},
            "history_rp_status": {"en": "System Restore", "es": "Restaurar Sistema"},
            "history_rp_enabled": {"en": "Enabled", "es": "Habilitado"},
            "history_rp_disabled": {"en": "Disabled", "es": "Deshabilitado"},
            "history_rp_count": {"en": "Points", "es": "Puntos"},
            "history_rp_max": {"en": "Max usage", "es": "Uso maximo"},
            "history_rp_none": {
                "en": "No restore points found.",
                "es": "No se encontraron puntos de restauracion.",
            },
            "history_rp_found": {"en": "Found", "es": "Encontrados"},
            "history_rp_points": {"en": "restore points", "es": "puntos de restauracion"},
            "history_rp_created_by_ws": {
                "en": "Created by WinSvalinn",
                "es": "Creado por WinSvalinn",
            },
            "history_rb_files": {"en": "Backup files", "es": "Archivos de backup"},
            "history_rb_size": {"en": "Total size", "es": "Tamano total"},
            "history_rb_tags": {"en": "Operations", "es": "Operaciones"},
            "history_rb_none": {
                "en": "No registry backups yet.",
                "es": "No hay backups de registro aun.",
            },
            "history_rb_auto": {
                "en": "Backups are created automatically before any registry modification.",
                "es": "Los backups se crean automaticamente antes de cualquier modificacion del registro.",
            },
            "history_rb_file": {"en": "File", "es": "Archivo"},
            "history_exported": {"en": "Report exported to", "es": "Informe exportado a"},
            "history_export_fail": {"en": "Export failed", "es": "Error al exportar"},
            "history_export_title": {"en": "Export Changelog", "es": "Exportar Historial"},
            # ─── Diagnostics ───────────────────────────────────────
            "nav_diagnostics": {"en": "System Diagnostics", "es": "Diagnostico del Sistema"},
            "diag_title": {"en": "System Diagnostics", "es": "Diagnostico del Sistema"},
            "diag_subtitle": {
                "en": "Deep hardware analysis, disk health, event logs, drivers, scheduled tasks, and thermal monitoring.",
                "es": "Analisis profundo de hardware, salud del disco, eventos del sistema, drivers, tareas programadas y monitoreo termal.",
            },
            "diag_tab_hardware": {"en": "Hardware", "es": "Hardware"},
            "diag_tab_disks": {"en": "Disks", "es": "Discos"},
            "diag_tab_events": {"en": "Events", "es": "Eventos"},
            "diag_tab_drivers": {"en": "Drivers", "es": "Drivers"},
            "diag_tab_tasks": {"en": "Tasks", "es": "Tareas"},
            "diag_tab_thermal": {"en": "Thermal", "es": "Temperatura"},
            # ─── Network Advanced ──────────────────────────────────
            "nav_network_advanced": {"en": "Advanced Network", "es": "Red Avanzada"},
            "netadv_title": {"en": "Advanced Network Analysis", "es": "Analisis de Red Avanzado"},
            "netadv_subtitle": {
                "en": "WiFi security audit, network diagnostics, VPN/proxy detection, and traffic monitoring.",
                "es": "Auditoria de seguridad WiFi, diagnostico de red, deteccion de VPN/proxy y monitoreo de trafico.",
            },
            "netadv_tab_wifi": {"en": "WiFi", "es": "WiFi"},
            "netadv_tab_diag": {"en": "Diagnostics", "es": "Diagnostico"},
            "netadv_tab_vpn": {"en": "VPN / Proxy", "es": "VPN / Proxy"},
            "netadv_tab_traffic": {"en": "Traffic", "es": "Trafico"},
            # ─── Advanced Cleanup ──────────────────────────────────
            "nav_cleanup_advanced": {"en": "Deep Cleanup", "es": "Limpieza Profunda"},
            "cleanadv_title": {
                "en": "Deep Cleanup & Privacy",
                "es": "Limpieza Profunda y Privacidad",
            },
            "cleanadv_subtitle": {
                "en": "Clean browser data, Windows privacy traces, and audit stored credentials.",
                "es": "Limpiar datos de navegadores, rastros de privacidad de Windows y auditar credenciales almacenadas.",
            },
            "cleanadv_tab_browsers": {"en": "Browsers", "es": "Navegadores"},
            "cleanadv_tab_privacy": {"en": "Privacy", "es": "Privacidad"},
            "cleanadv_tab_creds": {"en": "Credentials", "es": "Credenciales"},
            "cleanadv_clean": {"en": "Clean Selected", "es": "Limpiar Seleccion"},
            # ─── System Management ─────────────────────────────────
            "nav_system_management": {"en": "System Management", "es": "Gestion del Sistema"},
            "sysmgmt_title": {"en": "System Management", "es": "Gestion del Sistema"},
            "sysmgmt_subtitle": {
                "en": "Users, shared resources, certificates, system integrity, and environment variables.",
                "es": "Usuarios, recursos compartidos, certificados, integridad del sistema y variables de entorno.",
            },
            "sysmgmt_tab_users": {"en": "Users", "es": "Usuarios"},
            "sysmgmt_tab_shares": {"en": "Shares", "es": "Compartidos"},
            "sysmgmt_tab_certs": {"en": "Certificates", "es": "Certificados"},
            "sysmgmt_tab_integrity": {"en": "Integrity", "es": "Integridad"},
            "sysmgmt_tab_env": {"en": "Environment", "es": "Entorno"},
        }

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, value):
        if value in ("en", "es"):
            self._lang = value

    def t(self, key):
        """Get translated string."""
        entry = self._strings.get(key, {})
        return entry.get(self._lang, entry.get("en", f"[{key}]"))

    def get_all_keys(self):
        """Get all translation keys."""
        return list(self._strings.keys())
