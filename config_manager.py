"""Centralised YAML configuration management for Telegram Media Downloader."""

import logging
import os
from typing import Any, Dict

import yaml

logger = logging.getLogger("media_downloader")

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(THIS_DIR, "config.yaml")


def load_config() -> Dict[str, Any]:
    """Read ``config.yaml`` from disk and return the parsed dict."""
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f) or {}


def save_config(config: Dict[str, Any]) -> None:
    """Write *config* to ``config.yaml`` (full overwrite)."""
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, sort_keys=False, default_flow_style=False)
