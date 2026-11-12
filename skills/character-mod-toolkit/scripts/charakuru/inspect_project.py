#!/usr/bin/env python3
"""Check a local Charakuru project with the official unpacker and summarize its stages."""

import argparse
import json
import os
from collections import Counter
from pathlib import Path
import subprocess
import sys
import tempfile


def summarize(project):
    library = project.get("imageLibrary") or {}
    production = project.get("production") or {}
    workflow = project.get("workflow") or {}
    spring = project.get("springVerification") or {}
    review = project.get("reviewVRM") or {}
    blend = project.get("sourceBlend") or {}
    runtime = spring.get("runtime") or {}
    has_matching_review = bool(
        blend.get("sha256")
        and review.get("sha256")
        and spring.get("blendHash") == blend["sha256"]
        and spring.get("vrmHash") == review["sha256"]
        and runtime
        and any(
            item.get("path") == review.get("path") and item.get("sha256") == review["sha256"]
            for item in project.get("documents", [])
        )
    )
    return {
        "archiveValidated": True,
        "mode": project.get("mode"),
        "productionPhase": production.get("phase"),
        "riggingPhase": workflow.get("phase"),
        "imageVersionCount": len(library.get("versions", [])),
        "adoptedImageSlots": sorted(
            slot for slot, entry in library.get("slots", {}).items() if entry.get("adopted")
        ),
        "candidateCounts": {
            part: len(candidates) for part, candidates in production.get("candidates", {}).items()
        },
        "selectedParts": sorted(part for part, value in production.get("selected", {}).items() if value),
        "assetRoleCounts": dict(Counter(item["role"] for item in project["assets"])),
        "rigGuideJointCount": len((project.get("rigGuide") or {}).get("bones", [])),
        "editableBlendRegistered": bool(blend.get("sha256")),
        "reviewVrmRegistered": bool(review.get("sha256")),
        "matchingRecordedSpringReview": has_matching_review,
        "recordedSpringChecks": {
            key: runtime[key] for key in ("chains", "joints", "colliders", "frames") if key in runtime
        },
    }


def inspect(kit_root, archive):
    unpacker = kit_root / "skills" / "charakit-project" / "scripts" / "unpack.py"
    if not unpacker.is_file():
        raise ValueError("Pass --kit-root pointing to an unpacked official Charakuru kit.")
    if not archive.is_file() or archive.suffix.lower() != ".charakit":
        raise ValueError("Pass an existing .charakit archive.")
    with tempfile.TemporaryDirectory(prefix="charakuru-inspect-") as temp:
        destination = Path(temp) / "unpacked"
        result = subprocess.run(
            [sys.executable, str(unpacker), str(archive), str(destination)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONUTF8": "1"},
            check=False,
        )
        if result.returncode:
            raise ValueError(f"Official Charakuru unpacker rejected the archive:\n{result.stderr.strip()}")
        project = json.loads((destination / "project.json").read_text(encoding="utf-8"))
        return summarize(project)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit-root", required=True, type=Path, help="Unpacked official Charakuru directory")
    parser.add_argument("--require-review", action="store_true", help="Require matching stored VRM spring results")
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    try:
        report = inspect(args.kit_root.resolve(), args.archive.resolve())
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.require_review and not report["matchingRecordedSpringReview"]:
        parser.exit(1, "error: no matching stored VRM spring validation in this project\n")


if __name__ == "__main__":
    main()
