"""Check the generated Rochelle QC, SMD material names, and local VTF/VMT files."""
import json
import re
import shlex

from rochelle_profile import MATERIAL_DIR, MODEL_DIR, STEM, arguments

args = arguments(__doc__)
workspace = args.workspace.resolve()
qc = workspace / "04_compile/rochelle_world.qc"
references = []
world_meshes = []
materials = set()
triangles = 0
for line in qc.read_text(encoding="ascii").splitlines():
    if not line or line.startswith("//"):
        continue
    fields = shlex.split(line)
    directive = fields[0]
    if directive in {"$model", "$body", "$sequence", "$include", "$proceduralbones"}:
        ref = fields[2 if directive in {"$model", "$body", "$sequence"} else 1]
        path = (qc.parent / ref).resolve()
        if not path.is_relative_to(workspace) or not path.is_file():
            raise ValueError(f"QC input outside the workspace or missing: {ref}")
        references.append(ref)
        if directive in {"$model", "$body"}:
            world_meshes.append(path)

if not world_meshes or len(set(world_meshes)) != len(world_meshes):
    raise ValueError("Expected distinct world meshes")
for mesh in world_meshes:
    if mesh.parent != workspace / MODEL_DIR or mesh.suffix != ".smd":
        raise ValueError(f"Unexpected SMD path: {mesh}")
    content = mesh.read_text(encoding="ascii")
    match = re.search(r"(?m)^triangles\n([\s\S]*?)^end$", content)
    if match is None:
        raise ValueError(f"No complete triangles section: {mesh.name}")
    lines = match.group(1).splitlines()
    if len(lines) % 4 or not lines:
        raise ValueError(f"Malformed triangle record: {mesh.name}")
    for offset in range(0, len(lines), 4):
        material = lines[offset]
        if not STEM.fullmatch(material):
            raise ValueError(f"Invalid SMD material stem: {material}")
        materials.add(material)
        for line in lines[offset + 1:offset + 4]:
            fields = line.split()
            count = int(fields[9])
            if not 1 <= count <= 3 or len(fields) != 10 + 2 * count:
                raise ValueError(f"Unexpected SMD weight count: {mesh.name}")
            weights = [float(fields[11 + 2 * i]) for i in range(count)]
            if any(not 0 < weight <= 1 for weight in weights) or abs(sum(weights) - 1) > 1e-5:
                raise ValueError(f"Non-normalized SMD weights: {mesh.name}")
    triangles += len(lines) // 4

for material in materials:
    path = workspace / MATERIAL_DIR / f"{material}.vmt"
    texture = path.with_suffix(".vtf")
    virtual = MATERIAL_DIR.relative_to("addon/materials").as_posix()
    if f'"$basetexture" "{virtual}/{material}"' not in path.read_text(encoding="ascii"):
        raise ValueError(f"VMT base texture path mismatch: {path}")
    with texture.open("rb") as stream:
        if stream.read(4) != b"VTF\x00":
            raise ValueError(f"Invalid VTF signature: {texture}")
print(json.dumps({
    "scope": "Static world-model input check; no native compile or in-game test",
    "qc_references": len(references),
    "world_meshes": len(world_meshes),
    "triangles": triangles,
    "materials": sorted(materials),
}, indent=2))
