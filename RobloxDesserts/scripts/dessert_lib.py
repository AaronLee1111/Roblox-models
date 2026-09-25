"""Shared helpers for building, exporting, validating and previewing the
Roblox dessert café props.

Units: 1 Blender unit = 1 Roblox stud. Every asset is built Z-up with its
pivot at the bottom centre, then exported Y-up (.glb) / Y-up (.fbx).
"""
import math
import os

import bpy  # must come before bmesh when using the bpy pip module
import bmesh
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset_dir(name):
    path = os.path.join(ROOT, name)
    os.makedirs(os.path.join(path, "textures"), exist_ok=True)
    return path


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


# ---------------------------------------------------------------- textures

def srgb(c):
    """Hex '#rrggbb' -> linear-ish float tuple as Blender image pixels expect (sRGB stored)."""
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def image_from_array(name, rgb, out_dir):
    """rgb: HxWx3 float array in sRGB (row 0 = bottom of image, Blender convention)."""
    h, w, _ = rgb.shape
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.ones((h, w, 1))], axis=2).astype(np.float32)
    img = bpy.data.images.new(name, w, h, alpha=False)
    img.pixels.foreach_set(rgba.ravel())
    path = os.path.join(out_dir, "textures", f"{name}.png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    img.filepath = path
    img.pack()
    return img


def solid_image(name, hex_color, out_dir, size=4):
    rgb = np.ones((size, size, 3)) * np.array(srgb(hex_color))
    return image_from_array(name, rgb, out_dir)


def make_material(name, image, roughness=0.8, specular=0.5, clearcoat=0.0):
    """Principled material driven by a colour texture. Every material gets a
    texture (even flat ones) so Roblox's importer always has a ColorMap."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Specular IOR Level"].default_value = specular
    if clearcoat:
        bsdf.inputs["Coat Weight"].default_value = clearcoat
        bsdf.inputs["Coat Roughness"].default_value = 0.15
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.location = (-400, 200)
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


# ------------------------------------------------------------------ meshes

def obj_from_bm(name, bm, mat=None):
    bm.loops.layers.uv.verify()  # every part carries a UV layer so joins keep UVs
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if mat:
        mesh.materials.append(mat)
    return obj


def uvsphere_bm(u=24, v=14, radius=1.0):
    bm = bmesh.new()
    bm.loops.layers.uv.verify()  # calc_uvs only fills an existing layer
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=radius, calc_uvs=True)
    return bm


def add_subsurf(obj, levels=1):
    mod = obj.modifiers.new("Subsurf", "SUBSURF")
    mod.levels = levels
    mod.render_levels = levels
    return mod


def apply_modifiers(obj):
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def planar_uv(obj, axis_u=0, axis_v=2, bounds=None):
    """Project UVs from object-space coordinates onto the given axes."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    co = [v.co for v in me.vertices]
    if bounds is None:
        us = [c[axis_u] for c in co]
        vs = [c[axis_v] for c in co]
        bounds = (min(us), max(us), min(vs), max(vs))
    u0, u1, v0, v1 = bounds
    for loop in me.loops:
        c = co[loop.vertex_index]
        uv[loop.index].uv = ((c[axis_u] - u0) / (u1 - u0), (c[axis_v] - v0) / (v1 - v0))
    return bounds


def finalize(objs, name, smooth_angle=40):
    """Join parts, apply transforms, pivot at bottom centre, smooth by angle."""
    for o in objs:
        bpy.context.view_layer.objects.active = o
        if o.modifiers:
            apply_modifiers(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = obj.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Pivot: bottom centre of the bounding box.
    xs, ys, zs = zip(*[v.co for v in obj.data.vertices])
    offset = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    for v in obj.data.vertices:
        v.co -= offset
    obj.location = (0, 0, 0)

    # Merge the identical material slots created by joining.
    bpy.ops.object.material_slot_remove_unused()
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth_angle))
    return obj


def stats(obj):
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    return {
        "triangles": tris,
        "vertices": len(obj.data.vertices),
        "dimensions": tuple(round(d, 3) for d in obj.dimensions),
        "materials": [m.name for m in obj.data.materials],
    }


# ------------------------------------------------------------------ export

def export(obj, out_dir, name):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    glb = os.path.join(out_dir, f"{name}.glb")
    fbx = os.path.join(out_dir, f"{name}.fbx")
    bpy.ops.export_scene.gltf(
        filepath=glb, export_format="GLB", use_selection=True, export_yup=True,
        export_apply=True, export_texcoords=True, export_normals=True,
        export_materials="EXPORT", export_image_format="AUTO",
    )
    bpy.ops.export_scene.fbx(
        filepath=fbx, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Z", axis_up="Y", object_types={"MESH"}, mesh_smooth_type="FACE",
        path_mode="COPY", embed_textures=True, bake_space_transform=True,
    )
    return glb, fbx


def validate(path):
    """Re-import an exported file into an empty scene and report what survived."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if path.endswith(".glb"):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        bpy.ops.import_scene.fbx(filepath=path)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    mats = sorted({m.name for o in meshes for m in o.data.materials if m})
    textured = []
    for m in bpy.data.materials:
        if m.use_nodes and any(n.type == "TEX_IMAGE" and n.image and n.image.size[0] > 0
                               for n in m.node_tree.nodes):
            textured.append(m.name)
    dims = None
    if meshes:
        pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
        dims = tuple(round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3))
    return {"file": os.path.basename(path), "meshes": len(meshes), "triangles": tris,
            "materials": mats, "textured_materials": sorted(textured), "dimensions": dims}


# ------------------------------------------------------------------ preview

def render_preview(obj, out_path, cam_dir=(1.0, -1.1, 0.75), lens=55, samples=64, size=768,
                   bg="#f6ecef", ground="#f3e3e8", margin=1.35):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = size
    # Standard transform shows texture colours as authored (closer to Roblox than AgX).
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"

    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bgn = world.node_tree.nodes["Background"]
    bgn.inputs["Color"].default_value = (*[c ** 2.2 for c in srgb(bg)], 1)
    bgn.inputs["Strength"].default_value = 0.8
    scene.world = world

    dims = obj.dimensions
    radius = max(dims) * 0.5
    center = Vector((0, 0, dims.z * 0.45))

    key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", "AREA"))
    key.data.energy = 120 * radius ** 2
    key.data.size = radius * 4
    key.location = center + Vector((-2.5, -2.5, 3.5)) * radius
    key.rotation_euler = (center - key.location).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(key)
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 1.6
    sun.data.angle = math.radians(25)
    sun.rotation_euler = (math.radians(35), math.radians(-20), math.radians(-30))
    scene.collection.objects.link(sun)

    gm = bpy.data.materials.new("Ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (
        *[c ** 2.2 for c in srgb(ground)], 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=radius * 30)
    ground_obj = obj_from_bm("Ground", bm, gm)

    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = lens
    d = Vector(cam_dir).normalized()
    fov = 2 * math.atan(18 / lens)
    dist = radius * margin / math.tan(fov / 2) + radius
    cam.location = center + d * dist
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(cam)
    scene.camera = cam

    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    for o in (ground_obj, cam, key, sun):
        bpy.data.objects.remove(o)


def write_report(out_dir, name, st, glb_check, fbx_check, previews):
    lines = [
        f"# {name}", "",
        f"- Triangles: {st['triangles']}",
        f"- Vertices: {st['vertices']}",
        f"- Dimensions (studs, X x Y x Z-up): {st['dimensions'][0]} x {st['dimensions'][1]} x {st['dimensions'][2]}",
        f"- Materials ({len(st['materials'])}): {', '.join(st['materials'])}",
        f"- Exports: {name}.glb, {name}.fbx",
        f"- Previews: {', '.join(os.path.basename(p) for p in previews)}",
        "", "## Re-import validation",
        f"- GLB: {glb_check}",
        f"- FBX: {fbx_check}", "",
    ]
    with open(os.path.join(out_dir, "REPORT.md"), "w") as f:
        f.write("\n".join(lines))


def build_and_ship(name, build_fn, views=((1.0, -1.1, 0.75),), smooth_angle=40, **render_kw):
    """Standard pipeline: build -> finalize -> export -> preview -> validate."""
    out_dir = asset_dir(name)
    reset()
    parts = build_fn(out_dir)
    obj = finalize(parts, name, smooth_angle)
    st = stats(obj)
    glb, fbx = export(obj, out_dir, name)
    previews = []
    for i, v in enumerate(views):
        p = os.path.join(out_dir, f"{name}_preview{'' if i == 0 else f'_{i + 1}'}.png")
        render_preview(obj, p, cam_dir=v, **render_kw)
        previews.append(p)
    glb_check = validate(glb)
    fbx_check = validate(fbx)
    write_report(out_dir, name, st, glb_check, fbx_check, previews)
    print("STATS", st)
    print("GLB", glb_check)
    print("FBX", fbx_check)
    ok = (glb_check["meshes"] >= 1 and glb_check["triangles"] == st["triangles"]
          and len(glb_check["materials"]) == len(st["materials"])
          and len(glb_check["textured_materials"]) == len(st["materials"]))
    print("VALID" if ok else "INVALID")
    return ok
