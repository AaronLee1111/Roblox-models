"""Generate a low-poly, Roblox-ready strawberry daifuku and export it as .glb.

Run with Blender's Python (either `blender -b -P scripts/strawberry_daifuku.py`
or plain `python3` with the `bpy` pip package installed).

Output: models/strawberry_daifuku.glb (+ optional preview render).
"""
import math
import os
import sys

import bpy  # must come before bmesh when using the bpy pip module
import bmesh
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "models")
GLB_PATH = os.path.join(OUT_DIR, "strawberry_daifuku.glb")
PREVIEW_PATH = os.path.join(OUT_DIR, "strawberry_daifuku_preview.png")
RENDER_PREVIEW = "--no-preview" not in sys.argv

# Palette texture: each part's UVs point at the centre of one flat-colour cell.
# One small texture keeps it to a single MeshPart + single material in Roblox.
PALETTE_SIZE = 4
PALETTE = {
    "mochi": (0, (0.98, 0.93, 0.93)),
    "mochi_blush": (1, (0.98, 0.80, 0.84)),
    "berry": (2, (0.86, 0.12, 0.18)),
    "seed": (3, (0.99, 0.88, 0.45)),
    "leaf": (4, (0.30, 0.62, 0.22)),
    "stem": (5, (0.20, 0.45, 0.15)),
}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_palette_image():
    img = bpy.data.images.new("DaifukuPalette", PALETTE_SIZE, PALETTE_SIZE, alpha=False)
    px = [1.0] * (PALETTE_SIZE * PALETTE_SIZE * 4)
    for idx, color in PALETTE.values():
        x, y = idx % PALETTE_SIZE, idx // PALETTE_SIZE
        o = (y * PALETTE_SIZE + x) * 4
        px[o:o + 3] = color
    img.pixels = px
    img.file_format = "PNG"
    img.pack()
    return img


def palette_uv(name):
    idx = PALETTE[name][0]
    x, y = idx % PALETTE_SIZE, idx // PALETTE_SIZE
    return ((x + 0.5) / PALETTE_SIZE, (y + 0.5) / PALETTE_SIZE)


def make_material(img):
    mat = bpy.data.materials.new("StrawberryDaifuku")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Metallic"].default_value = 0.0
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def new_obj(name, bm):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def color_faces(bm, name_fn):
    """Assign palette UVs per face; name_fn(face) -> palette key."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        u = palette_uv(name_fn(f))
        for loop in f.loops:
            loop[uv].uv = u


def build_mochi():
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=1.0)
    for v in bm.verts:
        v.co.z *= 0.72
        # Flatten the bottom so it sits on a surface, with a soft bulge above it.
        if v.co.z < -0.45:
            v.co.z = -0.45
            v.co.xy *= 0.92
    bm.normal_update()
    # Pale pink blush on the lower sides, white everywhere else.
    color_faces(bm, lambda f: "mochi_blush" if f.calc_center_median().z < -0.3 else "mochi")
    obj = new_obj("Mochi", bm)
    obj.location.z = 0.45
    return obj


def build_strawberry():
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.42)
    for v in bm.verts:
        t = (v.co.z / 0.42 + 1) / 2  # 0 at tip (bottom), 1 at top
        radial = 0.25 + 0.75 * t ** 0.55
        v.co.x *= radial
        v.co.y *= radial
        v.co.z *= 1.25
        if v.co.z > 0.35:  # flat-ish shoulders where the hull sits
            v.co.z = 0.35 + (v.co.z - 0.35) * 0.4
    bm.normal_update()
    color_faces(bm, lambda f: "berry")
    obj = new_obj("Strawberry", bm)
    # Pointed end buried in the mochi, wide end + hull poking out the top.
    obj.location.z = 1.22
    return obj


def build_seeds(berry):
    seeds = []
    rings = [(0.12, 6, 0.0), (0.24, 5, 0.6)]
    for z_off, count, phase in rings:
        for i in range(count):
            a = 2 * math.pi * i / count + phase
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.035)
            for v in bm.verts:
                v.co.z *= 1.4
            color_faces(bm, lambda f: "seed")
            obj = new_obj("Seed", bm)
            # Place on the berry surface by ray-casting outward from its axis.
            origin = berry.location + Vector((0, 0, z_off))
            direction = Vector((math.cos(a), math.sin(a), 0.15)).normalized()
            hit, loc, _, _ = berry.ray_cast(origin - berry.location + direction * 2, -direction)
            obj.location = (loc + berry.location) if hit else origin + direction * 0.35
            seeds.append(obj)
    return seeds


def build_hull(berry_top_z):
    parts = []
    leaf_count = 6
    for i in range(leaf_count):
        a = 2 * math.pi * i / leaf_count
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=1.0)
        bmesh.ops.scale(bm, vec=(0.26, 0.10, 0.03), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0.22, 0, 0), verts=bm.verts)
        color_faces(bm, lambda f: "leaf")
        obj = new_obj("Leaf", bm)
        obj.location = (0, 0, berry_top_z)
        obj.rotation_euler = (0, math.radians(8), a)  # droop outward slightly
        parts.append(obj)

    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.035, radius2=0.025, depth=0.16)
    bmesh.ops.translate(bm, vec=(0, 0, 0.08), verts=bm.verts)
    color_faces(bm, lambda f: "stem")
    stem = new_obj("Stem", bm)
    stem.location = (0, 0, berry_top_z)
    stem.rotation_euler = (math.radians(10), 0, 0)
    parts.append(stem)
    return parts


def join_and_finalize(objs, mat):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = obj.data.name = "StrawberryDaifuku"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Pivot at bottom centre so it rests on surfaces when placed in Roblox.
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True

    # Triangulate so Roblox's triangle count matches what we report.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def render_preview(obj):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.render.film_transparent = False

    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.93, 0.95, 0.98, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    scene.world = world

    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(35))
    scene.collection.objects.link(sun)

    bpy.ops.mesh.primitive_plane_add(size=20)
    ground = bpy.context.active_object
    gmat = bpy.data.materials.new("Ground")
    gmat.use_nodes = True
    gmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.85, 0.88, 0.92, 1)
    ground.data.materials.append(gmat)

    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.location = (3.4, -3.4, 2.6)
    target = Vector((0, 0, 0.8))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 50
    scene.collection.objects.link(cam)
    scene.camera = cam

    scene.render.filepath = PREVIEW_PATH
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(ground)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    reset_scene()
    img = make_palette_image()
    mat = make_material(img)

    mochi = build_mochi()
    berry = build_strawberry()
    bpy.context.view_layer.update()
    berry_top = max((berry.matrix_world @ v.co).z for v in berry.data.vertices)
    seeds = build_seeds(berry)
    hull = build_hull(berry_top + 0.01)

    obj = join_and_finalize([mochi, berry, *seeds, *hull], mat)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
    )

    tris = len(obj.data.polygons)
    dims = obj.dimensions
    print(f"Exported {GLB_PATH}")
    print(f"Triangles: {tris}  Size (x,y,z): {dims.x:.2f} x {dims.y:.2f} x {dims.z:.2f}")

    if RENDER_PREVIEW:
        render_preview(obj)
        print(f"Preview: {PREVIEW_PATH}")


if __name__ == "__main__":
    main()
