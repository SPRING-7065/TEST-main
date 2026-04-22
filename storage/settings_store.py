"""
应用级设置持久化
存储位置：app_settings.json（与 tasks.json 同目录）
"""
import json
import os
import sys
from typing import Any, Dict


def _settings_path() -> str:
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "app_settings.json")


DEFAULTS: Dict[str, Any] = {
    "concurrency_limit": 2,
    "auto_minimize_on_picker": True,
}


def load_settings() -> Dict[str, Any]:
    path = _settings_path()
    if not os.path.exists(path):
        return dict(DEFAULTS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception:
        return dict(DEFAULTS)
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in data.items() if k in DEFAULTS})
    return merged


def save_settings(settings: Dict[str, Any]) -> None:
    path = _settings_path()
    to_write = {k: settings.get(k, DEFAULTS[k]) for k in DEFAULTS}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(to_write, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_setting(key: str) -> Any:
    return load_settings().get(key, DEFAULTS.get(key))


def update_setting(key: str, value: Any) -> None:
    s = load_settings()
    s[key] = value
    save_settings(s)
