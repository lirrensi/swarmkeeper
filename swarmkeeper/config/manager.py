"""Configuration and session registry management."""

import json
import os
from pathlib import Path


def get_swarmkeeper_dir() -> Path:
    """Get the swarmkeeper directory path (~/swarmkeeper)."""
    home = Path.home()
    return home / "swarmkeeper"


def get_config_path() -> Path:
    """Returns path to ~/swarmkeeper/config.json."""
    return get_swarmkeeper_dir() / "config.json"


def get_sessions_path() -> Path:
    """Returns path to ~/swarmkeeper/sessions.json."""
    return get_swarmkeeper_dir() / "sessions.json"


def ensure_swarmkeeper_dir() -> None:
    """Create ~/swarmkeeper directory if not exists."""
    swarmkeeper_dir = get_swarmkeeper_dir()
    swarmkeeper_dir.mkdir(parents=True, exist_ok=True)


def get_default_config() -> dict:
    """Get default configuration."""
    return {
        "apiBase": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "apiKey": "",
        "params": {"temperature": 0.2},
    }


def load_config() -> dict:
    """Load config from disk or create default."""
    ensure_swarmkeeper_dir()
    config_path = get_config_path()

    if not config_path.exists():
        default_config = get_default_config()
        save_config(default_config)
        return default_config

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # If file is corrupted, return default
        return get_default_config()


def save_config(config: dict) -> None:
    """Save config to disk."""
    ensure_swarmkeeper_dir()
    config_path = get_config_path()

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def load_sessions() -> dict:
    """Load sessions registry from disk."""
    ensure_swarmkeeper_dir()
    sessions_path = get_sessions_path()

    if not sessions_path.exists():
        return {}

    try:
        with open(sessions_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_sessions(sessions: dict) -> None:
    """Save sessions registry to disk."""
    ensure_swarmkeeper_dir()
    sessions_path = get_sessions_path()

    with open(sessions_path, "w") as f:
        json.dump(sessions, f, indent=2)
