"""Reusable stylized café parts: rounded lofts (cake slices), lathes,
piped cream dollops and strawberries. Built on dessert_lib."""
import math

import dessert_lib as L
import bpy  # noqa: F401  (must be imported before bmesh)
import bmesh
import numpy as np
from mathutils import Vector

# ------------------------------------------------------------- 2D outlines


def chaikin(points, iterations=2, closed=True):
    """Corner-cutting subdivision: rounds every corner of a polygon."""
    pts = [np.array(p, float) for p in points]
    for _ in range(iterations):
        out = []
        n = len(pts)
        rng = range(n) if closed else range(n - 1)
        if not closed:
            out.append(pts[0])
        for i in rng:
            a, b = pts[i], pts[(i + 1) % n]
            out += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        if not closed:
            out.append(pts[-1])
        pts = out
    return pts


def offset_outline(pts, d):
    """Move each vertex of a CCW closed outline inward by d (negative = outward)."""
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        e1, e2 = p1 - p0, p2 - p1
        n1 = np.array((-e1[1], e1[0])) / (np.linalg.norm(e1) + 1e-9)   # left normal = inward for CCW
        n2 = np.array((-e2[1], e2[0])) / (np.linalg.norm(e2) + 1e-9)
        nrm = n1 + n2
        nrm /= np.linalg.norm(nrm) + 1e-9
        out.append(p1 + nrm * d)
    return out


def wedge_outline(radius, angle_deg, arc_steps=10, tip=0.05):
    """Cake-slice outline (CCW), tip near the origin pointing toward -X.
    The tip is blunted by `tip` studs so inward offsets never pinch."""
    half = math.radians(angle_deg) / 2
    w = tip * math.tan(half)
    pts = [(tip, -w), None]
    pts.pop()
    for i in range(arc_steps + 1):
        a = -half + 2 * half * i / arc_steps
        pts.append((radius * math.cos(a), radius * math.sin(a)))
    pts.append((tip, w))
    # Densify the straight cut edges so corner rounding stays local.
    dense = []
    last = len(pts) - 1
    for i in range(len(pts)):
        a, b = np.array(pts[i]), np.array(pts[(i + 1) % len(pts)])
        steps = 4 if (i == 0 or i == last - 1) else 1
        for k in range(steps):
            dense.append(a + (b - a) * k / steps)
    return chaikin(dense, 2)


# ------------------------------------------------------------------ meshes

def obj_from_bm_multi(name, bm, mats):
    bm.loops.layers.uv.verify()
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for m in mats:
        mesh.materials.append(m)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def loft(name, outline, rings, mats, mat_fn, uv_fn=None):
    """Stack offset copies of a 2D outline.

    rings: list of (z, inset). mat_fn(center, kind) -> material index, where
    kind is 'side', 'top' or 'bottom'. uv_fn(co) -> (u, v), optional.
    """
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    layers = []
    for z, inset in rings:
        ring = offset_outline(outline, inset) if inset else outline
        layers.append([bm.verts.new((p[0], p[1], z)) for p in ring])
    n = len(outline)
    for a, b in zip(layers, layers[1:]):
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new((a[i], a[j], b[j], b[i]))
            f.material_index = mat_fn(f.calc_center_median(), "side")
    top = bm.faces.new(layers[-1])
    top.material_index = mat_fn(top.calc_center_median(), "top")
    bot = bm.faces.new(list(reversed(layers[0])))
    bot.material_index = mat_fn(bot.calc_center_median(), "bottom")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # Triangulate the caps nicely (fan from the centre would give slivers).
    bmesh.ops.triangulate(bm, faces=[top, bot], quad_method="BEAUTY", ngon_method="BEAUTY")
    if uv_fn:
        for f in bm.faces:
            for loop in f.loops:
                loop[uv].uv = uv_fn(loop.vert.co)
    return obj_from_bm_multi(name, bm, mats)


def lathe(name, profile, mat, segments=40, z0=0.0):
    bm = bmesh.new()
    verts = [bm.verts.new((r, 0, z + z0)) for r, z in profile]
    edges = [bm.edges.new((a, b)) for a, b in zip(verts, verts[1:])]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=2 * math.pi, steps=segments, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.obj_from_bm(name, bm, mat)


def cream_dollop(name, mat, radius=0.2, height=0.28, ridges=8, twist=1.3):
    """Piped whipped-cream swirl: star cross-section, tapering and twisting to a soft tip."""
    bm = bmesh.new()
    seg = ridges * 4
    rows = 11
    rings = []
    for k in range(rows):
        t = k / (rows - 1)
        r = radius * (1 - t ** 1.6) ** 0.7 if k < rows - 1 else 0.0
        z = height * t
        amp = 0.16 * (1 - t) + 0.04
        ring = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            rr = r * (1 + amp * math.cos(ridges * a + twist * t * math.pi))
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for j in range(seg):
            i2 = (j + 1) % seg
            bm.faces.new((a[j], a[i2], b[i2], b[j]))
    bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:              # v = height up the swirl (lets textures colour the tip)
        for loop in f.loops:
            loop[uv].uv = (0.5, loop.vert.co.z / height)
    return L.obj_from_bm(name, bm, mat)


def strawberry_texture(out_dir, name="Strawberry_Color"):
    """Flat saturated red with a few big seeds (matches the daifuku berry)."""
    h = w = 256
    rgb = np.broadcast_to(np.array(L.srgb("#f0385a")), (h, w, 3)).copy()
    seed = np.array(L.srgb("#fff0a3"))
    yy, xx = np.mgrid[0:h, 0:w]
    for r in range(4):
        vy = 0.3 + r * 0.14
        for c in range(7):
            ux = (c + 0.5 * (r % 2)) / 7
            cy, cx = vy * h, ux * w
            dx = np.minimum(np.abs(xx - cx), w - np.abs(xx - cx))
            rgb[(dx / 4.5) ** 2 + ((yy - cy) / 6.5) ** 2 < 1] = seed
    return L.image_from_array(name, rgb, out_dir)


def strawberry(mat, leaf_mat, radius=0.2, leaves=5):
    """Whole stylized strawberry, tip down, hull on top. Returns parts; base at z=0."""
    bm = L.uvsphere_bm(u=20, v=12, radius=radius)
    for vert in bm.verts:
        co = vert.co
        t = min(1.0, max(0.0, (co.z / radius + 1) / 2))
        radial = 0.35 + 0.65 * t ** 0.45
        co.x *= radial
        co.y *= radial
        co.z *= 1.2
        if co.z > radius:
            co.z = radius + (co.z - radius) * 0.6
    berry = L.obj_from_bm("Strawberry", bm, mat)
    bottom = -radius * 1.2
    top = radius + (radius * 1.2 - radius) * 0.6
    berry.location.z = -bottom
    parts = [berry]
    hull_z = top - bottom - 0.01
    s = radius / 0.34   # leaf sizes were tuned on a 0.34 berry
    for i in range(leaves):
        a = 2 * math.pi * i / leaves + 0.3
        lb = L.uvsphere_bm(u=10, v=6, radius=1.0)
        for vert in lb.verts:
            co = vert.co
            tt = (co.x + 1) / 2
            co.y *= 1 - 0.75 * tt ** 1.5
            co.z -= 0.9 * tt ** 2
        bmesh.ops.scale(lb, vec=(0.15 * s, 0.11 * s, 0.05 * s), verts=lb.verts)
        bmesh.ops.translate(lb, vec=(0.12 * s, 0, 0), verts=lb.verts)
        leaf = L.obj_from_bm("Leaf", lb, leaf_mat)
        leaf.location = (0, 0, hull_z)
        leaf.rotation_euler = (0, math.radians(4), a)
        parts.append(leaf)
    sb = bmesh.new()
    bmesh.ops.create_cone(sb, cap_ends=True, segments=8, radius1=0.045 * s, radius2=0.035 * s, depth=0.14 * s)
    bmesh.ops.translate(sb, vec=(0, 0, 0.07 * s), verts=sb.verts)
    stem = L.obj_from_bm("Stem", sb, leaf_mat)
    stem.location = (0, 0, hull_z)
    stem.rotation_euler = (math.radians(12), 0, 0)
    parts.append(stem)
    return parts


def move(parts, dx=0.0, dy=0.0, dz=0.0, rot_z=0.0, tilt=(0.0, 0.0)):
    """Rigidly place a group of parts (rotate about the group origin, then translate)."""
    from mathutils import Matrix, Vector
    bpy.context.view_layer.update()   # make matrix_world reflect loc/rot set on fresh objects
    m = (Matrix.Translation(Vector((dx, dy, dz))) @ Matrix.Rotation(rot_z, 4, "Z")
         @ Matrix.Rotation(tilt[0], 4, "X") @ Matrix.Rotation(tilt[1], 4, "Y"))
    for p in parts:
        p.matrix_world = m @ p.matrix_world
    return parts


def cut_texture(out_dir):
    """Strawberry cross-section: white heart core, pale-pink flesh, red rim."""
    n = 128
    a = (np.arange(n) + 0.5) / n * 2 - 1
    X, Z = np.meshgrid(a, a)
    r = np.hypot(X / 0.95, Z)
    rgb = np.broadcast_to(np.array(L.srgb("#f0385a")), (n, n, 3)).copy()
    rgb[r < 0.78] = L.srgb("#ff9fb2")
    core = (X / 0.22) ** 2 + ((Z - 0.1) / 0.5) ** 2 < 1
    rgb[core] = L.srgb("#ffe3e8")
    return L.image_from_array("StrawberryCut_Color", rgb, out_dir)


def strawberry_half(skin, cut, HALF_R=0.16):
    """Berry shape (tip up), halved along Y; the cut face (+Y) gets the cut material."""
    bm = L.uvsphere_bm(u=16, v=10, radius=HALF_R)
    for vert in bm.verts:
        co = vert.co
        t = min(1.0, max(0.0, (co.z / HALF_R + 1) / 2))
        radial = 0.35 + 0.65 * t ** 0.45
        co.x *= radial
        co.y *= radial
        co.z *= 1.2
        if co.z > HALF_R:
            co.z = HALF_R + (co.z - HALF_R) * 0.6
        co.z = -co.z                                  # tip up
    bmesh.ops.reverse_faces(bm, faces=bm.faces)       # mirroring flipped the winding
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, 1, 0),
                                 clear_outer=True)
    cut_edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    new = bmesh.ops.holes_fill(bm, edges=cut_edges, sides=0)["faces"]
    bmesh.ops.triangulate(bm, faces=new)
    uv = bm.loops.layers.uv.verify()
    cap = [f for f in bm.faces if f.normal.y > 0.9]
    xs = [v.co.x for f in cap for v in f.verts]
    zs = [v.co.z for f in cap for v in f.verts]
    for f in cap:
        f.material_index = 1
        for loop in f.loops:
            co = loop.vert.co
            loop[uv].uv = ((co.x - min(xs)) / (max(xs) - min(xs)), (co.z - min(zs)) / (max(zs) - min(zs)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm_multi("StrawberryHalf", bm, [skin, cut])


def tube(name, path, radii, mat, ring_n=10, closed=False, caps=False):
    """Sweep a circle along a polyline. Open ends are buried in other geometry;
    closed=True joins the last ring back to the first (seamless loop)."""
    bm = bmesh.new()
    rings = []
    pts = [Vector(p) for p in path]
    for i, p in enumerate(pts):
        if closed:
            tan = (pts[(i + 1) % len(pts)] - pts[i - 1]).normalized()
        else:
            tan = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        # All tubes here lie in vertical XZ planes: a fixed Y reference never flips.
        ref = Vector((0, 1, 0)) if abs(tan.y) < 0.9 else Vector((1, 0, 0))
        nx = tan.cross(ref).normalized()
        ny = tan.cross(nx).normalized()
        r = radii[i]
        rings.append([bm.verts.new(p + (nx * math.cos(a) + ny * math.sin(a)) * r)
                      for a in (2 * math.pi * j / ring_n for j in range(ring_n))])
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for a, b in pairs:
        for j in range(ring_n):
            k = (j + 1) % ring_n
            bm.faces.new((a[j], a[k], b[k], b[j]))
    if caps and not closed:                      # close visible ends (e.g. a spoon handle tip)
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.obj_from_bm(name, bm, mat)
