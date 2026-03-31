#!/usr/bin/env python3
"""
Install the matty-tiger-skills plugin directly into the Claude Code
local plugin cache, bypassing the RemotePluginManager wipe cycle.

Usage:
    python3 scripts/install.py

This writes the plugin to ~/.claude/plugins/cache/ and registers it in
installed_plugins.json and .install-manifests/, so it persists across
Claude Code restarts.

Restart Claude Code after running.
"""

import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration — edit these if you fork for a different plugin
# ---------------------------------------------------------------------------
MARKETPLACE_ID = "skills-poc"
MARKETPLACE_REPO = "mattstratton/skills-poc"
PLUGIN_DIR_IN_REPO = "plugins/matty-tiger-skills"  # relative to repo root
# ---------------------------------------------------------------------------

CLAUDE_DIR = Path.home() / ".claude" / "plugins"
CACHE_DIR = CLAUDE_DIR / "cache"
MANIFESTS_DIR = CLAUDE_DIR / ".install-manifests"
INSTALLED_JSON = CLAUDE_DIR / "installed_plugins.json"
KNOWN_MARKETPLACES_JSON = CLAUDE_DIR / "known_marketplaces.json"


def find_repo_root() -> Path:
    """Walk up from this script to find the git repo root."""
    here = Path(__file__).resolve().parent
    for ancestor in [here, *here.parents]:
        if (ancestor / ".git").exists():
            return ancestor
    print("Error: could not find git repo root.", file=sys.stderr)
    sys.exit(1)


def read_plugin_json(plugin_src: Path) -> dict:
    """Read .claude-plugin/plugin.json to get name + version."""
    pj = plugin_src / ".claude-plugin" / "plugin.json"
    if not pj.exists():
        print(f"Error: {pj} not found.", file=sys.stderr)
        sys.exit(1)
    return json.loads(pj.read_text())


def get_git_sha(repo_root: Path) -> str:
    """Get the current HEAD commit SHA."""
    import subprocess
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root, capture_output=True, text=True
    )
    return result.stdout.strip()


def collect_plugin_files(plugin_src: Path) -> list[Path]:
    """Collect all files in the plugin directory (excluding .DS_Store etc)."""
    skip = {".DS_Store", "__pycache__", ".git"}
    files = []
    for path in plugin_src.rglob("*"):
        if path.is_file() and not any(s in path.parts for s in skip):
            files.append(path)
    return sorted(files)


def sha256_of(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def copy_plugin_to_cache(plugin_src: Path, dest: Path, files: list[Path]) -> dict[str, str]:
    """Copy plugin files to cache dir. Returns {relative_path: sha256}."""
    if dest.exists():
        shutil.rmtree(dest)
    file_hashes = {}
    for src_file in files:
        rel = src_file.relative_to(plugin_src)
        dst_file = dest / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        content = src_file.read_bytes()
        dst_file.write_bytes(content)
        file_hashes[str(rel)] = sha256_of(content)
    return file_hashes


def update_installed_plugins(plugin_key: str, cache_path: Path, version: str, git_sha: str):
    """Register (or update) the plugin in installed_plugins.json."""
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if INSTALLED_JSON.exists():
        data = json.loads(INSTALLED_JSON.read_text())
    else:
        data = {"version": 2, "plugins": {}}

    data["plugins"][plugin_key] = [{
        "scope": "user",
        "installPath": str(cache_path),
        "version": version,
        "installedAt": now,
        "lastUpdated": now,
        "gitCommitSha": git_sha,
    }]
    INSTALLED_JSON.write_text(json.dumps(data, indent=2) + "\n")


def write_install_manifest(plugin_key: str, file_hashes: dict[str, str]):
    """Write the .install-manifests/<key>.json file."""
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    manifest = {
        "pluginId": plugin_key,
        "createdAt": now,
        "files": file_hashes,
    }
    manifest_path = MANIFESTS_DIR / f"{plugin_key}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


def ensure_known_marketplace():
    """Make sure our marketplace is registered in known_marketplaces.json."""
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if KNOWN_MARKETPLACES_JSON.exists():
        data = json.loads(KNOWN_MARKETPLACES_JSON.read_text())
    else:
        data = {}

    if MARKETPLACE_ID not in data:
        data[MARKETPLACE_ID] = {
            "source": {
                "source": "github",
                "repo": MARKETPLACE_REPO,
            },
            "lastUpdated": now,
        }
        KNOWN_MARKETPLACES_JSON.write_text(json.dumps(data, indent=2) + "\n")


def main():
    repo_root = find_repo_root()
    plugin_src = repo_root / PLUGIN_DIR_IN_REPO

    if not plugin_src.exists():
        print(f"Error: plugin source not found at {plugin_src}", file=sys.stderr)
        sys.exit(1)

    # Read plugin metadata
    plugin_meta = read_plugin_json(plugin_src)
    plugin_name = plugin_meta["name"]
    version = plugin_meta["version"]
    plugin_key = f"{plugin_name}@{MARKETPLACE_ID}"
    git_sha = get_git_sha(repo_root)

    print(f"Installing {plugin_key} v{version} ...")

    # Ensure directories exist
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)

    # Collect and copy files
    files = collect_plugin_files(plugin_src)
    cache_path = CACHE_DIR / MARKETPLACE_ID / plugin_name / version
    file_hashes = copy_plugin_to_cache(plugin_src, cache_path, files)
    print(f"  Copied {len(files)} files to {cache_path}")

    # Register in installed_plugins.json
    update_installed_plugins(plugin_key, cache_path, version, git_sha)
    print(f"  Updated {INSTALLED_JSON}")

    # Write install manifest
    write_install_manifest(plugin_key, file_hashes)
    print(f"  Wrote manifest to {MANIFESTS_DIR / (plugin_key + '.json')}")

    # Ensure marketplace is registered
    ensure_known_marketplace()

    print()
    print(f"Done! {plugin_name} v{version} installed.")
    print("Restart Claude Code to pick up the changes.")


if __name__ == "__main__":
    main()
