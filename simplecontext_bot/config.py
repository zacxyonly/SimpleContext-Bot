"""
config.py — Config manager
Read/write config.yaml untuk SimpleContext-Bot.
"""

import os
import json
from pathlib import Path


# Default install directory
DEFAULT_DIR = Path.home() / ".simplecontext-bot"

# Config file path
CONFIG_FILE = DEFAULT_DIR / "config.json"


DEFAULT_CONFIG = {
    "version": "1.0.0",
    "install_dir": str(DEFAULT_DIR),
    "telegram": {
        "token": "",
    },
    "llm": {
        "provider": "gemini",        # gemini | openai | ollama
        "model": "",
        "api_key": "",
        "base_url": "",              # untuk ollama / custom
    },
    "simplecontext": {
        "engine_dir": str(DEFAULT_DIR / "simplecontext"),
        "agents_dir": str(DEFAULT_DIR / "agents"),
        "db_path":    str(DEFAULT_DIR / "bot.db"),
        "hot_reload": True,
        "default_agent": "general",
    },
    "plugins": {
        "enabled": False,
        "installed": [],
        "configs": {}
    },
    "bot": {
        "debug": False,
        "memory_limit": 20,
        "max_tokens":    2048,
        "compression_threshold": 50,
    }
}


def load() -> dict:
    """Load config dari file. Return default jika belum ada."""
    if not CONFIG_FILE.exists():
        return dict(DEFAULT_CONFIG)
    with open(CONFIG_FILE) as f:
        data = json.load(f)
    # Merge dengan default agar key baru tidak hilang
    return _deep_merge(DEFAULT_CONFIG, data)


def save(cfg: dict):
    """Simpan config ke file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def get(key: str, default=None):
    """Ambil nilai config dengan dot notation. Contoh: get('llm.provider')"""
    cfg = load()
    parts = key.split(".")
    node = cfg
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def set_value(key: str, value):
    """Set nilai config dengan dot notation."""
    cfg = load()
    parts = key.split(".")
    node = cfg
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    save(cfg)


def is_configured() -> bool:
    """Cek apakah config sudah diisi."""
    cfg = load()
    return bool(
        cfg.get("telegram", {}).get("token") and
        cfg.get("llm", {}).get("api_key") or cfg.get("llm", {}).get("provider") == "ollama"
    )


def _deep_merge(base: dict, override: dict) -> dict:
    import copy
    result = copy.deepcopy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result
