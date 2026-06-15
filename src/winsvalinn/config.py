"""
Configuration loader for WinSvalinn.

Loads and validates configuration from config.json.
"""

import json
import os

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("Config")


class Config:
    """Application configuration manager."""

    DEFAULT_CONFIG = {
        "security": {
            "port_scan_range": [1, 1024],
            "port_scan_timeout": 0.5,
            "port_scan_workers": 100,
            "suspicious_ports": [4444, 5555, 6666, 7777, 8888, 9999, 1337, 31337],
            "suspicious_tlds": [".ru", ".cn", ".tk", ".ml", ".ga"],
            "process_whitelist": ["svchost.exe", "csrss.exe", "explorer.exe"],
        },
        "optimization": {
            "disabled_services": ["DiagTrack", "dmwappushservice"],
            "visual_effects_mode": "performance",
            "power_plan": "ultimate",
        },
        "ui": {
            "theme": "github-dark",
            "language": "es",
            "show_advanced_options": False,
            "confirm_destructive_actions": True,
            "first_run_done": False,
            "dry_run_default": False,
            "show_activity_log": False,
        },
        "logging": {
            "level": "INFO",
            "file": "winsvalinn.log",
            "folder": "",
            "max_size_mb": 10,
            "backup_count": 3,
        },
        "telemetry": {"opt_in": False},
        "integrations": {"virustotal_api_key": ""},
        "performance": {"enable_threading": True, "max_workers": 100, "scan_timeout": 30},
    }

    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.data = self._load_config()

    def _load_config(self):
        """Load configuration from file or use defaults."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    user_config = json.load(f)
                    logger.info(f"Loaded configuration from {self.config_file}")
                    return self._deep_merge(self.DEFAULT_CONFIG.copy(), user_config)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config file: {e}")
                logger.warning("Using default configuration")
                return self.DEFAULT_CONFIG.copy()
            except Exception as e:
                logger.exception(f"Error loading config: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            logger.info(f"Config file not found, creating default: {self.config_file}")
            self.save()
            return self.DEFAULT_CONFIG.copy()

    def _deep_merge(self, base, override):
        """Deep merge two dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def get(self, *keys, default=None):
        """
        Get nested configuration value.

        Example:
            >>> config = Config()
            >>> port_range = config.get("security", "port_scan_range")
        """
        value = self.data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default

    def set(self, *keys, value):
        """Set nested configuration value."""
        if len(keys) == 0:
            return

        current = self.data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
        logger.info(f"Config updated: {'.'.join(keys)} = {value}")

    def save(self, config_file=None):
        """Save configuration to file."""
        target_file = config_file or self.config_file
        try:
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {target_file}")
            return True
        except Exception as e:
            logger.exception(f"Failed to save config: {e}")
            return False

    def reload(self):
        """Reload configuration from file."""
        self.data = self._load_config()
        logger.info("Configuration reloaded")


# Global config instance
_config = None


def get_config():
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
