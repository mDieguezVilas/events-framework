import os
import yaml
from typing import Any
from pathlib import Path


def load_config(path: str = "config.yaml") -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_sources_package(config: dict[str, Any]) -> str:
    return config.get("sources_package", "")


def get_storage_config(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("storage", {"type": "csv", "data_dir": "data"})


def get_enabled_sources(config: dict[str, Any]) -> list[str]:
    sources = config.get("sources", {})
    return [sid for sid, cfg in sources.items() if cfg.get("enabled", True)]


def get_telegram_config(config: dict[str, Any]) -> dict[str, Any] | None:
    notif = config.get("notifications", {})
    tg = notif.get("telegram", {})
    if not tg.get("enabled", False):
        return None
    token = os.getenv(tg.get("token_env", "TELEGRAM_TOKEN"))
    chat_id = os.getenv(tg.get("chat_id_env", "TELEGRAM_CHAT_ID"))
    if not token or not chat_id:
        return None
    return {"token": token, "chat_id": chat_id}