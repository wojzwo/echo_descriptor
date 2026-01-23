#!/usr/bin/env python3
# scripts/sync_config_defaults.py
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _safe_clear_dir(dst: Path) -> None:
    """Remove all children of dst (but keep dst itself)."""
    dst.mkdir(parents=True, exist_ok=True)
    for child in dst.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink(missing_ok=True)


def _replace_one(src_item: Path, dst_item: Path) -> None:
    """
    Replace dst_item with src_item content.
    If dst_item exists, remove it first (file/symlink/dir), then copy.
    """
    if dst_item.exists() or dst_item.is_symlink():
        if dst_item.is_dir() and not dst_item.is_symlink():
            shutil.rmtree(dst_item)
        else:
            dst_item.unlink(missing_ok=True)

    if src_item.is_dir() and not src_item.is_symlink():
        shutil.copytree(src_item, dst_item)
    else:
        # file or symlink -> copy2 for files; for symlink treat as file-like copy if possible
        # If you want exact symlink preservation, we can add special handling.
        shutil.copy2(src_item, dst_item)


def _sync_replace_collisions(src: Path, dst: Path) -> None:
    """
    Default behavior:
    - copy src/* into dst/
    - if a name collides, replace the destination entry
    - do NOT delete destination-only entries
    """
    dst.mkdir(parents=True, exist_ok=True)

    for src_item in src.iterdir():
        dst_item = dst / src_item.name

        if dst_item.exists() or dst_item.is_symlink():
            _replace_one(src_item, dst_item)
        else:
            if src_item.is_dir() and not src_item.is_symlink():
                shutil.copytree(src_item, dst_item)
            else:
                shutil.copy2(src_item, dst_item)


def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "Sync ./config/* into ./echo_desc/config_defaults.\n"
            "Default: replace collisions only (do not delete destination-only files).\n"
            "Use --clear to wipe destination first."
        )
    )
    p.add_argument(
        "--src",
        type=Path,
        default=Path("config"),
        help="Source directory (default: ./config)",
    )
    p.add_argument(
        "--dst",
        type=Path,
        default=Path("echo_desc/config_defaults"),
        help="Destination directory (default: ./echo_desc/config_defaults)",
    )
    p.add_argument(
        "--clear",
        action="store_true",
        help="Delete all contents of destination before copying (wipe dst/*).",
    )
    args = p.parse_args()

    src = args.src.resolve()
    dst = args.dst.resolve()

    if not src.exists() or not src.is_dir():
        raise SystemExit(f"Source directory does not exist or is not a directory: {src}")

    dst.mkdir(parents=True, exist_ok=True)

    if args.clear:
        _safe_clear_dir(dst)

    _sync_replace_collisions(src, dst)

    print(f"OK: synced {src} -> {dst} (clear={args.clear})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
