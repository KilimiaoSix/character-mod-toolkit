#!/usr/bin/env python3
"""Report local tools and dependencies without installing or modifying anything."""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


def executable(name, hints):
    candidate = shutil.which(name)
    if candidate:
        return candidate
    return next((str(path) for path in hints if path.is_file()), None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--game-root", type=Path)
    args = parser.parse_args()
    deps = args.workspace.resolve() / "deps"
    node = shutil.which("node")
    node_version = None
    if node:
        try:
            node_version = subprocess.check_output([node, "--version"], text=True, timeout=5).strip()
        except (OSError, subprocess.SubprocessError):
            pass
    hints = [Path("/Applications/Blender.app/Contents/MacOS/Blender")]
    if os.name == "nt":
        apps = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Blender Foundation"
        hints.extend(sorted(apps.glob("Blender */blender.exe"), reverse=True))
    report = {
        "python": shutil.which("python3") or shutil.which("python"),
        "node": {"path": node, "version": node_version},
        "git": shutil.which("git"),
        "githubCli": shutil.which("gh"),
        "curl": shutil.which("curl.exe" if os.name == "nt" else "curl"),
        "blender": executable("blender", hints),
        "dependencies": {
            "charakuru": (deps / "charakuru/server.mjs").is_file(),
            "vrmAddonArchive": (deps / "VRM_Addon_for_Blender-Extension-4_10_4.zip").is_file(),
            "rochelleReference": (deps / "community-hedyl2/survivor_producer/vanilla_rochelle.blend").is_file(),
        },
    }
    if args.game_root:
        game = args.game_root.resolve()
        report["l4d2"] = {
            "root": str(game),
            "gameinfo": (game / "left4dead2/gameinfo.txt").is_file(),
            "studiomdl": (game / "bin/studiomdl.exe").is_file(),
            "vpk": (game / "bin/vpk.exe").is_file(),
        }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
