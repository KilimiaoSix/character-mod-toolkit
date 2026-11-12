"""Fit a supported Charakuru rig to the checked Rochelle world armature."""
from collections import defaultdict
from math import isfinite
from mathutils import Matrix, Vector
from pathlib import Path
import json
import sys
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rochelle_profile import MODEL_DIR, REFERENCE, arguments, load_profile

args = arguments(__doc__, blender=True, profile=True)
workspace = args.workspace.resolve()
profile = load_profile(args.profile)
reference = workspace / REFERENCE / "vanilla_rochelle.blend"
destination = workspace / MODEL_DIR
meters_per_unit = profile["meters_per_unit"]
stock_object = "ValveBiped.producer_wrk_exportData"
prefix = "ValveBiped.Bip01_"
scale_in_qc = .888
width_scale = 39.37007874 / scale_in_qc
scene = bpy.context.scene
old_rig, = [obj for obj in scene.objects if obj.type == 'ARMATURE']
source_meshes = [obj for obj in scene.objects if obj.type == 'MESH']
with bpy.data.libraries.load(str(reference.resolve()), link=False) as (available, imported):
    if stock_object not in available.objects:
        raise ValueError("The chosen file has no verified Rochelle world armature")
    imported.objects = [stock_object]
stock, = imported.objects
scene.collection.objects.link(stock)
stock.animation_data_clear()
stock.data.pose_position = 'REST'
stock.show_in_front = True
bpy.context.view_layer.update()
source_bones = old_rig.data.bones
target_bones = stock.data.bones
if len(target_bones) != 76 or any(abs(x-1)>1e-6 for x in stock.matrix_world.to_scale()):
    raise ValueError("Unexpected world armature or reference scale")

def source_point(name):
    return (old_rig.matrix_world @ source_bones[name].head_local) * meters_per_unit

def target_point(name):
    return stock.matrix_world @ target_bones[name].head_local

equivalent = {
    "root": "Pelvis", "hips": "Pelvis", "spine": "Spine",
    "chest": "Spine2", "upperChest": "Spine4", "neck": "Neck1",
    "head": "Head1", "eye.L": "Head1", "eye.R": "Head1",
}
for side in ('L', 'R'):
    for label, target in {
        'shoulder':'Clavicle', 'upper_arm':'UpperArm', 'lower_arm':'Forearm',
        'hand':'Hand', 'upper_leg':'Thigh', 'lower_leg':'Calf',
        'foot':'Foot', 'toes':'Toe0',
    }.items():
        equivalent[label+'.'+side] = side+'_'+target
    for index, finger in enumerate(('thumb','index','middle','ring','little')):
        for joint, suffix in zip(('proximal','intermediate','distal'), ('','1','2')):
            equivalent[f'{finger}_{joint}.{side}'] = f'{side}_Finger{index}{suffix}'
equivalent = {a:prefix+b for a,b in equivalent.items()}
missing = set(equivalent.values()) - set(target_bones.keys())
if missing:
    raise ValueError(f'Reference is missing required bones: {sorted(missing)}')

def base_name(name):
    if name.startswith("Ponytail_"):
        return "head"
    if name.startswith("Skirt_"):
        return "hips"
    if name in {"eye.L","eye.R"}:
        return "head"
    if name not in equivalent:
        raise ValueError(f"No Rochelle mapping for source bone {name!r}")
    return name

def pair(name):
    return source_point(name), target_point(equivalent[name])

def palm_basis(get_point, side):
    wrist = get_point('hand.'+side)
    axis = (get_point('middle_proximal.'+side) - wrist).normalized()
    across = get_point('index_proximal.'+side) - get_point('little_proximal.'+side)
    across = (across - axis * across.dot(axis)).normalized()
    return Matrix((axis, across, axis.cross(across))).transposed()

def directional(name, following, base_rotation=Matrix.Identity(3), bend=True):
    source, target = pair(name)
    src_child, dst_child = pair(following)
    direction = src_child - source
    desired = dst_child - target
    axis = direction.normalized()
    if direction.length < 1e-6 or desired.length < 1e-6:
        raise ValueError(f"Invalid landmarks for {name}")
    adjust = (base_rotation @ axis).rotation_difference(desired.normalized()).to_matrix() if bend else Matrix.Identity(3)
    ratio = desired.length / direction.length
    stretch = Matrix.Identity(3) * width_scale
    for row in range(3):
        for col in range(3):
            stretch[row][col] += (ratio-width_scale)*axis[row]*axis[col]
    linear = adjust @ base_rotation @ stretch
    return linear, target - linear @ source

def rigid(name, rotation=Matrix.Identity(3)):
    source, target = pair(name)
    linear = rotation * width_scale
    return linear, target-linear @ source

def apply(binding, point):
    return binding[0] @ point + binding[1]

placements = {
    'hips':directional('hips','spine'),
    'spine':directional('spine','chest'),
    'chest':directional('chest','upperChest'),
    'upperChest':directional('upperChest','neck'),
    'neck':directional('neck','head'),
    'head':rigid('head'),
}
placements['root'] = placements['hips']
for side in ('L','R'):
    name = lambda base:base+'.'+side
    source_palm = palm_basis(source_point, side)
    target_palm = palm_basis(lambda n:target_point(equivalent[n]),side)
    palm_rotation = target_palm @ source_palm.transposed()
    placements[name('shoulder')] = directional(name('shoulder'),name('upper_arm'))
    upper_axis = (source_point(name('lower_arm'))-source_point(name('upper_arm'))).normalized()
    target_axis = (target_point(equivalent[name('lower_arm')])-target_point(equivalent[name('upper_arm')])).normalized()
    upper_rotation = upper_axis.rotation_difference(target_axis).to_matrix()
    placements[name('upper_arm')] = directional(name('upper_arm'),name('lower_arm'),upper_rotation)
    placements[name('lower_arm')] = directional(name('lower_arm'),name('hand'),palm_rotation)
    placements[name('hand')] = directional(name('hand'),name('middle_proximal'),palm_rotation)
    for finger in ('thumb','index','middle','ring','little'):
        proximal, intermediate, distal = (name(finger+'_'+k) for k in ('proximal','intermediate','distal'))
        placements[proximal] = directional(proximal,intermediate,palm_rotation)
        placements[intermediate] = directional(intermediate,distal,palm_rotation)
        matrix = placements[intermediate][0]
        source, target = pair(distal)
        placements[distal] = matrix,target - matrix @ source
    placements[name('upper_leg')] = directional(name('upper_leg'),name('lower_leg'))
    placements[name('lower_leg')] = directional(name('lower_leg'),name('foot'))
    placements[name('foot')] = directional(name('foot'),name('toes'))
    toe_source, toe_target = pair(name('toes'))
    # One continuous shoe across ankle and toe, with Valve's toe weights retained.
    foot_matrix = placements[name('foot')][0]
    placements[name('toes')] = foot_matrix,toe_target - foot_matrix @ toe_source

stems = profile["meshes"]
if set(stems) != {obj.name for obj in source_meshes}:
    raise ValueError("Prepared scene and profile have different mesh names")
missing_sources = sorted(set(equivalent) - set(source_bones.keys()) - {"root", "eye.L", "eye.R"})
if missing_sources:
    raise ValueError(f"Unsupported source rig; missing source bones: {missing_sources}")
report = {}
for obj in source_meshes:
    assert obj.name in stems
    old_groups = [group.name for group in obj.vertex_groups]
    world = obj.matrix_world.copy()
    deformed = []
    all_weights = []
    for vertex in obj.data.vertices:
        p = (world @ vertex.co) * meters_per_unit
        q = Vector()
        weights = defaultdict(float)
        for member in vertex.groups:
            label = base_name(old_groups[member.group])
            q += member.weight * apply(placements[label],p)
            weights[equivalent[label]] += member.weight
        selected = sorted(weights.items(), key=lambda item: -item[1])[:3]
        total = sum(weight for _, weight in selected)
        if total <= 0 or not all(isfinite(x) for x in q):
            raise ValueError(f"{obj.name} has invalid geometry or weights")
        deformed.append(q)
        all_weights.append([(name, weight / total) for name, weight in selected])

    if obj.name == profile["body_object"] and profile["align_shoe_soles"]:
        # Keep both shoe soles on the reference floor without moving their ankle joints.
        for sign in (1,-1):
            foot_points = [p for p in deformed if sign*p.x > 0 and p.z < 3]
            if not foot_points:
                raise ValueError("Sole alignment requires foot points below 3 Source units")
            lowest = min(p.z for p in foot_points)
            correction = .018 - lowest
            for point in foot_points:
                fade = (3-point.z)/(3-lowest)
                point.z += correction*fade*fade

    obj.parent = None
    obj.matrix_world = Matrix.Identity(4)
    for vertex, point in zip(obj.data.vertices, deformed):
        vertex.co = point
    obj.data.update()
    # Source has its own bind pose and uses linear skinning.
    obj.vertex_groups.clear()
    groups = {name:obj.vertex_groups.new(name=name) for name in sorted({name for row in all_weights for name,_ in row})}
    for index,row in enumerate(all_weights):
        for name, weight in row:
            groups[name].add([index], weight, 'REPLACE')
    mod, = [mod for mod in obj.modifiers if mod.type == 'ARMATURE']
    mod.object = stock
    mod.use_deform_preserve_volume = False
    obj.parent = stock
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = Matrix.Identity(4)
    report[obj.name] = {"vertices":len(deformed),"triangles":len(obj.data.loop_triangles),
                        "weights":sorted(groups),"bounds":[list(map(min,zip(*deformed))),list(map(max,zip(*deformed)))]}

bpy.data.objects.remove(old_rig,do_unlink=True)
bpy.context.view_layer.update()
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = .0254 * scale_in_qc
scene['l4d2_reference_scale'] = scale_in_qc
scene['l4d2_survivor'] = 'Rochelle'
scene['l4d2_model_scope'] = 'Third-person cosmetic replacement'
for name in profile["rigid_head_meshes"]:
    if set(report[name]["weights"]) != {prefix + "Head1"}:
        raise ValueError(f"{name} must stay rigidly weighted to the head")

output = destination.resolve()
output.mkdir(parents=True,exist_ok=True)
# The Blender Source Tools' DMX importer and the reference .blend agree in Z-up,
# native Source units; write those rest transforms directly to the SMD.
bones = list(stock.data.bones)
bone_index = {bone.name:i for i,bone in enumerate(bones)}
lines = ["version 1","nodes"]
for bone in bones:
    idx = bone_index[bone.name]
    parent = bone_index[bone.parent.name] if bone.parent else -1
    lines.append(f'{idx} "{bone.name}" {parent}')
lines.extend(("end","skeleton","time 0"))

def number_line(values):
    return ' '.join(f'{value:.7f}' for value in values)

for bone in bones:
    transform = bone.matrix_local
    if bone.parent:
        transform = bone.parent.matrix_local.inverted() @ transform
    lines.append(f'{bone_index[bone.name]} '+number_line((*transform.translation,*transform.to_euler("XYZ"))))
lines.append("end")
header = '\n'.join(lines)+'\n'

for obj in source_meshes:
    mesh = obj.data
    mesh.calc_loop_triangles()
    uv = mesh.uv_layers.active.uv
    world = obj.matrix_world.copy()
    groups = [bone_index[g.name] for g in obj.vertex_groups]
    with (output / (stems[obj.name]+'.smd')).open('w',encoding='ascii',newline='\n') as smd:
        smd.write(header+"triangles\n")
        for tri in mesh.loop_triangles:
            smd.write(obj.material_slots[tri.material_index].material.name+'\n')
            for loop_id in tri.loops:
                loop = mesh.loops[loop_id]
                vertex = mesh.vertices[loop.vertex_index]
                coord = world @ vertex.co
                normal = mesh.corner_normals[loop_id].vector
                ranked = sorted(((groups[g.group],g.weight) for g in vertex.groups),key=lambda g:-g[1])
                weight_data = ' '.join(f'{bone} {weight:.8f}' for bone,weight in ranked)
                smd.write(f'{ranked[0][0]} '+number_line((*coord,*normal,*uv[loop_id].vector))+
                          f' {len(ranked)} {weight_data}\n')
        smd.write("end\n")

bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = stock
bpy.ops.file.pack_all()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(output.parents[1]/'01_blender'/'rochelle_world.blend'))
(output.parents[1]/'01_blender'/'rochelle_world.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'meshes':len(report),'triangles':sum(v['triangles'] for v in report.values()),'bones':len(bones)}))
