"""Crème Brûlée: shallow fluted pastel ramekin, glossy caramelized golden top
with darker toasted spots, and a gold spoon beside it. Stylized Roblox look."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
from bingsu_common import mint_leaf as B_mint_leaf  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

NAME = "CremeBrulee"
FLUTES = 24
SEG = FLUTES * 3
TOP_Z = 0.245
# Ramekin profile (r, z, fluted?) outer bottom -> rolled rim -> inner floor.
RAMEKIN = [(0.0, 0.0, 0), (0.4, 0.0, 0), (0.435, 0.018, 0), (0.46, 0.05, 1), (0.47, 0.13, 1),
           (0.47, 0.22, 1), (0.468, 0.265, 0), (0.45, 0.285, 0), (0.425, 0.28, 0), (0.415, 0.26, 0),
           (0.41, 0.2, 0), (0.0, 0.05, 0)]


def build_ramekin(mat):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    rows = []
    for r, z, fluted in RAMEKIN:
        row = []
        for j in range(SEG):
            a = 2 * math.pi * j / SEG
            rr = r + (0.014 * math.cos(FLUTES * a) if fluted else 0.0)
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        rows.append(row)
    n = len(rows)
    for k in range(n - 1):
        for j in range(SEG):
            j2 = (j + 1) % SEG
            f = bm.faces.new((rows[k][j], rows[k][j2], rows[k + 1][j2], rows[k + 1][j]))
            for loop in f.loops:                       # v = height (lets the rim take a white band)
                loop[uv].uv = (0.5, min(loop.vert.co.z / 0.285, 1.0))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.obj_from_bm("Ramekin", bm, mat)


def ramekin_texture(out_dir):
    h = 128
    v = (np.arange(h) + 0.5) / h
    body = np.array(L.srgb("#b9dcf6"))
    white = np.array(L.srgb("#fffaf2"))
    rgb = np.where((v > 0.88)[:, None], white, body)[:, None, :].repeat(8, axis=1)
    return L.image_from_array("Ramekin_Color", rgb, out_dir)


def caramel_texture(out_dir):
    """Golden-amber caramel: glassy lighter centre, deeper rim, clustered toasted
    patches of mixed sizes, and a couple of crack lines from a spoon tap."""
    n = 512
    a = (np.arange(n) + 0.5) / n * 2 - 1
    X, Y = np.meshgrid(a, a)
    r = np.hypot(X, Y)
    gold = np.array(L.srgb("#f3b957"))
    light = np.array(L.srgb("#fcdb8e"))
    toast = np.array(L.srgb("#b8682c"))
    rgb = gold + (light - gold) * np.clip(1 - r / 0.65, 0, 1)[..., None] * 0.7
    rgb = rgb + (toast - rgb) * np.clip((r - 0.78) / 0.22, 0, 1)[..., None] * 0.55
    rng = np.random.default_rng(21)
    spots = np.zeros((n, n))
    for _ in range(12):                                  # clusters of 2-4 overlapping blobs
        cx, cy = rng.uniform(-0.72, 0.72, 2)
        if math.hypot(cx, cy) > 0.78:
            continue
        for _ in range(rng.integers(2, 5)):
            bx, by = cx + rng.normal(0, 0.05), cy + rng.normal(0, 0.05)
            rad = rng.uniform(0.045, 0.1)
            spots = np.maximum(spots, np.clip((rad - np.hypot(X - bx, Y - by)) / 0.02, 0, 1)
                               * rng.uniform(0.55, 0.9))
    rgb = rgb + (toast - rgb) * spots[..., None]
    # Crack lines radiating from a tap point.
    px, py = 0.25, -0.2
    for ang, length in ((0.3, 0.35), (2.2, 0.3), (4.0, 0.28)):
        dx, dy = math.cos(ang), math.sin(ang)
        t = (X - px) * dx + (Y - py) * dy
        d = np.abs(-(X - px) * dy + (Y - py) * dx)
        rgb[(t > 0) & (t < length) & (d < 0.014 * (1 - t / length) + 0.005)] = L.srgb("#8f4a1c")
    return L.image_from_array("Caramel_Color", rgb, out_dir)


def build_top(mat):
    R = 0.418
    bm = bmesh.new()
    rings, seg = 6, 48
    center = bm.verts.new((0, 0, TOP_Z + 0.012))
    prev = None
    for i in range(1, rings + 1):
        rr = R * i / rings
        dz = 0.012 * (1 - (i / rings) ** 2)
        ring = [bm.verts.new((rr * math.cos(2 * math.pi * j / seg), rr * math.sin(2 * math.pi * j / seg),
                              TOP_Z + dz)) for j in range(seg)]
        for j in range(seg):
            k = (j + 1) % seg
            bm.faces.new((center, ring[j], ring[k]) if prev is None else (prev[j], ring[j], ring[k], prev[k]))
        prev = ring
    obj = L.obj_from_bm("CaramelTop", bm, mat)
    L.planar_uv(obj, 0, 1, (-R, R, -R, R))
    return obj


def build_spoon(mat):
    parts = []
    bm = L.uvsphere_bm(u=16, v=8, radius=1.0)
    for v in bm.verts:
        v.co.x *= 0.1
        v.co.y *= 0.07
        v.co.z *= 0.025
    bowl = L.obj_from_bm("SpoonBowl", bm, mat)
    bowl.location = (0, 0, 0.025)
    parts.append(bowl)
    def centre_z(x):                                 # handle rises gently away from the bowl
        t = min(max((x - 0.08) / 0.4, 0.0), 1.0)
        return 0.03 + 0.07 * t ** 2

    ts = np.linspace(0, 1, 8)
    path = [Vector((0.08 + 0.4 * t, 0.0, centre_z(0.08 + 0.4 * t))) for t in ts]
    radii = [0.018 + 0.012 * t for t in ts]
    handle = P.tube("SpoonHandle", path, radii, mat, ring_n=8, caps=True)
    for v in handle.data.vertices:                   # flatten the round tube into a ribbon
        zc = centre_z(v.co.x)
        v.co.z = zc + (v.co.z - zc) * 0.45
    parts.append(handle)
    return parts


def build(out_dir):
    ramekin = L.make_material("Ramekin", ramekin_texture(out_dir), roughness=0.4, specular=0.35)
    caramel = L.make_material("CaramelTop", caramel_texture(out_dir), roughness=0.25, specular=0.5)
    gold = L.make_material("Spoon", L.solid_image("Spoon_Color", "#e7bf6e", out_dir), roughness=0.35,
                           specular=0.5)
    skin = L.make_material("Strawberry", P.strawberry_texture(out_dir), roughness=0.5, specular=0.3)
    cut = L.make_material("StrawberryCut", P.cut_texture(out_dir), roughness=0.55, specular=0.25)
    mint = L.make_material("Mint", L.solid_image("Mint_Color", "#4fc463", out_dir), roughness=0.7, specular=0.25)
    parts = [build_ramekin(ramekin), build_top(caramel)]
    # Small garnish near the rim: strawberry half (cut side up) + a mint leaf.
    h = P.strawberry_half(skin, cut, 0.1)
    h.rotation_euler = (math.radians(70), 0, 0)
    P.move([h], dx=-0.14, dy=0.12, dz=TOP_Z + 0.04, rot_z=math.radians(150))
    parts.append(h)
    leaf = B_mint_leaf(mint)
    P.move([leaf], dx=-0.06, dy=0.2, dz=TOP_Z + 0.03, rot_z=math.radians(60))
    parts.append(leaf)
    parts += P.move(build_spoon(gold), dx=0.6, dy=-0.2, rot_z=math.radians(-70))
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.6, -1.0, 0.8), (0.15, -0.35, 1.3)),
                          bg="#f4eee6", ground="#efe6da", margin=0.95)
    sys.exit(0 if ok else 1)
