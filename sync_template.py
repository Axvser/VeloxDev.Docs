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
PRESERVE_RELATIVE = "src/CloudGlyph/Assets/Docs/content"
IGNORE_DIRS = {".git", "bin", "obj", ".vs"}
IGNORE_FILES = {".gitattributes"}
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


def check_sync(repo_root: Path) -> bool:
    """Return True if local master matches remote origin/master."""
    # Ensure remote info is fresh
    log("Fetching remote origin...")
    run_git(["fetch", "origin"], cwd=repo_root)

    # Get local HEAD commit
    local = run_git(["rev-parse", BRANCH], cwd=repo_root).stdout.strip()
    remote = run_git(["rev-parse", f"origin/{BRANCH}"], cwd=repo_root).stdout.strip()

    if not local or not remote:
        log("ERROR: Could not resolve branches.")
        sys.exit(1)

    synced = local == remote
    if synced:
        log(f"Local {BRANCH} is up-to-date with origin/{BRANCH}.")
    else:
        log(f"Local {BRANCH} ({local[:8]}) differs from origin/{BRANCH} ({remote[:8]}).")
    return synced


def clone_to_temp(repo_root: Path) -> Path:
    """Clone the repository to a temporary directory and return its path."""
    tmp = Path(tempfile.mkdtemp(prefix="cloudglyph_sync_"))
    log(f"Cloning into temporary directory: {tmp}")
    run_git(["clone", "--branch", BRANCH, REPO_URL, str(tmp)])
    return tmp


def sync_files(source: Path, target: Path) -> None:
    """Copy all files from source to target, preserving PRESERVE_RELATIVE and ignoring build artifacts."""

    preserve_path = (source / PRESERVE_RELATIVE).resolve()
    target_preserve_path = (target / PRESERVE_RELATIVE).resolve()

    log(f"Preserving directory: {PRESERVE_RELATIVE}")

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

        # Skip the preserve directory and everything under it
        try:
            resolved_src = src_path.resolve()
            if resolved_src == preserve_path or preserve_path in resolved_src.parents:
                continue
        except (ValueError, OSError):
            pass

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

        # Skip preserve dir and its contents
        try:
            resolved_dst = dst_path.resolve()
            if resolved_dst == target_preserve_path or target_preserve_path in resolved_dst.parents:
                continue
        except (ValueError, OSError):
            pass

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

    if not (repo_root / ".git").is_dir():
        log("ERROR: This script must be run from within a Git repository.")
        sys.exit(1)

    if not shutil.which("git"):
        log("ERROR: Git is not installed or not in PATH.")
        sys.exit(1)

    log(f"Repository root: {repo_root}")

    # Step 1: Check sync status
    if check_sync(repo_root):
        log("No update needed.")
        return

    # Step 2: Clone to temp
    tmp = clone_to_temp(repo_root)

    try:
        # Step 3: Sync files
        sync_files(tmp, repo_root)
    finally:
        # Cleanup temp directory
        log(f"Cleaning up temporary directory: {tmp}")
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
