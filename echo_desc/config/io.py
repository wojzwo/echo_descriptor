# echo_desc/config/io.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os
import shutil


APP_NAME = "echo_desc"


def _xdg_config_home() -> Path:
    x = os.environ.get("XDG_CONFIG_HOME", "").strip()
    if x:
        return Path(x).expanduser()
    return Path.home() / ".config"


@dataclass(frozen=True)
class ConfigPaths:
    """
    Local (user) config dir by default (outside repo):
      ~/.config/echo_desc/

    Override with env:
      ECHO_DESC_CONFIG_DIR=/some/path
    """
    base_dir: Path

    @staticmethod
    def resolve() -> "ConfigPaths":
        # env override first
        env = os.environ.get("ECHO_DESC_CONFIG_DIR", "").strip()
        if env:
            return ConfigPaths(base_dir=Path(env).expanduser().resolve())

        # default: user-local config directory
        return ConfigPaths(base_dir=(_xdg_config_home() / APP_NAME).resolve())

    def file(self, rel: str) -> Path:
        return (self.base_dir / rel).resolve()


def package_root() -> Path:
    """
    Returns path to the python package directory: .../echo_desc
    """
    return Path(__file__).resolve().parents[1]


def defaults_dir() -> Path:
    """
    Returns path to packaged defaults: .../echo_desc/config_defaults
    """
    return (package_root() / "config_defaults").resolve()


def ensure_bootstrap_file(rel: str) -> Path:
    """
    Return LOCAL config path for rel.
    If missing, bootstrap-copy from packaged defaults.

    rel examples:
      "parameters/pettersen_detroit.yaml"
      "reports/templates.yaml"
    """
    cfg = ConfigPaths.resolve()
    dst = cfg.file(rel)
    if dst.exists():
        return dst

    src = (defaults_dir() / rel).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Missing default config file: {src}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def read_text(path: Path, encoding: str = "utf-8") -> str:
    return path.read_text(encoding=encoding)


def write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding=encoding)


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def save_json(path: Path, data: Any, indent: int = 2) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=indent) + "\n")


def load_yaml(path: Path) -> Any:
    """
    Requires PyYAML: pip install pyyaml
    """
    try:
        import yaml  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "PyYAML is required to load YAML configs. Install: pip install pyyaml"
        ) from e

    return yaml.safe_load(read_text(path))


def save_yaml(path: Path, data: Any) -> None:
    """
    Requires PyYAML: pip install pyyaml
    """
    try:
        import yaml  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "PyYAML is required to save YAML configs. Install: pip install pyyaml"
        ) from e

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
