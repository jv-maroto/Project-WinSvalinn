"""
GPU Brand-Specific Optimization - WinSvalinn
Detects GPU brand (NVIDIA, AMD, Intel) and applies brand-specific tweaks.
"""

import platform
import subprocess
from datetime import datetime

from winsvalinn.utils.registry_helper import set_registry

# Per-brand GPU tweaks (path, value_name, type, value, description). Mirrors the
# lists in optimize_nvidia/amd/intel; used by the selectable plan()/apply_selected().
_GPU0 = r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000"

BRAND_TWEAKS: dict[str, list[tuple]] = {
    "NVIDIA": [
        (_GPU0, "PerfLevelSrc", "REG_DWORD", "8738", "Preferir máximo rendimiento (NVIDIA)"),
        (
            r"HKLM\SOFTWARE\NVIDIA Corporation\NvControlPanel2\Client",
            "OptInOrOutPreference",
            "REG_DWORD",
            "0",
            "Desactivar telemetría NVIDIA",
        ),
        (
            r"HKLM\SOFTWARE\NVIDIA Corporation\Global\GfExperience",
            "GameStream",
            "REG_DWORD",
            "0",
            "Desactivar NVIDIA GameStream",
        ),
        (_GPU0, "ShaderCacheSizeInMB", "REG_DWORD", "4096", "Aumentar caché de shaders a 4 GB"),
        (_GPU0, "PowerMizerEnable", "REG_DWORD", "1", "Activar PowerMizer"),
        (_GPU0, "PowerMizerLevel", "REG_DWORD", "1", "PowerMizer a máximo rendimiento"),
        (
            r"HKLM\SOFTWARE\NVIDIA Corporation\Global\NVTweak",
            "Threaded optimization",
            "REG_DWORD",
            "1",
            "Activar optimización multihilo",
        ),
        (
            r"HKCU\SOFTWARE\NVIDIA Corporation\Global\ShadowPlay\NVSPCAPS",
            "{1B4A1DA5-4E40-4DE7-8307-6C5F6CB8E2B6}",
            "REG_DWORD",
            "0",
            "Desactivar overlay NVIDIA (menos input lag)",
        ),
        (
            r"HKLM\SOFTWARE\NVIDIA Corporation\Global\NVTweak",
            "TextureFilterQuality",
            "REG_DWORD",
            "0",
            "Filtrado de texturas a alto rendimiento",
        ),
    ],
    "AMD": [
        (_GPU0, "EnableUlps", "REG_DWORD", "0", "Desactivar AMD ULPS (estabilidad)"),
        (_GPU0, "EnableCrossFireAutoLink", "REG_DWORD", "0", "Desactivar CrossFire auto-link"),
        (
            _GPU0,
            "PP_ThermalAutoThrottlingEnable",
            "REG_DWORD",
            "0",
            "Desactivar auto-throttling térmico",
        ),
        (r"HKLM\SOFTWARE\AMD\CN", "SWLAYERS_ENABLE", "REG_SZ", "0", "Desactivar overlay Radeon"),
        (r"HKLM\SOFTWARE\AMD\CN", "AntiLag", "REG_DWORD", "1", "Activar Anti-Lag (menos latencia)"),
        (
            r"HKLM\SOFTWARE\AMD\CN",
            "RadeonChill",
            "REG_DWORD",
            "0",
            "Desactivar Radeon Chill (evita limitar FPS)",
        ),
        (r"HKLM\SOFTWARE\AMD\CN", "RIS", "REG_DWORD", "1", "Activar Radeon Image Sharpening"),
        (_GPU0 + r"\UMD", "ShaderCache", "REG_DWORD", "1", "Activar caché de shaders AMD"),
        (_GPU0, "KMD_FRCGFEnabled", "REG_DWORD", "0", "Desactivar FRTC para máximos FPS"),
        (_GPU0, "KMD_DeLagEnabled", "REG_DWORD", "1", "Activar DeLag (menos input delay)"),
    ],
    "Intel": [
        (
            r"HKLM\SOFTWARE\Intel\GMM",
            "DedicatedSegmentSize",
            "REG_DWORD",
            "512",
            "Aumentar memoria GPU Intel a 512 MB",
        ),
        (
            _GPU0,
            "FeatureTestControl",
            "REG_DWORD",
            "9a40",
            "Desactivar ahorro de energía GPU Intel",
        ),
        (_GPU0, "AdaptiveVsyncEnable", "REG_DWORD", "0", "Desactivar Adaptive VSync (Intel)"),
        (
            _GPU0,
            "Disable_OverlayDSQualityEnhancement",
            "REG_DWORD",
            "1",
            "Desactivar mejora de overlay (menos latencia)",
        ),
        (
            r"HKLM\SOFTWARE\Intel\Display\igfxcui\profiles\Media\Brighten Movie",
            "ProcAmpBrightness",
            "REG_DWORD",
            "0",
            "Procesado de imagen Intel neutro",
        ),
        (
            _GPU0,
            "ACPowerPolicyVersion",
            "REG_DWORD",
            "16898",
            "Política de energía GPU Intel a máximo (AC)",
        ),
        (
            _GPU0,
            "DCPowerPolicyVersion",
            "REG_DWORD",
            "16642",
            "Política de energía GPU Intel optimizada (batería)",
        ),
    ],
}


class GPUBrandOptimizer:
    """Detect GPU brand and apply brand-specific optimizations."""

    def __init__(self, callback=None):
        self.callback = callback or (lambda msg, level="info": None)
        self.is_windows = platform.system() == "Windows"
        self._detected_brand = None
        self._gpu_name = None

    def log(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.callback(f"[{timestamp}] {message}", level)

    def detect_gpu_brand(self):
        """Detect GPU brand from system."""
        if not self.is_windows:
            return "Unknown", "Non-Windows system"

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                gpu_names = [
                    line.strip() for line in result.stdout.strip().split("\n") if line.strip()
                ]
                for name in gpu_names:
                    name_lower = name.lower()
                    if (
                        "nvidia" in name_lower
                        or "geforce" in name_lower
                        or "rtx" in name_lower
                        or "gtx" in name_lower
                    ):
                        self._detected_brand = "NVIDIA"
                        self._gpu_name = name
                        return "NVIDIA", name
                    elif "amd" in name_lower or "radeon" in name_lower or "rx " in name_lower:
                        self._detected_brand = "AMD"
                        self._gpu_name = name
                        return "AMD", name
                    elif "intel" in name_lower:
                        self._detected_brand = "Intel"
                        self._gpu_name = name
                        return "Intel", name

                if gpu_names:
                    self._detected_brand = "Unknown"
                    self._gpu_name = gpu_names[0]
                    return "Unknown", gpu_names[0]

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return "Unknown", "Could not detect"

    # ─── NVIDIA Optimizations ───────────────────────────────────────

    def optimize_nvidia(self):
        """Apply NVIDIA-specific optimizations."""
        results = {"actions": [], "success": True, "brand": "NVIDIA"}

        if not self.is_windows:
            return results

        tweaks = [
            # NVIDIA Control Panel - Prefer Maximum Performance
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "PerfLevelSrc",
                "REG_DWORD",
                "8738",
                "Set NVIDIA to prefer maximum performance",
            ),
            # Disable NVIDIA Telemetry
            (
                r"HKLM\SOFTWARE\NVIDIA Corporation\NvControlPanel2\Client",
                "OptInOrOutPreference",
                "REG_DWORD",
                "0",
                "Disabled NVIDIA telemetry",
            ),
            # Disable NVIDIA GameStream
            (
                r"HKLM\SOFTWARE\NVIDIA Corporation\Global\GfExperience",
                "GameStream",
                "REG_DWORD",
                "0",
                "Disabled NVIDIA GameStream",
            ),
            # Shader cache optimization
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "ShaderCacheSizeInMB",
                "REG_DWORD",
                "4096",
                "Increased NVIDIA shader cache to 4GB",
            ),
            # Power management mode - prefer max performance
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "PowerMizerEnable",
                "REG_DWORD",
                "1",
                "Enabled NVIDIA PowerMizer",
            ),
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "PowerMizerLevel",
                "REG_DWORD",
                "1",
                "Set NVIDIA PowerMizer to max performance",
            ),
            # Enable threaded optimization
            (
                r"HKLM\SOFTWARE\NVIDIA Corporation\Global\NVTweak",
                "Threaded optimization",
                "REG_DWORD",
                "1",
                "Enabled NVIDIA threaded optimization",
            ),
            # Disable NVIDIA overlay
            (
                r"HKCU\SOFTWARE\NVIDIA Corporation\Global\ShadowPlay\NVSPCAPS",
                "{1B4A1DA5-4E40-4DE7-8307-6C5F6CB8E2B6}",
                "REG_DWORD",
                "0",
                "Disabled NVIDIA overlay (reduces input lag)",
            ),
            # Set texture filtering to high performance
            (
                r"HKLM\SOFTWARE\NVIDIA Corporation\Global\NVTweak",
                "TextureFilterQuality",
                "REG_DWORD",
                "0",
                "Set texture filtering to high performance",
            ),
        ]

        for reg_path, name, reg_type, value, description in tweaks:
            success, msg = set_registry(reg_path, name, value, reg_type)
            if success:
                results["actions"].append(description)
                self.log(f"  NVIDIA: {description}", "success")
            else:
                self.log(f"  NVIDIA: {description} (may need admin)", "warning")

        # Disable NVIDIA telemetry tasks
        nvidia_tasks = [
            "NvTmRepOnLogon_{B2FE1952-0186-46C3-BAEC-A80AA35AC5B8}",
            "NvTmRep_{B2FE1952-0186-46C3-BAEC-A80AA35AC5B8}",
            "NvTmMon_{B2FE1952-0186-46C3-BAEC-A80AA35AC5B8}",
        ]
        for task in nvidia_tasks:
            try:
                subprocess.run(
                    ["schtasks", "/change", "/tn", task, "/disable"],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
        results["actions"].append("Disabled NVIDIA telemetry scheduled tasks")

        return results

    # ─── AMD Optimizations ──────────────────────────────────────────

    def optimize_amd(self):
        """Apply AMD-specific optimizations."""
        results = {"actions": [], "success": True, "brand": "AMD"}

        if not self.is_windows:
            return results

        tweaks = [
            # AMD Radeon - Performance mode
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "EnableUlps",
                "REG_DWORD",
                "0",
                "Disabled AMD ULPS (Ultra Low Power State) for stability",
            ),
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "EnableCrossFireAutoLink",
                "REG_DWORD",
                "0",
                "Disabled AMD CrossFire auto-link",
            ),
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "PP_ThermalAutoThrottlingEnable",
                "REG_DWORD",
                "0",
                "Disabled AMD thermal auto-throttling",
            ),
            # Disable AMD overlay
            (
                r"HKLM\SOFTWARE\AMD\CN",
                "SWLAYERS_ENABLE",
                "REG_SZ",
                "0",
                "Disabled AMD Radeon overlay",
            ),
            # Anti-Lag
            (
                r"HKLM\SOFTWARE\AMD\CN",
                "AntiLag",
                "REG_DWORD",
                "1",
                "Enabled AMD Anti-Lag (reduces input latency)",
            ),
            # Disable Radeon Chill (can limit FPS)
            (
                r"HKLM\SOFTWARE\AMD\CN",
                "RadeonChill",
                "REG_DWORD",
                "0",
                "Disabled AMD Radeon Chill (prevents FPS limiting)",
            ),
            # Image sharpening
            (
                r"HKLM\SOFTWARE\AMD\CN",
                "RIS",
                "REG_DWORD",
                "1",
                "Enabled AMD Radeon Image Sharpening",
            ),
            # Shader cache on
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000\UMD",
                "ShaderCache",
                "REG_DWORD",
                "1",
                "Enabled AMD shader cache",
            ),
            # High performance power profile
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "KMD_FRCGFEnabled",
                "REG_DWORD",
                "0",
                "Disabled AMD Frame Rate Target Control for max FPS",
            ),
            # Disable power efficiency
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "KMD_DeLagEnabled",
                "REG_DWORD",
                "1",
                "Enabled AMD DeLag for reduced input delay",
            ),
        ]

        for reg_path, name, reg_type, value, description in tweaks:
            success, msg = set_registry(reg_path, name, value, reg_type)
            if success:
                results["actions"].append(description)
                self.log(f"  AMD: {description}", "success")
            else:
                self.log(f"  AMD: {description} (may need admin)", "warning")

        return results

    # ─── Intel Optimizations ────────────────────────────────────────

    def optimize_intel(self):
        """Apply Intel GPU-specific optimizations."""
        results = {"actions": [], "success": True, "brand": "Intel"}

        if not self.is_windows:
            return results

        tweaks = [
            # Intel Graphics - Maximum Performance
            (
                r"HKLM\SOFTWARE\Intel\GMM",
                "DedicatedSegmentSize",
                "REG_DWORD",
                "512",
                "Increased Intel dedicated GPU memory to 512MB",
            ),
            # Disable Intel power-saving for graphics
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "FeatureTestControl",
                "REG_DWORD",
                "9a40",
                "Disabled Intel GPU power-saving features",
            ),
            # Force maximum performance
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "AdaptiveVsyncEnable",
                "REG_DWORD",
                "0",
                "Disabled Intel Adaptive VSync",
            ),
            # Disable Intel panel self-refresh
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "Disable_OverlayDSQualityEnhancement",
                "REG_DWORD",
                "1",
                "Disabled Intel overlay quality enhancement (reduces latency)",
            ),
            # Set to performance mode
            (
                r"HKLM\SOFTWARE\Intel\Display\igfxcui\profiles\Media\Brighten Movie",
                "ProcAmpBrightness",
                "REG_DWORD",
                "0",
                "Set Intel display processing to neutral",
            ),
            # Disable Intel power conservation
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "ACPowerPolicyVersion",
                "REG_DWORD",
                "16898",
                "Set Intel GPU to maximum performance power policy",
            ),
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "DCPowerPolicyVersion",
                "REG_DWORD",
                "16642",
                "Optimized Intel GPU battery power policy",
            ),
        ]

        for reg_path, name, reg_type, value, description in tweaks:
            success, msg = set_registry(reg_path, name, value, reg_type)
            if success:
                results["actions"].append(description)
                self.log(f"  Intel: {description}", "success")
            else:
                self.log(f"  Intel: {description} (may need admin)", "warning")

        return results

    # ─── Auto-detect and optimize ───────────────────────────────────

    def auto_optimize(self):
        """Detect GPU brand and apply matching optimizations."""
        brand, name = self.detect_gpu_brand()
        self.log(f"Detected GPU: {name} (Brand: {brand})", "info")

        optimize_map = {
            "NVIDIA": self.optimize_nvidia,
            "AMD": self.optimize_amd,
            "Intel": self.optimize_intel,
        }

        func = optimize_map.get(brand)
        if func:
            results = func()
            results["gpu_name"] = name
            return results

        return {
            "actions": ["GPU brand not recognized - applied generic optimizations only"],
            "success": True,
            "brand": brand,
            "gpu_name": name,
        }

    def get_brand_info(self):
        """Get detected GPU brand and name."""
        if not self._detected_brand:
            self.detect_gpu_brand()
        return self._detected_brand or "Unknown", self._gpu_name or "Unknown"

    # ─── Selectable plan / apply (for the GPU dropdown with checkboxes) ──

    def plan(self) -> dict:
        """Detected brand + the list of tweaks it *would* apply (no changes made)."""
        brand, name = self.detect_gpu_brand()
        tweaks = BRAND_TWEAKS.get(brand, [])
        items = [{"id": f"{brand.lower()}_{i}", "label": t[4]} for i, t in enumerate(tweaks)]
        return {"brand": brand, "gpu_name": name, "tweaks": items}

    def apply_selected(self, selected: list[str] | None = None) -> dict:
        """Apply only the chosen GPU tweaks (by id). ``None`` applies them all."""
        brand, name = self.detect_gpu_brand()
        results = {"actions": [], "skipped": 0, "success": True, "brand": brand, "gpu_name": name}
        if not self.is_windows:
            return results
        chosen = set(selected) if selected is not None else None
        for i, (reg_path, value_name, reg_type, value, description) in enumerate(
            BRAND_TWEAKS.get(brand, [])
        ):
            if chosen is not None and f"{brand.lower()}_{i}" not in chosen:
                results["skipped"] += 1
                continue
            ok, _msg = set_registry(reg_path, value_name, value, reg_type)
            if ok:
                results["actions"].append(description)
                self.log(f"  {brand}: {description}", "success")
            else:
                self.log(f"  {brand}: {description} (puede requerir admin)", "warning")
        return results
