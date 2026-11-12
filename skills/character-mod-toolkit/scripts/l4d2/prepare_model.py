"""Prepare the Source mesh without changing the original VRM working file."""
from collections import Counter
from mathutils.bvhtree import BVHTree
from pathlib import Path
import json
import sys
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rochelle_profile import arguments, load_profile

args = arguments(__doc__, blender=True, profile=True)
profile = load_profile(args.profile)
destination = args.workspace.resolve() / "01_blender/prepared.blend"
if bpy.data.filepath and destination == Path(bpy.data.filepath).resolve():
    raise ValueError("Open the source model, not the prepared output")
destination.parent.mkdir(parents=True, exist_ok=True)
ratios = profile["decimate"]
material_names = profile["materials"]

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
rigs = [obj for obj in scene.objects if obj.type == "ARMATURE"]
if len(rigs) != 1:
    raise ValueError("Expected exactly one character armature in the scene")
rig = rigs[0]
rig.data.pose_position = 'REST'
meshes = {obj.name: obj for obj in scene.objects if obj.type == 'MESH'}
if meshes.keys() != profile["meshes"].keys():
    raise ValueError(f"Configure the exact mesh names in the scene: {sorted(meshes)}")
for mesh in meshes.values():
    if not mesh.material_slots or any(
        not slot.material or slot.material.name not in material_names
        for slot in mesh.material_slots
    ):
        raise ValueError(f"Unmapped material on {mesh.name}")
used_materials = {
    slot.material for mesh in meshes.values() for slot in mesh.material_slots
}
if {m.name for m in used_materials} != material_names.keys():
    raise ValueError("The material map must cover precisely the used material slots")
for material in used_materials:
    existing = bpy.data.materials.get(material_names[material.name])
    if existing is not None and existing != material:
        raise ValueError(f"Material stem collides with an existing datablock: {existing.name}")

report = {}

def sampled_deviation(original_points, obj):
    transformed = [obj.matrix_world @ v.co for v in obj.data.vertices]
    reduced_faces = [poly.vertices[:] for poly in obj.data.polygons]
    reduced = BVHTree.FromPolygons(transformed, reduced_faces)
    distances = sorted(reduced.find_nearest(p)[3] for p in original_points)
    return {
        "p95_mm": round(1000 * profile["meters_per_unit"] * distances[int((len(distances) - 1) * .95)], 3),
        "max_mm": round(1000 * profile["meters_per_unit"] * distances[-1], 3),
    }

for name, obj in meshes.items():
    modifiers = [m for m in obj.modifiers if m.type == "ARMATURE"]
    if len(modifiers) != 1 or modifiers[0].object != rig:
        raise ValueError(f"{obj.name}: expected one modifier pointing at the character rig")
    modifier = modifiers[0]
    preserve_volume = modifier.use_deform_preserve_volume
    original_triangles = len(obj.data.loop_triangles)
    before_points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    obj.modifiers.remove(modifier)
    ratio = ratios.get(name, 1)
    if ratio < 1:
        bpy.context.view_layer.objects.active = obj
        mod = obj.modifiers.new("Source mesh reduction", "DECIMATE")
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if not obj.data.uv_layers:
        if any(slot.material.name not in profile["constant_uv_materials"] for slot in obj.material_slots):
            raise ValueError(f"{name}: textured mesh has no UV map")
        uv = obj.data.uv_layers.new(name='UVMap')
        for corner in uv.uv:
            corner.vector = (.5, .5)
    weights = Counter()
    for vertex in obj.data.vertices:
        ordered = sorted(((g.weight, g.group) for g in vertex.groups if g.weight > 1e-7), reverse=True)
        if not ordered:
            raise ValueError(f"Unweighted vertex {name}:{vertex.index}")
        group_ids = [entry.group for entry in vertex.groups]
        selected = ordered[:3]
        for group_id in group_ids:
            obj.vertex_groups[group_id].remove([vertex.index])
        total = sum(weight for weight, _ in selected)
        for weight, group_id in selected:
            obj.vertex_groups[group_id].add([vertex.index], weight / total, 'REPLACE')
        weights[len(selected)] += 1
    restored = obj.modifiers.new("Armature", "ARMATURE")
    restored.object = rig
    restored.use_deform_preserve_volume = preserve_volume
    report[name] = {
        "vertices": len(obj.data.vertices),
        "original_triangles": original_triangles,
        "triangles": len(obj.data.loop_triangles),
        "influences": dict(sorted(weights.items())),
        "surface_deviation": sampled_deviation(before_points, obj),
    }

for material in used_materials:
    material.name = material_names[material.name]
bpy.context.view_layer.update()
for obj in meshes.values():
    assert obj.data.uv_layers.active
    for v in obj.data.vertices:
        assert 1 <= len(v.groups) <= 3 and abs(sum(g.weight for g in v.groups)-1) < 1e-6
bpy.ops.file.pack_all()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(destination))
destination.with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
