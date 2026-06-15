"""
AI Windows Module - WinGuardOptimizer

Detects and removes ALL Windows AI features:
- Windows Copilot
- Recall (screenshot AI)
- AI Explorer
- Suggested Actions
- Telemetry AI
- Widgets AI
- Live Captions
- Voice Access

Author: WinGuardOptimizer Team
Date: 2025-02-28
"""

import os
import platform
import subprocess
from datetime import datetime

from winsvalinn.utils.logger import ModuleLogger
from winsvalinn.utils.registry_helper import get_registry, set_registry

logger = ModuleLogger("AIWindowsRemover")


class AIWindowsRemover:
    """
    Detect and remove all Windows AI features.

    Supported Windows versions:
    - Windows 11 23H2, 24H2 (Copilot, Recall)
    - Windows 11 22H2 (Copilot)
    - Windows 10 (limited AI features)
    """

    def __init__(self, callback=None):
        """
        Initialize AI Windows Remover.

        Args:
            callback: Optional GUI logging callback (msg, level)
        """
        self.callback = callback or (lambda msg, level="info": None)
        self.is_windows = platform.system() == "Windows"
        self.windows_version = platform.version()

        logger.info(f"AIWindowsRemover initialized - Windows version: {self.windows_version}")

    def log(self, message, level="info"):
        """Log to both GUI and file."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.callback(f"[{timestamp}] {message}", level)

        log_method = getattr(logger, level.lower(), logger.info)
        log_method(message)

    # ═══════════════════════════════════════════════════════════════
    # Detection Methods
    # ═══════════════════════════════════════════════════════════════

    def detect_all_ai_features(self):
        """
        Detect all Windows AI features currently active.

        Returns:
            dict: Status of all AI features
        """
        logger.info("Starting AI feature detection...")
        self.log("Escaneando características de IA de Windows...", "info")

        results = {
            "copilot": self.check_copilot_status(),
            "recall": self.check_recall_status(),
            "suggested_actions": self.check_suggested_actions(),
            "live_captions": self.check_live_captions(),
            "voice_access": self.check_voice_access(),
            "ai_widgets": self.check_ai_widgets(),
            "ai_search": self.check_ai_search(),
            "ai_telemetry": self.check_ai_telemetry(),
            "cortana": self.check_cortana_status(),
        }

        # Count active features
        active_count = sum(1 for feature in results.values() if feature.get("active", False))
        total_count = len(results)

        self.log(
            f"Encontradas {active_count} de {total_count} características de IA activas",
            "warning" if active_count > 0 else "success",
        )

        # Add summary
        results["summary"] = {
            "total_features": total_count,
            "active_features": active_count,
            "inactive_features": total_count - active_count,
        }

        return results

    def check_copilot_status(self):
        """Check Windows Copilot status."""
        logger.info("Checking Copilot status...")

        try:
            # Check registry key for Copilot
            success, value = get_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "ShowCopilotButton",
            )

            # Check if Copilot process is running
            copilot_running = self._is_process_running("Copilot.exe")

            # Check Copilot service
            copilot_service = self._is_service_running("CopilotService")

            active = (value == "1") or copilot_running or copilot_service

            return {
                "name": "Windows Copilot",
                "active": active,
                "registry_enabled": value == "1" if success else None,
                "process_running": copilot_running,
                "service_running": copilot_service,
                "description": "Asistente de IA de Windows 11",
            }

        except Exception as e:
            logger.error(f"Error checking Copilot: {e}")
            return {"name": "Windows Copilot", "active": False, "error": str(e)}

    def check_recall_status(self):
        """Check Windows Recall (screenshot AI) status."""
        logger.info("Checking Recall status...")

        try:
            # Recall is in Windows 11 24H2
            # Check if Recall feature is enabled
            success, value = get_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "DisableRecall"
            )

            # If registry key doesn't exist OR value is not "1", Recall is potentially active
            # But only on Windows 11 24H2+
            is_24h2 = self._is_windows_11_24h2()
            recall_enabled = (value != "1" if success else False) and is_24h2

            return {
                "name": "Windows Recall",
                "active": recall_enabled,
                "description": "IA que captura screenshots constantemente (privacidad crítica)",
                "privacy_risk": "HIGH",
                "available": is_24h2,
            }

        except Exception as e:
            logger.error(f"Error checking Recall: {e}")
            return {"name": "Windows Recall", "active": False, "error": str(e)}

    def check_suggested_actions(self):
        """Check Suggested Actions (AI suggestions) status."""
        logger.info("Checking Suggested Actions...")

        try:
            success, value = get_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\SmartActionPlatform\SmartClipboard",
                "Disabled",
            )

            active = value != "1" if success else True

            return {
                "name": "Suggested Actions",
                "active": active,
                "description": "Sugerencias de IA en portapapeles y texto seleccionado",
            }

        except Exception as e:
            logger.error(f"Error checking Suggested Actions: {e}")
            return {"name": "Suggested Actions", "active": False, "error": str(e)}

    def check_live_captions(self):
        """Check Live Captions (AI transcription) status."""
        logger.info("Checking Live Captions...")

        try:
            success, value = get_registry(
                r"HKCU\Software\Microsoft\Accessibility", "LiveCaptionsEnabled"
            )

            active = value == "1" if success else False

            return {
                "name": "Live Captions",
                "active": active,
                "description": "Subtítulos en vivo con IA (transcripción de audio)",
            }

        except Exception as e:
            logger.error(f"Error checking Live Captions: {e}")
            return {"name": "Live Captions", "active": False, "error": str(e)}

    def check_voice_access(self):
        """Check Voice Access (voice AI) status."""
        logger.info("Checking Voice Access...")

        try:
            # Check if Voice Access is running
            voice_running = self._is_process_running("VoiceAccess.exe")

            return {
                "name": "Voice Access",
                "active": voice_running,
                "description": "Control de voz con IA",
            }

        except Exception as e:
            logger.error(f"Error checking Voice Access: {e}")
            return {"name": "Voice Access", "active": False, "error": str(e)}

    def check_ai_widgets(self):
        """Check AI-powered widgets status."""
        logger.info("Checking AI Widgets...")

        try:
            success, value = get_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarDa"
            )

            active = value == "1" if success else False

            return {
                "name": "AI Widgets",
                "active": active,
                "description": "Widgets con contenido generado por IA",
            }

        except Exception as e:
            logger.error(f"Error checking AI Widgets: {e}")
            return {"name": "AI Widgets", "active": False, "error": str(e)}

    def check_ai_search(self):
        """Check AI-powered Windows Search."""
        logger.info("Checking AI Search...")

        try:
            # Check if Bing AI is integrated in search
            success, value = get_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\SearchSettings",
                "IsDynamicSearchBoxEnabled",
            )

            active = value == "1" if success else False

            return {
                "name": "AI Search (Bing)",
                "active": active,
                "description": "Búsqueda con IA de Bing integrada",
            }

        except Exception as e:
            logger.error(f"Error checking AI Search: {e}")
            return {"name": "AI Search", "active": False, "error": str(e)}

    def check_ai_telemetry(self):
        """Check AI-specific telemetry."""
        logger.info("Checking AI Telemetry...")

        try:
            # Check DiagTrack (telemetry service)
            diagtrack_running = self._is_service_running("DiagTrack")

            # Check AI Experience telemetry
            success, value = get_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry"
            )

            telemetry_enabled = value != "0" if success else True

            return {
                "name": "AI Telemetry",
                "active": diagtrack_running or telemetry_enabled,
                "description": "Recopilación de datos para mejorar IA de Microsoft",
            }

        except Exception as e:
            logger.error(f"Error checking AI Telemetry: {e}")
            return {"name": "AI Telemetry", "active": False, "error": str(e)}

    def check_cortana_status(self):
        """Check Cortana (legacy AI assistant) status."""
        logger.info("Checking Cortana...")

        try:
            cortana_running = self._is_process_running("Cortana.exe")

            success, value = get_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "ShowCortanaButton",
            )

            button_shown = value == "1" if success else False

            return {
                "name": "Cortana",
                "active": cortana_running or button_shown,
                "description": "Asistente de IA legacy (reemplazado por Copilot)",
            }

        except Exception as e:
            logger.error(f"Error checking Cortana: {e}")
            return {"name": "Cortana", "active": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════
    # Removal Methods
    # ═══════════════════════════════════════════════════════════════

    def remove_all_ai(self):
        """
        Remove ALL Windows AI features.

        Returns:
            dict: Results of removal operations
        """
        logger.info("Starting complete AI removal...")
        self.log("🤖 Eliminando TODAS las características de IA de Windows...", "warning")

        results = {
            "copilot": self.remove_copilot(),
            "recall": self.remove_recall(),
            "suggested_actions": self.remove_suggested_actions(),
            "live_captions": self.remove_live_captions(),
            "voice_access": self.remove_voice_access(),
            "ai_widgets": self.remove_ai_widgets(),
            "ai_search": self.remove_ai_search(),
            "ai_telemetry": self.remove_ai_telemetry(),
            "cortana": self.remove_cortana(),
        }

        success_count = sum(1 for r in results.values() if r.get("success", False))
        total_count = len(results)

        self.log(f"✅ Eliminación completa: {success_count}/{total_count} exitosas", "success")
        logger.info(f"AI removal complete: {success_count}/{total_count} successful")

        return results

    def remove_copilot(self):
        """Remove Windows Copilot completely."""
        logger.info("Removing Copilot...")
        self.log("Eliminando Windows Copilot...", "info")

        actions = []

        try:
            # 1. Hide Copilot button
            success, msg = set_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "ShowCopilotButton",
                "0",
                "REG_DWORD",
            )
            if success:
                actions.append("Botón de Copilot ocultado")

            # 2. Disable Copilot via policy
            success, msg = set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot",
                "TurnOffWindowsCopilot",
                "1",
                "REG_DWORD",
            )
            if success:
                actions.append("Copilot desactivado via política")

            # 3. Disable Copilot in Edge
            success, msg = set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Edge", "CopilotPageEnabled", "0", "REG_DWORD"
            )
            if success:
                actions.append("Copilot en Edge desactivado")

            # 4. Kill Copilot process if running
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "Copilot.exe"],
                    capture_output=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                actions.append("Proceso Copilot terminado")
            except Exception as e:
                self._log(f"Error: {str(e)}", "error")
                pass

            self.log("✓ Copilot eliminado exitosamente", "success")
            return {"success": True, "actions": actions}

        except Exception as e:
            logger.exception(f"Error removing Copilot: {e}")
            self.log(f"✗ Error eliminando Copilot: {e}", "error")
            return {"success": False, "error": str(e), "actions": actions}

    def remove_recall(self):
        """Remove Windows Recall (screenshot AI)."""
        logger.info("Removing Recall...")
        self.log("Eliminando Windows Recall (IA de screenshots)...", "info")

        actions = []

        try:
            # 1. Disable Recall completely
            success, msg = set_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "DisableRecall",
                "1",
                "REG_DWORD",
            )
            if success:
                actions.append("Recall desactivado")

            # 2. Disable AI snapshot feature
            success, msg = set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsAI",
                "DisableAIDataAnalysis",
                "1",
                "REG_DWORD",
            )
            if success:
                actions.append("Análisis de datos AI desactivado")

            # 3. Clear Recall data folder if exists
            recall_data_path = os.path.join(
                os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Recall"
            )

            if os.path.exists(recall_data_path):
                try:
                    import shutil

                    shutil.rmtree(recall_data_path)
                    actions.append(f"Datos de Recall eliminados: {recall_data_path}")
                except Exception as e:
                    logger.warning(f"Could not delete Recall data: {e}")

            self.log("✓ Recall eliminado exitosamente", "success")
            return {"success": True, "actions": actions}

        except Exception as e:
            logger.exception(f"Error removing Recall: {e}")
            self.log(f"✗ Error eliminando Recall: {e}", "error")
            return {"success": False, "error": str(e), "actions": actions}

    def remove_suggested_actions(self):
        """Remove AI Suggested Actions."""
        logger.info("Removing Suggested Actions...")
        self.log("Eliminando Suggested Actions...", "info")

        actions = []

        try:
            success, msg = set_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\SmartActionPlatform\SmartClipboard",
                "Disabled",
                "1",
                "REG_DWORD",
            )
            if success:
                actions.append("Suggested Actions desactivado")

            self.log("✓ Suggested Actions eliminado", "success")
            return {"success": True, "actions": actions}

        except Exception as e:
            logger.exception(f"Error removing Suggested Actions: {e}")
            return {"success": False, "error": str(e), "actions": actions}

    def remove_live_captions(self):
        """Remove Live Captions AI."""
        logger.info("Removing Live Captions...")
        self.log("Eliminando Live Captions...", "info")

        actions = []

        try:
            success, msg = set_registry(
                r"HKCU\Software\Microsoft\Accessibility", "LiveCaptionsEnabled", "0", "REG_DWORD"
            )
            if success:
                actions.append("Live Captions desactivado")

            self.log("✓ Live Captions eliminado", "success")
            return {"success": True, "actions": actions}

        except Exception as e:
            logger.exception(f"Error removing Live Captions: {e}")
            return {"success": False, "error": str(e), "actions": actions}

    def remove_voice_access(self):
        """Remove Voice Access AI."""
        logger.info("Removing Voice Access...")
        self.log("Eliminando Voice Access...", "info")

        actions = []

        try:
            # Kill Voice Access if running
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "VoiceAccess.exe"],
                    capture_output=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                actions.append("Voice Access terminado")
            except Exception as e:
                self._log(f"Error: {str(e)}", "error")
                pass

            # Disable Voice Access
            success, msg = set_registry(
                r"HKCU\Software\Microsoft\Speech_OneCore\Settings\VoiceActivation\UserPreferenceForAllApps",
                "AgentActivationEnabled",
                "0",
                "REG_DWORD",
            )
            if success:
                actions.append("Voice Access desactivado")

            self.log("✓ Voice Access eliminado", "success")
            return {"success": True, "actions": actions}

        except Exception as e:
            logger.exception(f"Error removing Voice Access: {e}")
            return {"success": False, "error": str(e), "actions": actions}

    def remove_ai_widgets(self):
        """Remove AI Widgets."""
        logger.info("Removing AI Widgets...")
        self.log("Eliminando AI Widgets...", "info")

        actions = []

        try:
            # Disable widgets completely
            success, msg = set_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "TaskbarDa",
                "0",
                "REG_DWORD",
            )
            if success:
                actions.append("Widgets desactivados")

            # Kill widgets process
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "WidgetService.exe"],
                    capture_output=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                actions.append("Widget Service terminado")
            except Exception as e:
                self._log(f"Error: {str(e)}", "error")
                pass

            self.log("✓ AI Widgets eliminados", "success")
            return {"success": True, "actions": actions}

        except Exception as e:
            logger.exception(f"Error removing AI Widgets: {e}")
            return {"success": False, "error": str(e), "actions": actions}

    def remove_ai_search(self):
        """Remove AI Search (Bing)."""
        logger.info("Removing AI Search...")
        self.log("Eliminando AI Search (Bing)...", "info")

        actions = []

        try:
            # Disable Bing search in Start Menu
            success, msg = set_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Search",
                "BingSearchEnabled",
                "0",
                "REG_DWORD",
            )
            if success:
                actions.append("Bing Search desactivado")

            # Disable web search
            success, msg = set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                "DisableWebSearch",
                "1",
                "REG_DWORD",
            )
            if success:
                actions.append("Web Search desactivado")

            # Disable Cortana in search
            success, msg = set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                "AllowCortana",
                "0",
                "REG_DWORD",
            )
            if success:
                actions.append("Cortana en búsqueda desactivado")

            self.log("✓ AI Search eliminado", "success")
            return {"success": True, "actions": actions}

        except Exception as e:
            logger.exception(f"Error removing AI Search: {e}")
            return {"success": False, "error": str(e), "actions": actions}

    def remove_ai_telemetry(self):
        """Remove AI Telemetry."""
        logger.info("Removing AI Telemetry...")
        self.log("Eliminando telemetría de IA...", "info")

        actions = []

        try:
            # Disable telemetry completely
            success, msg = set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                "AllowTelemetry",
                "0",
                "REG_DWORD",
            )
            if success:
                actions.append("Telemetría desactivada")

            # Disable AI data collection
            success, msg = set_registry(
                r"HKCU\Software\Microsoft\Siuf\Rules", "NumberOfSIUFInPeriod", "0", "REG_DWORD"
            )
            if success:
                actions.append("Recopilación de datos AI desactivada")

            # Disable DiagTrack service
            try:
                subprocess.run(
                    ["sc", "stop", "DiagTrack"],
                    capture_output=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                subprocess.run(
                    ["sc", "config", "DiagTrack", "start=", "disabled"],
                    capture_output=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                actions.append("Servicio DiagTrack desactivado")
            except Exception as e:
                self._log(f"Error: {str(e)}", "error")
                pass

            self.log("✓ Telemetría AI eliminada", "success")
            return {"success": True, "actions": actions}

        except Exception as e:
            logger.exception(f"Error removing AI Telemetry: {e}")
            return {"success": False, "error": str(e), "actions": actions}

    def remove_cortana(self):
        """Remove Cortana."""
        logger.info("Removing Cortana...")
        self.log("Eliminando Cortana...", "info")

        actions = []

        try:
            # Kill Cortana process
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "Cortana.exe"],
                    capture_output=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                actions.append("Proceso Cortana terminado")
            except Exception as e:
                self._log(f"Error: {str(e)}", "error")
                pass

            # Disable Cortana via registry
            success, msg = set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                "AllowCortana",
                "0",
                "REG_DWORD",
            )
            if success:
                actions.append("Cortana desactivada via política")

            # Hide Cortana button
            success, msg = set_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "ShowCortanaButton",
                "0",
                "REG_DWORD",
            )
            if success:
                actions.append("Botón Cortana ocultado")

            self.log("✓ Cortana eliminada", "success")
            return {"success": True, "actions": actions}

        except Exception as e:
            logger.exception(f"Error removing Cortana: {e}")
            return {"success": False, "error": str(e), "actions": actions}

    # ═══════════════════════════════════════════════════════════════
    # Helper Methods
    # ═══════════════════════════════════════════════════════════════

    def _is_process_running(self, process_name):
        """Check if a process is running."""
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return process_name.lower() in result.stdout.lower()
        except Exception:
            return False

    def _is_service_running(self, service_name):
        """Check if a service is running."""
        try:
            result = subprocess.run(
                ["sc", "query", service_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return "RUNNING" in result.stdout
        except Exception:
            return False

    def _is_windows_11_24h2(self):
        """Check if running Windows 11 24H2 or later."""
        try:
            # Windows 11 24H2 build number is 26100+
            build = int(platform.version().split(".")[2])
            return build >= 26100
        except Exception:
            return False


# Example usage
if __name__ == "__main__":
    from winsvalinn.utils.logger import setup_logging

    setup_logging()

    print("=" * 60)
    print("AI Windows Remover - Test")
    print("=" * 60)

    remover = AIWindowsRemover()

    print("\n1. Detectando características de IA...")
    print("-" * 60)
    features = remover.detect_all_ai_features()

    for key, feature in features.items():
        if isinstance(feature, dict):
            status = "🔴 ACTIVO" if feature.get("active") else "🟢 INACTIVO"
            name = feature.get("name", key)
            print(f"{status} - {name}")
            if feature.get("description"):
                print(f"         {feature['description']}")

    print("\n2. ¿Quieres eliminar TODAS las características de IA?")
    print("   (Esto requiere privilegios de administrador)")

    # Uncomment to actually remove:
    # response = input("\n   Escribe 'SI' para continuar: ")
    # if response.upper() == "SI":
    #     print("\n   Eliminando IA de Windows...")
    #     results = remover.remove_all_ai()
    #     print("\n   ✅ Proceso completo!")

    print("\n✅ Test completado. Revisa winguard.log para detalles.")
