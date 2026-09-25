"""Strawberry Daifuku: chunky pink mochi with a big strawberry peeking out the top.

Stylized Roblox pass: exaggerated berry/leaves, flat colours, bold readable detail."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402

NAME = "StrawberryDaifuku"
MOCHI_R = 0.55          # half-width of the mochi in studs
MOCHI_SQUASH = 0.8
BERRY_R = 0.34
OPEN_R = 0.34           # radius of the dimple the berry sits in


def mochi_texture(out_dir):
    """Flat pastel-pink mochi with a bold powder cap (wavy edge) on the crown."""
    h = w = 256
    pink = np.array(L.srgb("#f9b3c6"))
    powder = np.array(L.srgb("#fff2f5"))
    yy, xx = np.mgrid[0:h, 0:w]
    edge = 0.74 + 0.03 * np.sin(xx / w * 2 * np.pi * 7)   # scalloped powder line
    cap = np.clip((yy / h - edge) * h / 1.5 + 0.5, 0, 1)[..., None]  # anti-aliased edge
    rgb = pink + (powder - pink) * cap
    return L.image_from_array("Mochi_Color", rgb, out_dir)


def berry_texture(out_dir):
    """Flat saturated red with a few big, readable seeds."""
    h = w = 256
    rgb = np.broadcast_to(np.array(L.srgb("#f0385a")), (h, w, 3)).copy()
    seed = np.array(L.srgb("#fff0a3"))
    yy, xx = np.mgrid[0:h, 0:w]
    rows, cols = 3, 7
    for r in range(rows):
        vy = 0.5 + r * 0.13
        for c in range(cols):
            ux = (c + 0.5 * (r % 2)) / cols
            cy, cx = vy * h, ux * w
            dx = np.minimum(np.abs(xx - cx), w - np.abs(xx - cx))
            rgb[(dx / 4.5) ** 2 + ((yy - cy) / 6.5) ** 2 < 1] = seed
    return L.image_from_array("Strawberry_Color", rgb, out_dir)


def build_mochi(mat):
    bm = L.uvsphere_bm(u=32, v=16, radius=MOCHI_R)
    for vert in bm.verts:
        co = vert.co
        co.z *= MOCHI_SQUASH
        # Soft flat base.
        floor = -MOCHI_R * MOCHI_SQUASH * 0.62
        if co.z < floor:
            co.z = floor + (co.z - floor) * 0.15
        # Dimple at the top where the strawberry nestles.
        r = math.hypot(co.x, co.y)
        if r < OPEN_R * 1.4 and co.z > 0:
            k = min(1.0, r / (OPEN_R * 1.4))
            co.z -= 0.14 * (1 - k ** 2) ** 2  # smooth, rounded rim
    return L.obj_from_bm("Mochi", bm, mat)


def build_berry(mat, top_z):
    bm = L.uvsphere_bm(u=18, v=12, radius=BERRY_R)
    for vert in bm.verts:
        co = vert.co
        t = min(1.0, max(0.0, (co.z / BERRY_R + 1) / 2))  # 0 = tip (down), 1 = top
        radial = 0.35 + 0.65 * t ** 0.45
        co.x *= radial
        co.y *= radial
        co.z *= 1.2
        cap = BERRY_R * 1.0
        if co.z > cap:
            co.z = cap + (co.z - cap) * 0.6
    obj = L.obj_from_bm("Strawberry", bm, mat)
    obj.location.z = top_z
    return obj


def build_hull(mat, z):
    parts = []
    n = 5
    for i in range(n):
        a = 2 * math.pi * i / n + 0.3
        bm = L.uvsphere_bm(u=12, v=7, radius=1.0)
        for vert in bm.verts:
            co = vert.co
            # Pointed leaf: taper the outer end.
            t = (co.x + 1) / 2
            co.y *= 1 - 0.75 * t ** 1.5
            co.z -= 0.9 * t ** 2  # droop the tip over the berry shoulder
        bmesh.ops.scale(bm, vec=(0.15, 0.11, 0.05), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0.12, 0, 0), verts=bm.verts)
        leaf = L.obj_from_bm("Leaf", bm, mat)
        leaf.location = (0, 0, z)
        leaf.rotation_euler = (0, math.radians(4), a)
        parts.append(leaf)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.045, radius2=0.035, depth=0.14)
    bmesh.ops.translate(bm, vec=(0, 0, 0.07), verts=bm.verts)
    stem = L.obj_from_bm("Stem", bm, mat)
    stem.location = (0, 0, z)
    stem.rotation_euler = (math.radians(12), 0, 0)
    parts.append(stem)
    return parts


def build(out_dir):
    mochi_mat = L.make_material("Mochi", mochi_texture(out_dir), roughness=0.75, specular=0.25)
    berry_mat = L.make_material("Strawberry", berry_texture(out_dir), roughness=0.55, specular=0.3)
    leaf_mat = L.make_material("Leaf", L.solid_image("Leaf_Color", "#5ccb5f", out_dir),
                              roughness=0.75, specular=0.25)

    mochi = build_mochi(mochi_mat)
    top = MOCHI_R * MOCHI_SQUASH - 0.14
    berry = build_berry(berry_mat, top + 0.03)
    berry_top = top + 0.03 + BERRY_R * 1.0 + (BERRY_R * 1.2 - BERRY_R * 1.0) * 0.6
    hull = build_hull(leaf_mat, berry_top - 0.015)
    return [mochi, berry, *hull]


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, bg="#f4eee6", ground="#efe6da")
    sys.exit(0 if ok else 1)
