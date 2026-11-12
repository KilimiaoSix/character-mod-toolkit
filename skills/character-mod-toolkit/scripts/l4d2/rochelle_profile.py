"""Input contract for the Rochelle world-model pipeline."""
import argparse
import json
import math
from pathlib import Path
import re
import sys

STEM = re.compile(r"[a-z][a-z0-9_]{0,62}\Z")
REFERENCE = Path("deps/community-hedyl2/survivor_producer")
MODEL_DIR = Path("04_compile/mesh")
MATERIAL_DIR = Path("addon/materials/models/survivors/character_mod")


def arguments(description, *, blender=False, profile=False):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--workspace", type=Path, required=True)
    if profile:
        parser.add_argument("--profile", type=Path, required=True)
    argv = None
    if blender:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(argv)


def load_profile(path):
    profile = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(profile, dict):
        raise ValueError("Profile must be a JSON object")
    unknown = profile.keys() - {
        "meshes", "body_object", "materials", "decimate", "constant_uv_materials",
        "two_sided_materials", "rigid_head_meshes", "align_shoe_soles",
        "meters_per_unit",
    }
    if unknown:
        raise ValueError(f"Unknown profile keys: {sorted(unknown)}")
    meshes = profile.get("meshes")
    materials = profile.get("materials")
    for name, value in (("meshes", meshes), ("materials", materials)):
        if not isinstance(value, dict) or not value:
            raise ValueError(f"{name} must map Blender names to unique ASCII stems")
        if any(not isinstance(s, str) or not STEM.fullmatch(s) for s in value.values()):
            raise ValueError(f"Invalid {name} output stem")
        if len(set(value.values())) != len(value):
            raise ValueError(f"Duplicate {name} output stem")
    if profile.get("body_object") not in meshes:
        raise ValueError("body_object must be one of the configured meshes")
    ratios = profile.setdefault("decimate", {})
    if not isinstance(ratios, dict) or not ratios.keys() <= meshes.keys():
        raise ValueError("decimate keys must name configured meshes")
    if any(type(r) not in (int, float) or not 0 < r <= 1 for r in ratios.values()):
        raise ValueError("decimate values must be numbers in (0, 1]")
    for name, allowed in (
        ("constant_uv_materials", set(materials)),
        ("two_sided_materials", set(materials.values())),
        ("rigid_head_meshes", set(meshes)),
    ):
        selected = profile.setdefault(name, [])
        if (not isinstance(selected, list) or any(
            not isinstance(item, str) or item not in allowed for item in selected
        )):
            raise ValueError(f"Invalid names in {name}")
    if type(profile.setdefault("align_shoe_soles", False)) is not bool:
        raise ValueError("align_shoe_soles must be a boolean")
    units = profile.setdefault("meters_per_unit", 1)
    if type(units) not in (int, float) or not math.isfinite(units) or units <= 0:
        raise ValueError("meters_per_unit must be positive and finite")
    return profile
