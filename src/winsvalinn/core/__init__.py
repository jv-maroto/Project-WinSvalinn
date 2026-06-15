"""WinSvalinn Core - Backend engines (no GUI imports)."""

from . import autoruns, process_tree
from .ai_windows import AIWindowsRemover
from .bandwidth_monitor import BandwidthMonitor
from .bloatware_remover import BloatwareRemover
from .browser_cleanup import BrowserCleanup
from .change_log import ChangeLogger
from .defender_control import DefenderControl
from .disk_health import DiskHealthMonitor
from .dns_manager import DNSManager
from .driver_manager import DriverManager
from .dry_run import DryRunContext, disable_dry_run, enable_dry_run, is_dry_run
from .environment_manager import EnvironmentManager
from .features_manager import FeaturesManager
from .firewall_manager import FirewallManager
from .gpu import GPUBrandOptimizer
from .hardware_info import HardwareAnalyzer
from .hosts_manager import HostsManager
from .network_diagnostics import NetworkDiagnostics
from .optimization import SystemOptimizer
from .package_manager import PackageManager
from .privacy_cleaner import PrivacyCleaner
from .ram import RAMOptimizer
from .registry_backup import RegistryBackupManager
from .restore_point import RestorePointManager
from .security import SecurityScanner
from .security_audit import SecurityAudit
from .telemetry_blocker import TelemetryBlocker
from .thermal_monitor import ThermalMonitor
from .update_control import UpdateControl
from .vpn_detector import VPNProxyDetector

__all__ = [
    "SecurityScanner",
    "SystemOptimizer",
    "GPUBrandOptimizer",
    "RAMOptimizer",
    "DefenderControl",
    "FirewallManager",
    "SecurityAudit",
    "BloatwareRemover",
    "TelemetryBlocker",
    "DNSManager",
    "HostsManager",
    "PackageManager",
    "UpdateControl",
    "FeaturesManager",
    "AIWindowsRemover",
    "RestorePointManager",
    "RegistryBackupManager",
    "ChangeLogger",
    "DiskHealthMonitor",
    "HardwareAnalyzer",
    "DriverManager",
    "ThermalMonitor",
    "NetworkDiagnostics",
    "VPNProxyDetector",
    "BandwidthMonitor",
    "BrowserCleanup",
    "PrivacyCleaner",
    "EnvironmentManager",
    "DryRunContext",
    "is_dry_run",
    "enable_dry_run",
    "disable_dry_run",
    "process_tree",
    "autoruns",
]
