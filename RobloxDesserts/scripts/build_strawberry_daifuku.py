"""Strawberry Daifuku: soft powdered mochi with a strawberry peeking out the top."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402

NAME = "StrawberryDaifuku"
MOCHI_R = 0.55          # half-width of the mochi in studs
MOCHI_SQUASH = 0.74
BERRY_R = 0.28
OPEN_R = 0.30           # radius of the dimple the berry sits in
rng = np.random.default_rng(7)


def mochi_texture(out_dir):
    h = w = 256
    base = np.array(L.srgb("#f7cfd8"))
    top = np.array(L.srgb("#fbe3e8"))
    v = np.linspace(0, 1, h)[:, None, None]
    # Paler (powdered) towards the top, soft pink towards the base.
    rgb = base + (top - base) * np.clip((v - 0.25) / 0.5, 0, 1)
    rgb = np.broadcast_to(rgb, (h, w, 3)).copy()
    # Powder speckles: denser on the upper half.
    # Soft powder blotches (white, alpha-blended) concentrated on the top.
    yy, xx = np.mgrid[0:h, 0:w]
    powder = np.zeros((h, w))
    for _ in range(320):
        cy = rng.uniform(0.55, 1.0) ** 0.4 * (h - 1)
        cx = rng.uniform(0, w)
        rad = rng.uniform(2, 5)
        dx = np.minimum(np.abs(xx - cx), w - np.abs(xx - cx))  # wrap around seam
        powder = np.maximum(powder, np.clip(1 - np.hypot(dx, yy - cy) / rad, 0, 1) * rng.uniform(0.5, 1))
    powder += np.clip((yy / h - 0.8) / 0.08, 0, 1)  # solid dusting on the crown
    a = np.clip(powder * 1.6, 0, 0.95)[..., None]
    rgb = rgb * (1 - a) + np.array([1.0, 0.99, 0.98]) * a
    return L.image_from_array("Mochi_Color", rgb, out_dir)


def berry_texture(out_dir):
    h = w = 256
    red = np.array(L.srgb("#e8354f"))
    pale = np.array(L.srgb("#f47f8c"))
    v = np.linspace(0, 1, h)[:, None, None]
    rgb = red + (pale - red) * np.clip((v - 0.78) / 0.2, 0, 1)
    rgb = np.broadcast_to(rgb, (h, w, 3)).copy()
    seed = np.array(L.srgb("#ffe39a"))
    yy, xx = np.mgrid[0:h, 0:w]
    rows, cols = 4, 9
    for r in range(rows):
        vy = 0.46 + r * 0.1
        for c in range(cols):
            ux = (c + 0.5 * (r % 2)) / cols
            cy, cx = vy * h, ux * w
            dx = np.minimum(np.abs(xx - cx), w - np.abs(xx - cx))
            m = (dx / 2.6) ** 2 + ((yy - cy) / 4.2) ** 2 < 1  # small upright oval
            rgb[m] = seed
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
    n = 6
    for i in range(n):
        a = 2 * math.pi * i / n + 0.3
        bm = L.uvsphere_bm(u=8, v=5, radius=1.0)
        for vert in bm.verts:
            co = vert.co
            # Pointed leaf: taper the outer end.
            t = (co.x + 1) / 2
            co.y *= 1 - 0.75 * t ** 1.5
            co.z -= 0.9 * t ** 2  # droop the tip over the berry shoulder
        bmesh.ops.scale(bm, vec=(0.12, 0.085, 0.03), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0.1, 0, 0), verts=bm.verts)
        leaf = L.obj_from_bm("Leaf", bm, mat)
        leaf.location = (0, 0, z)
        leaf.rotation_euler = (0, math.radians(4), a)
        parts.append(leaf)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.028, radius2=0.02, depth=0.12)
    bmesh.ops.translate(bm, vec=(0, 0, 0.06), verts=bm.verts)
    stem = L.obj_from_bm("Stem", bm, mat)
    stem.location = (0, 0, z)
    stem.rotation_euler = (math.radians(12), 0, 0)
    parts.append(stem)
    return parts


def build(out_dir):
    mochi_mat = L.make_material("Mochi", mochi_texture(out_dir), roughness=0.9, specular=0.3)
    berry_mat = L.make_material("Strawberry", berry_texture(out_dir), roughness=0.35, specular=0.6)
    leaf_mat = L.make_material("Leaf", L.solid_image("Leaf_Color", "#79c26a", out_dir), roughness=0.7)

    mochi = build_mochi(mochi_mat)
    top = MOCHI_R * MOCHI_SQUASH - 0.14
    berry = build_berry(berry_mat, top + 0.06)
    berry_top = top + 0.06 + BERRY_R * 1.0 + (BERRY_R * 1.2 - BERRY_R * 1.0) * 0.6
    hull = build_hull(leaf_mat, berry_top - 0.015)
    return [mochi, berry, *hull]


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, bg="#f4eee6", ground="#efe6da")
    sys.exit(0 if ok else 1)
