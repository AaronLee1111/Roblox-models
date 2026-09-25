"""Shared bingsu builder: pastel bowl, lumpy shaved-ice mound with painted
sauce drizzle + condensed milk, fruit rings, and an ice-cream scoop on top.
Variants (mango / strawberry) only supply colours and fruit builders."""
import math

import dessert_lib as L
import cafe_parts as P
import bpy  # noqa: F401
import bmesh
import numpy as np
from mathutils import Matrix, Vector

SEG = 48
RIM_Z = 0.56
# Shaved-ice base profile (radius, z): starts inside the bowl, overhangs the rim,
# domes up to a flattish crown that holds the scoop.
MOUND = [(0.56, 0.46), (0.63, 0.57), (0.62, 0.66), (0.55, 0.82), (0.45, 0.98),
         (0.33, 1.12), (0.2, 1.2), (0.0, 1.23)]
BOWL = [(0.0, 0.0), (0.26, 0.0), (0.28, 0.035), (0.26, 0.07), (0.34, 0.12), (0.48, 0.22),
        (0.59, 0.34), (0.655, 0.46), (0.68, RIM_Z - 0.015), (0.665, RIM_Z + 0.012),
        (0.635, RIM_Z - 0.01), (0.56, 0.42), (0.0, 0.3)]


# ---------------------------------------------------------------- mound

def _profile(s):
    """Arc-length parameterised base profile: s in [0,1] -> (r, z)."""
    pts = np.array(MOUND)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
    return float(np.interp(s, cum, pts[:, 0])), float(np.interp(s, cum, pts[:, 1]))


def mound_point(theta, s):
    """Lumpy snow-mountain surface. Lumps fade out inside the bowl and at the crown."""
    r, z = _profile(s)
    fade = math.sin(math.pi * min(max((s - 0.08) / 0.8, 0), 1))
    # Fluffy "snow drift" lumps: a few big lobes plus smaller puffs.
    lump = (0.10 * math.sin(6 * theta + 9 * s) + 0.07 * math.sin(4 * theta - 13 * s + 1.3)
            + 0.05 * math.sin(10 * theta + 5 * s + 0.4))
    r *= 1 + lump * fade
    return Vector((r * math.cos(theta), r * math.sin(theta), z + 0.05 * lump * fade))


def mound_normal(theta, s, eps=1e-3):
    p = mound_point(theta, s)
    du = mound_point(theta + eps, s) - p
    dv = mound_point(theta, min(s + eps, 1.0)) - p
    n = dv.cross(du)
    if n.length < 1e-9:
        return Vector((0, 0, 1))
    n.normalize()
    return n if n.dot(Vector((p.x, p.y, 0.3))) > 0 else -n


def build_mound(mat, rows=20):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    grid = []
    for k in range(rows + 1):
        s = k / rows
        grid.append([bm.verts.new(mound_point(2 * math.pi * j / SEG, s)) for j in range(SEG)])
    for k in range(rows):
        for j in range(SEG):
            j2 = (j + 1) % SEG
            f = bm.faces.new((grid[k][j], grid[k][j2], grid[k + 1][j2], grid[k + 1][j]))
            for loop, (jj, kk) in zip(f.loops, ((j, k), (j + 1, k), (j + 1, k + 1), (j, k + 1))):
                loop[uv].uv = (jj / SEG, kk / rows)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.obj_from_bm("ShavedIce", bm, mat)


def ice_texture(out_dir, name, sauce_hex, drips=6, seed=3):
    """Shaved ice with a pooled sauce crown, chunky drips and a condensed-milk ribbon.
    Texture space: u = angle around the mound, v = s (0 bottom -> 1 crown)."""
    w = h = 512
    u = (np.arange(w) + 0.5) / w
    v = (np.arange(h) + 0.5) / h
    U, V = np.meshgrid(u, v)
    ice = np.array(L.srgb("#fbfcff"))
    sauce = np.array(L.srgb(sauce_hex))
    milk = np.array(L.srgb("#fff0bd"))
    rgb = np.broadcast_to(ice, (h, w, 3)).copy()
    # Condensed-milk ribbon zig-zagging around the upper slope.
    zig = 0.58 + 0.045 * np.sin(2 * np.pi * 7 * U)
    rgb[np.abs(V - zig) < 0.016] = milk
    # Sauce: wavy pooled crown + drips running down between the fruit.
    crown = 0.8 + 0.03 * np.sin(2 * np.pi * 5 * U + 0.7)
    mask = V > crown
    rng = np.random.default_rng(seed)
    for k in range(drips):
        uc = (k + 0.5 + rng.uniform(-0.15, 0.15)) / drips
        end = rng.uniform(0.5, 0.64)
        du = np.minimum(np.abs(U - uc), 1 - np.abs(U - uc)) * 2 * np.pi   # angular distance
        width = 0.075 * (0.6 + 0.4 * np.clip((V - end) / (crown.mean() - end), 0, 1))
        body = (du < width) & (V > end) & (V <= crown + 0.01)
        tip = (du / 0.09) ** 2 + ((V - end) / 0.03) ** 2 < 1                 # round drop
        mask |= body | tip
    rgb[mask] = sauce
    return L.image_from_array(name, rgb, out_dir)


# ------------------------------------------------------------------ bowl

def bowl_texture(out_dir, hex_body):
    h = 128
    v = (np.arange(h) + 0.5) / h
    body = np.array(L.srgb(hex_body))
    white = np.array(L.srgb("#fffaf2"))
    rgb = np.where((v > 0.9)[:, None], white, body)[:, None, :].repeat(8, axis=1)
    return L.image_from_array("Bowl_Color", rgb, out_dir)


def build_bowl(mat):
    obj = P.lathe("Bowl", BOWL, mat, segments=SEG)
    L.planar_uv(obj, 0, 2, (-1, 1, 0.0, RIM_Z + 0.01))
    return obj


# ------------------------------------------------------------ placement

def frame_on_mound(theta, s, lift, tilt_up=0.35, spin=0.0):
    """Matrix placing an object on the mound: local +Y faces outward, +Z roughly up."""
    p = mound_point(theta, s)
    n = mound_normal(theta, s)
    out = Vector((math.cos(theta), math.sin(theta), 0))
    y = (out + Vector((0, 0, tilt_up))).normalized()
    z = Vector((0, 0, 1)) - y * y.z
    z.normalize()
    x = y.cross(z)
    rot = Matrix((x, y, z)).transposed().to_4x4()
    return Matrix.Translation(p + n * lift) @ rot @ Matrix.Rotation(spin, 4, "Y")


def scoop(mat, radius=0.21, ruffles=10):
    """Ice-cream scoop: round ball with a ruffled 'scooped' skirt near the base."""
    bm = L.uvsphere_bm(u=30, v=12, radius=radius)
    for vert in bm.verts:
        co = vert.co
        t = co.z / radius
        if t < -0.15:
            a = math.atan2(co.y, co.x)
            k = 1 + 0.2 * math.cos(ruffles * a) * min(1.0, (-t - 0.15) / 0.4)
            co.x *= k * 1.08
            co.y *= k * 1.08
            co.z = -0.15 * radius + (co.z + 0.15 * radius) * 0.55
    return L.obj_from_bm("Scoop", bm, mat)


def mint_leaf(mat, size=0.13):
    lb = L.uvsphere_bm(u=10, v=6, radius=1.0)
    for vert in lb.verts:
        co = vert.co
        tt = (co.x + 1) / 2
        co.y *= 1 - 0.8 * tt ** 1.4
        co.z += 0.25 * (co.y ** 2)          # slight fold along the vein
    bmesh.ops.scale(lb, vec=(size, size * 0.55, size * 0.16), verts=lb.verts)
    bmesh.ops.translate(lb, vec=(size * 0.8, 0, 0), verts=lb.verts)
    return L.obj_from_bm("MintLeaf", lb, mat)


def crown_z():
    return mound_point(0.0, 1.0).z
