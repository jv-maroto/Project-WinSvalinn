"""
Hardware Information Analyzer for WinSvalinn.

Comprehensive hardware details via WMI queries: BIOS, motherboard,
CPU, RAM slots, battery, network adapters, USB devices.
"""

import json
import platform
import subprocess

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("HardwareInfo")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class HardwareAnalyzer:
    """Comprehensive hardware information via WMI."""

    def __init__(self, callback=None):
        self._callback = callback or (lambda msg, level="info": None)

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _wmi_query(self, wmi_class, properties, timeout=20):
        """Generic WMI query helper. Returns list of dicts."""
        props = ", ".join(properties)
        cmd = (
            f"Get-CimInstance -ClassName {wmi_class} | "
            f"Select-Object {props} | ConvertTo-Json -Compress"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout.strip())
                if isinstance(data, dict):
                    data = [data]
                return data
            return []
        except Exception as e:
            logger.error(f"WMI query {wmi_class} failed: {e}")
            return []

    def get_bios_info(self):
        """
        BIOS/UEFI information.

        Returns:
            dict: manufacturer, version, date, serial, smbios_version
        """
        if not IS_WINDOWS:
            return {}

        data = self._wmi_query(
            "Win32_BIOS",
            ["Manufacturer", "Name", "Version", "SMBIOSBIOSVersion", "ReleaseDate", "SerialNumber"],
        )
        if not data:
            return {}

        b = data[0]
        release_date = b.get("ReleaseDate", "")
        # Parse WMI datetime if needed
        if release_date and "/Date(" in str(release_date):
            try:
                ts = int(str(release_date).split("(")[1].split(")")[0][:10])
                from datetime import datetime

                release_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            except Exception:
                pass

        return {
            "manufacturer": b.get("Manufacturer", "Unknown"),
            "name": b.get("Name", "Unknown"),
            "version": b.get("Version", "Unknown"),
            "smbios_version": b.get("SMBIOSBIOSVersion", "Unknown"),
            "release_date": release_date,
            "serial_number": b.get("SerialNumber", "N/A"),
        }

    def get_motherboard_info(self):
        """
        Motherboard information.

        Returns:
            dict: manufacturer, product, version, serial
        """
        if not IS_WINDOWS:
            return {}

        data = self._wmi_query(
            "Win32_BaseBoard", ["Manufacturer", "Product", "Version", "SerialNumber"]
        )
        if not data:
            return {}

        m = data[0]
        return {
            "manufacturer": m.get("Manufacturer", "Unknown"),
            "product": m.get("Product", "Unknown"),
            "version": m.get("Version", ""),
            "serial_number": m.get("SerialNumber", "N/A"),
        }

    def get_cpu_detailed(self):
        """
        Detailed CPU information.

        Returns:
            dict: model, cores, threads, speed, cache, architecture, etc.
        """
        if not IS_WINDOWS:
            return {}

        data = self._wmi_query(
            "Win32_Processor",
            [
                "Name",
                "Manufacturer",
                "NumberOfCores",
                "NumberOfLogicalProcessors",
                "MaxClockSpeed",
                "CurrentClockSpeed",
                "L2CacheSize",
                "L3CacheSize",
                "Architecture",
                "ProcessorId",
                "SocketDesignation",
                "CurrentVoltage",
                "Description",
            ],
        )
        if not data:
            return {}

        c = data[0]
        arch_map = {0: "x86", 1: "MIPS", 5: "ARM", 6: "Itanium", 9: "x64", 12: "ARM64"}
        arch_code = c.get("Architecture", -1)

        return {
            "model": c.get("Name", "Unknown").strip(),
            "manufacturer": c.get("Manufacturer", "Unknown"),
            "cores": c.get("NumberOfCores", 0),
            "threads": c.get("NumberOfLogicalProcessors", 0),
            "max_speed_mhz": c.get("MaxClockSpeed", 0),
            "current_speed_mhz": c.get("CurrentClockSpeed", 0),
            "l2_cache_kb": c.get("L2CacheSize", 0),
            "l3_cache_kb": c.get("L3CacheSize", 0),
            "architecture": arch_map.get(arch_code, f"Unknown ({arch_code})"),
            "socket": c.get("SocketDesignation", "N/A"),
            "voltage": c.get("CurrentVoltage"),
            "description": c.get("Description", ""),
        }

    def get_ram_slots(self):
        """
        RAM module details per slot.

        Returns:
            dict: total_slots, used_slots, modules: list[dict]
        """
        if not IS_WINDOWS:
            return {"total_slots": 0, "used_slots": 0, "modules": []}

        data = self._wmi_query(
            "Win32_PhysicalMemory",
            [
                "BankLabel",
                "DeviceLocator",
                "Capacity",
                "Speed",
                "MemoryType",
                "SMBIOSMemoryType",
                "Manufacturer",
                "PartNumber",
                "SerialNumber",
                "ConfiguredClockSpeed",
            ],
        )

        # Get total slots from PhysicalMemoryArray
        slots_data = self._wmi_query("Win32_PhysicalMemoryArray", ["MemoryDevices"])
        total_slots = 0
        if slots_data:
            total_slots = slots_data[0].get("MemoryDevices", 0) or 0

        ddr_map = {
            20: "DDR",
            21: "DDR2",
            22: "DDR2",
            24: "DDR3",
            26: "DDR4",
            30: "DDR5",
            34: "DDR5",
        }

        modules = []
        for m in data:
            cap = m.get("Capacity", 0) or 0
            smbios_type = m.get("SMBIOSMemoryType", 0) or 0
            ddr_type = ddr_map.get(smbios_type, f"Type {smbios_type}")

            modules.append(
                {
                    "bank": m.get("BankLabel", "N/A"),
                    "locator": m.get("DeviceLocator", "N/A"),
                    "capacity_gb": round(cap / (1024**3), 1) if cap else 0,
                    "speed_mhz": m.get("Speed", 0) or 0,
                    "configured_speed_mhz": m.get("ConfiguredClockSpeed", 0) or 0,
                    "type": ddr_type,
                    "manufacturer": (m.get("Manufacturer") or "Unknown").strip(),
                    "part_number": (m.get("PartNumber") or "N/A").strip(),
                    "serial": (m.get("SerialNumber") or "N/A").strip(),
                }
            )

        return {
            "total_slots": total_slots,
            "used_slots": len(modules),
            "free_slots": max(0, total_slots - len(modules)),
            "total_gb": sum(m["capacity_gb"] for m in modules),
            "modules": modules,
        }

    def get_battery_info(self):
        """
        Battery information (laptops).

        Returns:
            dict or None: capacity, cycles, status, estimated_runtime
        """
        if not IS_WINDOWS:
            return None

        data = self._wmi_query(
            "Win32_Battery",
            [
                "Name",
                "Status",
                "BatteryStatus",
                "EstimatedChargeRemaining",
                "EstimatedRunTime",
                "DesignCapacity",
                "FullChargeCapacity",
            ],
        )

        if not data:
            return None

        b = data[0]
        status_map = {
            1: "Discharging",
            2: "AC Power",
            3: "Fully Charged",
            4: "Low",
            5: "Critical",
            6: "Charging",
            7: "Charging & High",
            8: "Charging & Low",
            9: "Charging & Critical",
            10: "Undefined",
            11: "Partially Charged",
        }

        design_cap = b.get("DesignCapacity", 0) or 0
        full_cap = b.get("FullChargeCapacity", 0) or 0
        health_pct = round((full_cap / design_cap * 100), 1) if design_cap > 0 else None

        return {
            "name": b.get("Name", "Battery"),
            "status": b.get("Status", "Unknown"),
            "battery_status": status_map.get(b.get("BatteryStatus", 10), "Unknown"),
            "charge_remaining": b.get("EstimatedChargeRemaining", 0),
            "estimated_runtime_min": b.get("EstimatedRunTime", 0),
            "design_capacity_mwh": design_cap,
            "full_charge_capacity_mwh": full_cap,
            "health_percent": health_pct,
        }

    def get_network_adapters(self):
        """
        Network adapter details.

        Returns:
            list[dict]: Per-adapter info
        """
        if not IS_WINDOWS:
            return []

        data = self._wmi_query(
            "Win32_NetworkAdapter",
            ["Name", "MACAddress", "Speed", "NetConnectionStatus", "AdapterType", "Manufacturer"],
        )

        status_map = {
            0: "Disconnected",
            1: "Connecting",
            2: "Connected",
            3: "Disconnecting",
            4: "Hardware not present",
            5: "Hardware disabled",
            6: "Hardware malfunction",
            7: "Media disconnected",
            8: "Authenticating",
            9: "Authentication succeeded",
        }

        adapters = []
        for a in data:
            mac = a.get("MACAddress")
            if not mac:
                continue
            speed = a.get("Speed", 0) or 0
            speed_mbps = round(speed / 1_000_000) if speed > 0 else 0

            adapters.append(
                {
                    "name": a.get("Name", "Unknown"),
                    "mac": mac,
                    "speed_mbps": speed_mbps,
                    "status": status_map.get(a.get("NetConnectionStatus"), "Unknown"),
                    "type": a.get("AdapterType", "Unknown"),
                    "manufacturer": a.get("Manufacturer", "Unknown"),
                }
            )

        return adapters

    def get_usb_devices(self):
        """
        Connected USB devices.

        Returns:
            list[dict]: Per-device info
        """
        if not IS_WINDOWS:
            return []

        self._wmi_query("Win32_USBControllerDevice", ["Dependent"])

        # Get PnP device details for USB devices
        cmd = (
            "Get-PnpDevice -Class USB -Status OK -ErrorAction SilentlyContinue | "
            "Select-Object FriendlyName, Manufacturer, DeviceID, Status "
            "| ConvertTo-Json -Compress"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode == 0 and result.stdout.strip():
                devices_raw = json.loads(result.stdout.strip())
                if isinstance(devices_raw, dict):
                    devices_raw = [devices_raw]

                devices = []
                for d in devices_raw:
                    name = d.get("FriendlyName", "Unknown USB Device")
                    if "Root Hub" in name or "Host Controller" in name:
                        continue
                    devices.append(
                        {
                            "name": name,
                            "manufacturer": d.get("Manufacturer", "Unknown"),
                            "device_id": d.get("DeviceID", ""),
                            "status": d.get("Status", "Unknown"),
                        }
                    )
                return devices
        except Exception:
            pass

        return []

    def get_gpu_info(self):
        """
        GPU details.

        Returns:
            list[dict]: Per-GPU info
        """
        if not IS_WINDOWS:
            return []

        data = self._wmi_query(
            "Win32_VideoController",
            [
                "Name",
                "AdapterRAM",
                "DriverVersion",
                "DriverDate",
                "VideoProcessor",
                "CurrentRefreshRate",
                "CurrentHorizontalResolution",
                "CurrentVerticalResolution",
                "Status",
            ],
        )

        gpus = []
        for g in data:
            vram = g.get("AdapterRAM", 0) or 0
            vram_gb = round(vram / (1024**3), 1) if vram > 0 else 0

            resolution = ""
            h = g.get("CurrentHorizontalResolution")
            v = g.get("CurrentVerticalResolution")
            if h and v:
                resolution = f"{h}x{v}"

            gpus.append(
                {
                    "name": g.get("Name", "Unknown"),
                    "vram_gb": vram_gb,
                    "driver_version": g.get("DriverVersion", "N/A"),
                    "processor": g.get("VideoProcessor", "N/A"),
                    "refresh_rate": g.get("CurrentRefreshRate", 0),
                    "resolution": resolution,
                    "status": g.get("Status", "Unknown"),
                }
            )

        return gpus

    def generate_full_report(self):
        """
        Generate a complete hardware report.

        Returns:
            dict: All hardware information combined
        """
        self._log("Generating full hardware report...")

        report = {
            "bios": self.get_bios_info(),
            "motherboard": self.get_motherboard_info(),
            "cpu": self.get_cpu_detailed(),
            "ram": self.get_ram_slots(),
            "gpu": self.get_gpu_info(),
            "battery": self.get_battery_info(),
            "network_adapters": self.get_network_adapters(),
            "usb_devices": self.get_usb_devices(),
        }

        self._log("Hardware report complete")
        return report
