"""Extract opaque MToon base colors from the prepared Blender scene."""
import hashlib
import json
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rochelle_profile import arguments, load_profile

args = arguments(__doc__, blender=True, profile=True)
profile = load_profile(args.profile)
output = args.workspace.resolve() / "02_material_input"
output.mkdir(parents=True, exist_ok=True)
manifest = {}
for stem in profile["materials"].values():
    material = bpy.data.materials.get(stem)
    if material is None:
        raise ValueError(f"Open prepared.blend; material {stem!r} is missing")
    extension = getattr(getattr(material, "vrm_addon_extension", None), "mtoon1", None)
    if extension is None:
        raise ValueError("Enable VRM Add-on in Blender before extracting MToon")
    if not extension.enabled:
        raise ValueError(f"{stem}: enable MToon or bake the material to an opaque MToon base color")
    if extension.alpha_mode != "OPAQUE":
        raise ValueError(f"{stem}: this pipeline supports opaque materials only")
    pbr = extension.pbr_metallic_roughness
    entry = {
        "linear_color": list(pbr.base_color_factor[:3]),
        "two_sided": stem in profile["two_sided_materials"],
    }
    image = pbr.base_color_texture.index.source
    if image is not None:
        if image.packed_file is not None:
            data = bytes(image.packed_file.data)
        else:
            image_file = Path(bpy.path.abspath(image.filepath))
            if image.source != 'FILE' or not image_file.is_file():
                raise ValueError(f"{stem}: bake or pack the base-color image first")
            data = image_file.read_bytes()
        path = output / f"{stem}.image"
        path.write_bytes(data)
        entry.update(image=path.name, sha256=hashlib.sha256(data).hexdigest())
    manifest[stem] = entry
(output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"Extracted {len(manifest)} opaque base colors to {output}")
