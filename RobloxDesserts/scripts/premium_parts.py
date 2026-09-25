"""Parts for the premium / rare dessert line.

Rarity is communicated with shape, colour and garnish rather than realistic
reflections, so it survives flat Roblox lighting:
- mochi and pearls carry a *painted* cartoon highlight in their texture;
- 'gold' is a flat warm yellow (no metallic), used for rims and trim;
- motifs (stars, crescents, crowns, beads) are real, chunky geometry.
"""
import math

import dessert_lib as L
import cafe_parts as P
import bpy  # noqa: F401
import bmesh
import numpy as np
from mathutils import Vector

GOLD = "#f4c24f"
HIGHLIGHT_AZ = math.radians(-100)   # painted shine faces the default preview camera / key light
HIGHLIGHT_EL = math.radians(42)


# ------------------------------------------------------------------ mochi

def _sphere_uv(bm, radius):
    """u = azimuth, v = elevation of each vertex direction (seam at -X, hidden at the back)."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        us = []
        for loop in f.loops:
            d = loop.vert.co.normalized()
            us.append(((math.atan2(d.y, d.x) / (2 * math.pi)) % 1.0,
                       math.asin(max(-1.0, min(1.0, d.z))) / math.pi + 0.5))
        # Keep faces that straddle the seam from wrapping across the whole texture.
        if max(u for u, _ in us) - min(u for u, _ in us) > 0.5:
            us = [(u + 1.0 if u < 0.5 else u, v) for u, v in us]
        for loop, (u, v) in zip(f.loops, us):
            loop[uv].uv = (u, v)


def mochi(name, mat, r=0.3, squash=0.76, u=26, v=14):
    """Soft mochi: squashed dome, flat base (base at z=0)."""
    bm = L.uvsphere_bm(u=u, v=v, radius=r)
    _sphere_uv(bm, r)          # UVs from the round sphere, before squashing
    floor = -r * 0.55
    for vert in bm.verts:
        co = vert.co
        if co.z < floor:
            co.z = floor + (co.z - floor) * 0.2
            co.x *= 1.04
            co.y *= 1.04
        co.z = (co.z - floor * 1.0) * squash
    obj = L.obj_from_bm(name, bm, mat)
    return obj


def shine_texture(name, base_hex, out_dir, shade_hex=None, size=256, spot=(0.075, 0.1), rim=True):
    """Flat base colour + slightly deeper underside + painted white highlight."""
    w = h = size
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    base = np.array(L.srgb(base_hex))
    shade = np.array(L.srgb(shade_hex)) if shade_hex else base * 0.86
    rgb = base + (shade - base) * np.clip((0.42 - V) / 0.2, 0, 1)[..., None]
    # Main shine: soft-edged ellipse, plus a small companion dot (anime-style).
    hu = (HIGHLIGHT_AZ / (2 * math.pi)) % 1.0
    hv = HIGHLIGHT_EL / math.pi + 0.5
    du = np.minimum(np.abs(U - hu), 1 - np.abs(U - hu))
    d1 = np.hypot(du / spot[0], (V - hv) / spot[1])
    d2 = np.hypot(np.minimum(np.abs(U - hu - 0.07), 1 - np.abs(U - hu - 0.07)) / (spot[0] * 0.35),
                  (V - hv + 0.1) / (spot[1] * 0.35))
    white = np.array([1.0, 1.0, 1.0])
    a = np.clip((1 - np.minimum(d1, d2)) * 4, 0, 1)[..., None] * 0.92
    rgb = rgb + (white - rgb) * a
    return L.image_from_array(name, rgb, out_dir)


def pearl(name, mat, r=0.05):
    bm = L.uvsphere_bm(u=12, v=8, radius=r)
    _sphere_uv(bm, r)
    return L.obj_from_bm(name, bm, mat)


def pearl_texture(out_dir, name="Pearl_Color", hex_base="#f6ecff"):
    """Pearl: pale lilac-white with a pink blush underside and a bold shine."""
    return shine_texture(name, hex_base, out_dir, shade_hex="#f2c9e2", size=128, spot=(0.1, 0.13))


# ----------------------------------------------------------------- shapes

def rounded_extrude(name, outline, thickness, mat, round_frac=0.35, steps=3, uv_fn=None):
    """Extrude a CCW outline with rounded (quarter-circle) top and bottom edges."""
    b = thickness * round_frac
    rings = []
    for k in range(steps + 1):                       # bottom quarter circle
        a = math.pi / 2 * k / steps
        rings.append((b - b * math.cos(a), b - b * math.sin(a)))
    for k in range(steps + 1):                       # top quarter circle
        a = math.pi / 2 * k / steps
        rings.append((thickness - b + b * math.sin(a), b - b * math.cos(a)))
    return P.loft(name, outline, rings, [mat], lambda c, kind: 0, uv_fn=uv_fn)


def star_outline(R, r_in=0.5, points=5, rounding=1):
    pts = []
    for i in range(points * 2):
        a = math.pi / 2 + math.pi * i / points
        rr = R if i % 2 == 0 else R * r_in
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return P.chaikin(pts, rounding)


def crescent_outline(R, c=0.35, steps=18):
    """Fat crescent opening toward +X (CCW)."""
    t0 = math.radians(40)
    p1 = (R * math.cos(t0), R * math.sin(t0))
    cx = c * R
    ri = math.hypot(p1[0] - cx, p1[1])
    a1 = math.atan2(p1[1], p1[0] - cx)               # inner-circle angle of the tip
    pts = [(R * math.cos(t), R * math.sin(t)) for t in np.linspace(t0, 2 * math.pi - t0, steps * 2)]
    pts += [(cx + ri * math.cos(t), ri * math.sin(t))
            for t in np.linspace(2 * math.pi - a1, a1, steps)[1:-1]]
    return P.chaikin(pts, 2)


def crescent(name, mat, R=0.3, width=0.3, flat=0.55, steps=22, ring_n=12):
    """Puffy crescent moon: a tube swept along an arc whose radius tapers to
    soft points at both tips. Lies in the XY plane opening toward +X; `flat`
    squashes its depth (Z). No concave caps, so it never self-intersects."""
    t0 = math.radians(48)
    rc = R * (1 - width / 2)                          # centre-line radius
    path, radii = [], []
    for t in np.linspace(0, 1, steps):
        a = t0 + (2 * math.pi - 2 * t0) * t
        path.append((rc * math.cos(a) - R * 0.12, rc * math.sin(a), 0.0))
        radii.append(R * width / 2 * max(math.sin(math.pi * t), 0.0) ** 0.6 + R * 0.015)
    obj = P.tube(name, path, radii, mat, ring_n=ring_n, caps=True)
    for v in obj.data.vertices:
        v.co.z *= flat
    return obj


def gem(name, mat, r=0.06):
    """Chunky faceted gem (octagonal brilliant-ish): reads as a jewel, not glass."""
    bm = bmesh.new()
    n = 8
    top = [bm.verts.new((r * 0.6 * math.cos(2 * math.pi * i / n), r * 0.6 * math.sin(2 * math.pi * i / n),
                         r * 0.45)) for i in range(n)]
    mid = [bm.verts.new((r * math.cos(2 * math.pi * (i + 0.5) / n), r * math.sin(2 * math.pi * (i + 0.5) / n),
                         r * 0.15)) for i in range(n)]
    tip = bm.verts.new((0, 0, -r * 0.7))
    bm.faces.new(top)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((top[i], mid[i], top[j]))
        bm.faces.new((mid[i], mid[j], top[j]))
        bm.faces.new((mid[i], tip, mid[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.obj_from_bm(name, bm, mat)


def gem_texture(out_dir, name, hex_color):
    """Flat jewel tone."""
    rgb = np.ones((8, 8, 3)) * np.array(L.srgb(hex_color))
    return L.image_from_array(name, rgb, out_dir)


def gold_flake(name, mat, size=0.05, seed=0):
    """Irregular flat gold-leaf flake."""
    rng = np.random.default_rng(seed)
    n = 7
    pts = [(size * rng.uniform(0.6, 1.0) * math.cos(2 * math.pi * i / n),
            size * rng.uniform(0.6, 1.0) * math.sin(2 * math.pi * i / n)) for i in range(n)]
    return rounded_extrude(name, P.chaikin(pts, 1), 0.012, mat, round_frac=0.3, steps=1)


def lathe_multi(name, profile, mats, pick, segments=40):
    obj = P.lathe(name, profile, mats[0], segments=segments)
    for m in mats[1:]:
        obj.data.materials.append(m)
    for poly in obj.data.polygons:
        poly.material_index = pick(poly.center)
    return obj


def place_on(obj, target_z, xy=(0.0, 0.0)):
    """Drop an object so its lowest point sits at target_z."""
    bpy.context.view_layer.update()
    low = min((obj.matrix_world @ Vector(c)).z for c in obj.bound_box)
    obj.location.z += target_z - low
    obj.location.x += xy[0]
    obj.location.y += xy[1]
    return obj
