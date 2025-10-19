# app/config.py
"""Configuration management for GripLab application."""

import yaml
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict
from utils.logger import logger


@dataclass
class AppConfig:
    """Application configuration container."""

    theme: str = "dark"
    unit_system: str = "USCS"
    sign_convention: str = "ISO"
    demo_mode: bool = False
    colorway: str = "G10"
    colormap: str = "Jet"
    data_dir: str = ""

    @classmethod
    def from_yaml(cls, filepath: str) -> "AppConfig":
        """Load configuration from YAML file."""
        try:
            with open(filepath) as f:
                data = yaml.safe_load(f)
                return cls(
                    theme=data.get("theme", "dark"),
                    unit_system=data.get("unit_system", "USCS"),
                    sign_convention=data.get("sign_convention", "ISO"),
                    demo_mode=data.get("demo_mode", False),
                    colorway=data.get("plotting", {}).get("colorway", "G10"),
                    colormap=data.get("plotting", {}).get("colormap", "Jet"),
                    data_dir=data.get("paths", {}).get("data_dir", str(Path.cwd())),
                )
        except FileNotFoundError:
            logger.warning(f"Config file {filepath} not found, using defaults")
            config = cls(data_dir=str(Path.cwd()))
            return config

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary for YAML export."""
        return {
            "theme": self.theme,
            "unit_system": self.unit_system,
            "sign_convention": self.sign_convention,
            "demo_mode": self.demo_mode,
            "plotting": {
                "colorway": self.colorway,
                "colormap": self.colormap,
            },
            "paths": {
                "data_dir": self.data_dir,
            },
        }

    def save(self, filepath: str):
        """Save configuration to YAML file."""
        try:
            with open(filepath, "w") as f:
                yaml.dump(self.to_dict(), f)
            logger.info(f"Settings saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)
