"""Afternoon Tea Set: three-tier porcelain stand (gold pole + ring finial) with
finger sandwiches, scones with jam and macarons, plus a pastel teapot and a
teacup on its saucer. Stylized Roblox look, one prop.

All small pastries share ONE palette-textured material (each face's UVs point
at a flat colour cell), which keeps the whole set to five materials."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

NAME = "AfternoonTeaSet"
SEG = 40

PALETTE = ["#fff1d6", "#9fd67f", "#ffb3a6", "#e8a24e",      # bread, cucumber, salmon, scone top
           "#fff0c9", "#e8355a", "#fff8ef", "#ffadc6",      # scone side, jam, cream, macaron pink
           "#b7e39a", "#cdb8f2", "#ffe38a", "#fff4e2"]      # macaron green, lavender, yellow, filling
CELL = {name: i for i, name in enumerate(
    ["bread", "cucumber", "salmon", "scone_top", "scone_side", "jam", "cream",
     "mac_pink", "mac_green", "mac_lav", "mac_yellow", "filling"])}
GRID = 4          # palette is GRID x GRID cells, each cell 4x4 px (no bleed with linear filtering)

# Tier layout: (plate radius, plate z)
TIERS = [(0.62, 0.10), (0.5, 0.58), (0.38, 1.02)]
POLE_TOP = 1.3


# ---------------------------------------------------------------- palette

def palette_texture(out_dir):
    px = 4
    rgb = np.ones((GRID * px, GRID * px, 3))
    for i, hexc in enumerate(PALETTE):
        x, y = i % GRID, i // GRID
        rgb[y * px:(y + 1) * px, x * px:(x + 1) * px] = L.srgb(hexc)
    return L.image_from_array("Pastries_Palette", rgb, out_dir)


def cell_uv(name):
    i = CELL[name]
    return ((i % GRID + 0.5) / GRID, (i // GRID + 0.5) / GRID)


def paint(obj, fn):
    """Point each face's UVs at one palette cell: fn(center, normal) -> cell name."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        u = cell_uv(fn(poly.center, poly.normal))
        for li in poly.loop_indices:
            uv[li].uv = u
    return obj


def paint_all(obj, name):
    return paint(obj, lambda c, n: name)


# ------------------------------------------------------------------ helpers

def lathe_multi(name, profile, mats, pick, segments=SEG):
    """Lathe with per-face material: pick(face_center) -> material index."""
    obj = P.lathe(name, profile, mats[0], segments=segments)
    for m in mats[1:]:
        obj.data.materials.append(m)
    for poly in obj.data.polygons:
        poly.material_index = pick(poly.center)
    return obj


def plate_profile(R, t=0.05):
    return [(0.0, 0.0), (R * 0.5, 0.0), (R * 0.56, 0.012), (R * 0.9, 0.03), (R, 0.075),
            (R - 0.025, 0.088), (R * 0.88, 0.055), (R * 0.56, t), (0.0, t)]


# ------------------------------------------------------------------ stand

def build_stand(porcelain, gold):
    parts = []
    # Foot under the bottom plate.
    parts.append(P.lathe("Foot", [(0.0, 0.0), (0.2, 0.0), (0.21, 0.025), (0.12, 0.05),
                                  (0.07, 0.1), (0.0, 0.1)], gold, segments=24))
    for R, z in TIERS:
        prof = [(r, zz + z) for r, zz in plate_profile(R)]
        parts.append(lathe_multi("Plate", prof, [porcelain, gold],
                                 lambda c, R=R: 1 if math.hypot(c.x, c.y) > R * 0.93 else 0))
    pb = bmesh.new()
    bmesh.ops.create_cone(pb, cap_ends=True, segments=12, radius1=0.035, radius2=0.035,
                          depth=POLE_TOP - 0.08)
    pole = L.obj_from_bm("Pole", pb, gold)
    pole.location = (0, 0, 0.08 + (POLE_TOP - 0.08) / 2)
    parts.append(pole)
    # Collars where the pole meets each plate (hides the join, reads as metalwork).
    for R, z in TIERS[1:]:
        c = P.lathe("Collar", [(0.0, -0.02), (0.06, -0.02), (0.075, 0.0), (0.06, 0.02), (0.0, 0.02)],
                    gold, segments=16)
        c.location = (0, 0, z + 0.05)
        parts.append(c)
    # Ring finial.
    ring = [Vector((0.1 * math.cos(a), 0.0, POLE_TOP + 0.1 + 0.1 * math.sin(a)))
            for a in np.linspace(-math.pi / 2, 1.5 * math.pi, 20, endpoint=False)]
    parts.append(P.tube("Finial", ring, [0.026] * len(ring), gold, ring_n=8, closed=True))
    return parts


# --------------------------------------------------------------- pastries

def sandwich(mat):
    """Crustless finger sandwich: rounded triangle, bread / filling / bread."""
    outline = P.chaikin([(0.0, -0.16), (0.3, 0.0), (0.0, 0.16)], 2)
    t1, t2, t3 = 0.055, 0.105, 0.16
    rings = [(0.0, 0.01), (0.012, 0.0), (t1, 0.0), (t1, -0.012), (t2, -0.012), (t2, 0.0),
             (t3 - 0.012, 0.0), (t3, 0.012)]
    obj = P.loft("Sandwich", outline, rings, [mat], lambda c, k: 0)
    return obj, (t1, t2)


def scone(mat, R=0.13, H=0.14):
    prof = []
    for k in range(9):
        phi = -math.pi / 2 + math.pi * k / 8
        c, s = math.cos(phi), math.sin(phi)
        prof.append((R * abs(c) ** 0.7, H / 2 + H / 2 * math.copysign(abs(s) ** 0.7, s)))
    prof[0] = (0.0, prof[0][1])
    prof[-1] = (0.0, prof[-1][1])
    obj = P.lathe("Scone", prof, mat, segments=20)
    return paint(obj, lambda c, n: "scone_top" if n.z > 0.55 else "scone_side")


def macaron(mat, color, R=0.1):
    parts = []
    for z in (0.04, 0.11):
        bm = L.uvsphere_bm(u=16, v=6, radius=R)
        for v in bm.verts:
            v.co.z *= 0.4
        shell = L.obj_from_bm("Shell", bm, mat)
        shell.location.z = z
        parts.append(paint_all(shell, color))
    fb = bmesh.new()
    bmesh.ops.create_cone(fb, cap_ends=True, segments=16, radius1=R * 0.92, radius2=R * 0.92, depth=0.05)
    fill = L.obj_from_bm("Filling", fb, mat)
    fill.location.z = 0.075
    parts.append(paint_all(fill, "filling"))
    return parts


# -------------------------------------------------------------- tea things

def build_teapot(ceramic, gold):
    body = [(0.0, 0.0), (0.18, 0.0), (0.22, 0.03), (0.3, 0.12), (0.33, 0.24), (0.3, 0.36),
            (0.22, 0.43), (0.17, 0.45), (0.0, 0.45)]
    parts = [P.lathe("TeapotBody", body, ceramic, segments=32)]
    lid = P.lathe("Lid", [(0.0, 0.0), (0.19, 0.0), (0.18, 0.03), (0.12, 0.07), (0.0, 0.08)], ceramic,
                  segments=24)
    lid.location.z = 0.44
    parts.append(lid)
    kb = L.uvsphere_bm(u=12, v=8, radius=0.05)
    knob = L.obj_from_bm("Knob", kb, gold)
    knob.location.z = 0.56
    parts.append(knob)
    spout = [(0.24, 0, 0.14), (0.34, 0, 0.18), (0.42, 0, 0.26), (0.47, 0, 0.35), (0.52, 0, 0.42)]
    parts.append(P.tube("Spout", spout, [0.075, 0.065, 0.055, 0.047, 0.042], ceramic))
    handle = [Vector((-0.27 - 0.17 * math.cos(a), 0.0, 0.25 + 0.14 * math.sin(a)))
              for a in np.linspace(-math.pi / 2, math.pi / 2, 11)]
    handle = [Vector((-0.27, 0, 0.11))] + handle + [Vector((-0.27, 0, 0.39))]
    parts.append(P.tube("TeapotHandle", handle, [0.04] * len(handle), ceramic))
    return parts


def build_teacup(porcelain, ceramic, gold, tea):
    parts = [lathe_multi("Saucer", [(0.0, 0.0), (0.14, 0.0), (0.16, 0.015), (0.26, 0.03), (0.3, 0.055),
                                    (0.29, 0.065), (0.24, 0.045), (0.15, 0.035), (0.0, 0.035)],
                         [ceramic], lambda c: 0, segments=32)]
    cup = [(0.0, 0.035), (0.08, 0.035), (0.1, 0.045), (0.15, 0.1), (0.18, 0.18), (0.19, 0.24),
           (0.17, 0.235), (0.16, 0.18), (0.13, 0.11), (0.0, 0.09)]
    parts.append(lathe_multi("Cup", cup, [porcelain, gold],
                             lambda c: 1 if c.z > 0.225 else 0, segments=32))
    tb = bmesh.new()
    bmesh.ops.create_circle(tb, cap_ends=True, segments=24, radius=0.162)
    surf = L.obj_from_bm("Tea", tb, tea)
    surf.location.z = 0.2
    parts.append(surf)
    h = [Vector((0.175 + 0.07 * math.cos(a), 0.0, 0.16 + 0.05 * math.sin(a)))
         for a in np.linspace(-math.pi / 2, math.pi / 2, 9)]
    parts.append(P.tube("CupHandle", h, [0.022] * len(h), porcelain, ring_n=8))
    return parts


# ------------------------------------------------------------------- build

def build(out_dir):
    porcelain = L.make_material("Porcelain", L.solid_image("Porcelain_Color", "#fffaf3", out_dir),
                                roughness=0.45, specular=0.3)
    gold = L.make_material("Gold", L.solid_image("Gold_Color", "#e7bf6e", out_dir),
                           roughness=0.4, specular=0.5)
    ceramic = L.make_material("PastelCeramic", L.solid_image("PastelCeramic_Color", "#f6b8cb", out_dir),
                              roughness=0.45, specular=0.3)
    pastry = L.make_material("Pastries", palette_texture(out_dir), roughness=0.7, specular=0.2)
    tea = L.make_material("Tea", L.solid_image("Tea_Color", "#d88c3e", out_dir), roughness=0.3, specular=0.4)

    parts = build_stand(porcelain, gold)

    # Bottom tier: finger sandwiches, alternating fillings, points toward the pole.
    R, z = TIERS[0]
    top = z + 0.05
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.3
        s, (t1, t2) = sandwich(pastry)
        fill = "cucumber" if i % 2 == 0 else "salmon"
        paint(s, lambda c, n, t1=t1, t2=t2, fill=fill: fill if (t1 < c.z < t2 and abs(n.z) < 0.5)
              else "bread")
        s.rotation_euler = (0, 0, a + math.pi)
        s.location = (0.5 * math.cos(a), 0.5 * math.sin(a), top)
        parts.append(s)

    # Middle tier: scones with a jam dollop.
    R, z = TIERS[1]
    top = z + 0.05
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.5
        x, y = 0.3 * math.cos(a), 0.3 * math.sin(a)
        sc = scone(pastry)
        sc.location = (x, y, top)
        parts.append(sc)
        jam = P.cream_dollop("Jam", pastry, radius=0.075, height=0.07, ridges=6)
        paint_all(jam, "jam")
        jam.location = (x, y, top + 0.13)
        parts.append(jam)

    # Top tier: macarons in pastel colours.
    R, z = TIERS[2]
    top = z + 0.05
    colors = ["mac_pink", "mac_green", "mac_lav", "mac_yellow", "mac_pink"]
    for i, col in enumerate(colors):
        a = 2 * math.pi * i / 5
        group = macaron(pastry, col)
        P.move(group, dx=0.22 * math.cos(a), dy=0.22 * math.sin(a), dz=top,
               tilt=(math.radians(10 * math.sin(a)), math.radians(-12 * math.cos(a))))
        parts += group

    # Teapot to the left-back, teacup on saucer front-right.
    teapot = build_teapot(ceramic, gold)
    for t in teapot:
        t.scale = (1.15, 1.15, 1.15)
    parts += P.move(teapot, dx=-1.08, dy=0.25, rot_z=math.radians(-125))   # spout toward front-left
    parts += P.move(build_teacup(porcelain, ceramic, gold, tea), dx=0.95, dy=-0.4, rot_z=math.radians(200))
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.6, -1.0, 0.55), (0.1, -0.7, 1.0)),
                          bg="#f4eee6", ground="#efe6da", margin=0.8)
    sys.exit(0 if ok else 1)
