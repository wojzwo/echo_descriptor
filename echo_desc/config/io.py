from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os
import shutil


APP_NAME = "echo_desc"


@dataclass(frozen=True)
class ConfigPaths:
    """
    Repo-local config dir by default:
      <repo_root>/config/

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

        # default: repo-root/config
        # package_root = .../<repo_root>/echo_desc
        repo_root = Path(__file__).resolve().parents[2]
        return ConfigPaths(base_dir=(repo_root / "config").resolve())

    def file(self, rel: str) -> Path:
        return (self.base_dir / rel).resolve()


def package_root() -> Path:
    """
    Absolute path to python package directory: .../<repo_root>/echo_desc
    """
    return Path(__file__).resolve().parents[1]


def defaults_dir() -> Path:
    """
    Absolute path: .../<repo_root>/echo_desc/config_defaults
    """
    return (package_root() / "config_defaults").resolve()


def ensure_bootstrap_file(rel: str) -> Path:
    """
    Ensure repo-local config has <repo_root>/config/<rel>.
    If missing, copy from packaged defaults: <repo_root>/echo_desc/config_defaults/<rel>.

    Returns: local path.
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


def ensure_bootstrap_tree() -> None:
    """
    Copies entire echo_desc/config_defaults/** into repo-local config dir
    (<repo_root>/config/**) but only for files that do not exist yet.
    """
    cfg = ConfigPaths.resolve()
    src_root = defaults_dir()
    dst_root = cfg.base_dir

    if not src_root.exists():
        raise FileNotFoundError(f"Defaults dir not found: {src_root}")

    for src in src_root.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(src_root)
        dst = (dst_root / rel).resolve()
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


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
    try:
        import yaml  # type: ignore
    except Exception as e:
        raise RuntimeError("PyYAML is required. Install: pip install pyyaml") from e
    return yaml.safe_load(read_text(path))


def save_yaml(path: Path, data: Any) -> None:
    try:
        import yaml  # type: ignore
    except Exception as e:
        raise RuntimeError("PyYAML is required. Install: pip install pyyaml") from e

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
