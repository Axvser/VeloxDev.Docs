#!/usr/bin/env python3
"""
CloudGlyph Template Sync Script
Syncs the local repository with the latest remote template, preserving user documents.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ---- Configuration ----
# Paths that are USER-owned in a child wiki repo and must never be overwritten by a sync:
# the wiki content itself, and the local config (site title in site.json, the language map in
# languages.json). Everything else (app code, skills, validators) is replaced from the template.
PRESERVE_RELATIVES = (
    "src/CloudGlyph/Assets/Docs/content",
    "src/CloudGlyph/Assets/Docs/config",
)
PRESERVE_PARTS = [tuple(Path(p).parts) for p in PRESERVE_RELATIVES]
IGNORE_DIRS = {".git", "bin", "obj", ".vs"}
IGNORE_FILES = {".gitattributes"}


def is_preserved(rel_parts: tuple[str, ...]) -> bool:
    """True when a relative path is at or beneath one of the user-owned PRESERVE_RELATIVES."""
    return any(rel_parts[: len(pp)] == pp for pp in PRESERVE_PARTS)
REPO_URL = "https://github.com/Axvser/CloudGlyph.git"
BRANCH = "master"


def log(msg: str) -> None:
    print(f"[sync] {msg}", flush=True)


def run_git(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", *cmd], cwd=cwd, capture_output=True, text=True, check=check)
    except FileNotFoundError:
        log("ERROR: 'git' command not found. Please install Git.")
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else "(no stderr)"
        log(f"ERROR: git {' '.join(cmd)} failed (exit {exc.returncode}):")
        for line in stderr.splitlines():
            log(f"  git: {line}")
        sys.exit(1)


def clone_to_temp(repo_root: Path) -> Path:
    """Clone the repository to a temporary directory and return its path."""
    tmp = Path(tempfile.mkdtemp(prefix="cloudglyph_sync_"))
    log(f"Cloning into temporary directory: {tmp}")
    run_git(["clone", "--branch", BRANCH, REPO_URL, str(tmp)])
    return tmp


def sync_files(source: Path, target: Path) -> None:
    """Copy all files from source to target, preserving user-owned paths and ignoring build artifacts."""

    for pr in PRESERVE_RELATIVES:
        log(f"Preserving user-owned: {pr}")

    for src_path in source.rglob("*"):
        # Normalize to relative path
        rel = src_path.relative_to(source)
        parts = rel.parts

        # Skip ignored root-level files
        if rel.name in IGNORE_FILES:
            continue

        # Skip if any component in the relative path is an ignored directory
        if any(part in IGNORE_DIRS for part in parts):
            continue

        # Skip the user-owned preserve paths and everything under them
        if is_preserved(parts):
            continue

        dst_path = target / rel

        if src_path.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
        else:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src_path, dst_path)
                log(f"  Copied: {rel}")
            except Exception as e:
                log(f"  WARNING: Could not copy {rel}: {e}")

    # Remove files in target that exist in the preserve dir but not in the source
    # (This handles the case where a file was added to the template under preserve area)
    # We also need to clean up files in target that don't exist in source (outside preserve)
    log("Cleaning up stale files...")
    for dst_path in target.rglob("*"):
        if dst_path == target:
            continue
        rel = dst_path.relative_to(target)
        parts = rel.parts

        # Skip ignored dirs
        if any(part in IGNORE_DIRS for part in parts):
            continue

        # Skip user-owned preserve paths and their contents
        if is_preserved(parts):
            continue

        src_path = source / rel
        if not src_path.exists():
            if dst_path.is_dir():
                try:
                    shutil.rmtree(dst_path)
                    log(f"  Removed dir: {rel}")
                except Exception as e:
                    log(f"  WARNING: Could not remove {rel}: {e}")
            else:
                try:
                    dst_path.unlink()
                    log(f"  Removed file: {rel}")
                except Exception as e:
                    log(f"  WARNING: Could not remove {rel}: {e}")

    log("Sync complete.")


def main() -> None:
    repo_root = Path(__file__).resolve().parent

    has_git = (repo_root / ".git").is_dir()
    if not has_git:
        log("Warning: No .git directory found. Template files will be synced, but version history (.git) will not be copied.")

    if not shutil.which("git"):
        log("ERROR: Git is not installed or not in PATH.")
        sys.exit(1)

    log(f"Repository root: {repo_root}")

    # Clone template to temp directory and sync
    tmp = clone_to_temp(repo_root)

    try:
        # Sync files from template to local repository
        sync_files(tmp, repo_root)
    finally:
        # Cleanup temp directory
        log(f"Cleaning up temporary directory: {tmp}")
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
