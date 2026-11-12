"""Generate a Rochelle world QC referencing the external stock-rig template."""
import json
from pathlib import Path
from rochelle_profile import MATERIAL_DIR, MODEL_DIR, REFERENCE, arguments, load_profile

args = arguments(__doc__, profile=True)
workspace = args.workspace.resolve()
profile = load_profile(args.profile)
mesh_paths = {obj: workspace / MODEL_DIR / f"{stem}.smd" for obj, stem in profile["meshes"].items()}
external_paths = [
    "mdl/physics.dmx", "qc/procedurals.vrd", "qc/hbox.qci",
    "qc/attachments.qci", "qc/bone_rochelle.qci",
]
upstream_qc = workspace / REFERENCE / "rochelle.qc"
for file in (upstream_qc, *mesh_paths.values(), *(workspace / REFERENCE / p for p in external_paths)):
    if not file.is_file():
        raise FileNotFoundError(file)

template_settings = {"$scale": 1, "$surfaceprop": 1, "$contents": 1, "$ambientboost": 1,
                     "$mostlyopaque": 1, "$eyeposition": 1, "$ikchain": 4, "$ikautoplaylock": 2}
settings = {directive: [] for directive in template_settings}
for line in upstream_qc.read_text(encoding="utf-8-sig").splitlines():
    tokens = line.split(maxsplit=1)
    if tokens and tokens[0] in settings:
        settings[tokens[0]].append(line.strip())
for directive, count in template_settings.items():
    if len(settings[directive]) != count:
        raise ValueError(f"Expected {count} {directive} directive(s) in the pinned Rochelle QC")

lines = [
    '// Third-person cosmetic replacement for Rochelle.',
    '$modelname "survivors/survivor_producer.mdl"',
    *settings.pop("$scale"),
]
main_mesh = profile["body_object"]
for obj in [main_mesh, *(obj for obj in mesh_paths if obj != main_mesh)]:
    stem = mesh_paths[obj].stem
    declaration = '$model "Producer"' if obj == main_mesh else f'$body "{stem}"'
    lines.append(f'{declaration} "mesh/{stem}.smd"')
reference = '../' + REFERENCE.as_posix()
material_root = MATERIAL_DIR.relative_to("addon/materials").as_posix()
lines.extend([
    f'$cdmaterials "{material_root}/"',
    *(line for group in settings.values() for line in group),
    f'$sequence "Producer" "{reference}/mdl/physics.dmx"',
    f'$sequence "ragdoll" "{reference}/mdl/physics.dmx" ACT_DIERAGDOLL 1 fps 30.00',
    '$includemodel "survivors/anim_producer.mdl"',
    '$includemodel "survivors/anim_gestures.mdl"',
    f'$proceduralbones "{reference}/qc/procedurals.vrd"',
    *(f'$include "{reference}/{p}"' for p in external_paths[2:]),
])
qc = workspace / "04_compile/rochelle_world.qc"
qc.write_text('\n'.join(lines) + '\n', encoding="ascii")
print(json.dumps({"qc": str(qc), "mesh_count": len(mesh_paths)}, indent=2))
