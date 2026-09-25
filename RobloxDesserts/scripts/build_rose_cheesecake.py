"""Rose Cheesecake (premium, romantic): a cheesecake slice with a golden biscuit
base, cream body and a pale blush glaze that drips down the back, crowned
with a large sculpted rose, sage leaves, pearls and a gold flake, on a white
plate with a gold rim."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import premium_parts as Q  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "RoseCheesecake"
R, ANGLE = 1.0, 50
TOP = 0.7
CRUST, GLAZE = 0.08, 0.63          # crust top / glaze start (z)
PLATE_TOP = 0.06
HALF = math.radians(ANGLE) / 2


def cake_texture(out_dir):
    """u = angle across the back arc (0..1 between the cut faces), v = z / TOP."""
    w = h = 512
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    crust = np.array(L.srgb("#e2ae6c"))
    body = np.array(L.srgb("#fff3e0"))
    glaze = np.array(L.srgb("#f8c2d0"))
    rgb = np.where((V < CRUST / TOP)[..., None], crust, body)
    g0 = GLAZE / TOP
    # Drips on the back arc only (u well inside 0..1, away from the cut faces).
    drip = np.zeros_like(U)
    for uc, depth in ((0.18, 0.2), (0.34, 0.12), (0.52, 0.26), (0.7, 0.14), (0.84, 0.21)):
        du = np.abs(U - uc)
        body_ = (du < 0.035) & (V > g0 - depth)
        tip = np.hypot(du / 0.035, (V - (g0 - depth)) / 0.05) < 1
        drip = np.maximum(drip, body_ | tip)
    edge = np.clip(np.minimum(U, 1 - U) / 0.06, 0, 1)     # no drips on the cut faces
    glazed = (V > g0) | ((drip > 0) & (edge >= 1))
    rgb[glazed] = glaze
    rgb[np.abs(V - CRUST / TOP) < 0.006] = L.srgb("#c98f4f")   # crisp crust line
    return L.image_from_array("Cheesecake_Color", rgb, out_dir)


def build_slice(mat):
    outline = P.wedge_outline(R, ANGLE, tip=0.12, arc_steps=16)
    rings = [(0.0, 0.025), (0.025, 0.0), (CRUST, 0.0), (0.3, 0.0), (GLAZE - 0.03, 0.0),
             (GLAZE, -0.012), (TOP - 0.03, -0.012), (TOP - 0.008, -0.004), (TOP, 0.02)]

    def uv_fn(co):
        a = math.atan2(co.y, co.x)
        u = min(max((a + HALF) / (2 * HALF), 0.0), 1.0)
        if math.hypot(co.x, co.y) < R * 0.9:              # cut faces / top: no drips
            u = 0.0 if a < 0 else 1.0
        return (u, min(max(co.z / TOP, 0.0), 0.995))      # stay below v=1 (texture wraps)

    return P.loft("Cheesecake", outline, rings, [mat], lambda c, k: 0, uv_fn=uv_fn)


def petal(mat, w, h, cup=0.5):
    bm = L.uvsphere_bm(u=12, v=8, radius=1.0)
    for v in bm.verts:
        co = v.co
        co.z = (co.z + 1) / 2                             # 0..1 base to tip
        co.x *= 0.5 * (0.55 + 0.9 * math.sin(math.pi * min(co.z, 1.0) * 0.85))   # wider near the top
        co.y *= 0.14
        co.y -= cup * co.x ** 2                           # edges curl toward the rose centre
        co.y += 0.12 * co.z ** 2                          # lip rolls outward
    bmesh.ops.scale(bm, vec=(w, w, h), verts=bm.verts)
    return L.obj_from_bm("Petal", bm, mat)


def build_rose(mat, leaf_mat):
    parts = []
    bud = L.obj_from_bm("Bud", L.uvsphere_bm(u=14, v=10, radius=0.06), mat)
    bud.scale = (1, 1, 1.5)
    bud.location = (0, 0, 0.1)
    parts.append(bud)
    # (count, ring radius, width, height, outward lean deg, base z)
    rings = [(3, 0.035, 0.1, 0.17, 12, 0.02), (5, 0.08, 0.14, 0.17, 32, 0.01), (6, 0.13, 0.17, 0.15, 58, 0.0)]
    for k, (n, rr, w, h, lean, z0) in enumerate(rings):
        for i in range(n):
            a = 2 * math.pi * i / n + k * 0.6
            p = petal(mat, w, h, cup=0.6 if k < 2 else 0.35)
            p.matrix_world = (Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((0, rr, z0))
                              @ Matrix.Rotation(-math.radians(lean), 4, "X"))
            parts.append(p)
    for a in (math.radians(-35), math.radians(-150)):
        lb = L.uvsphere_bm(u=10, v=6, radius=1.0)
        for v in lb.verts:
            t = (v.co.x + 1) / 2
            v.co.y *= 1 - 0.8 * t ** 1.4
            v.co.z -= 0.35 * t ** 2
        bmesh.ops.scale(lb, vec=(0.12, 0.07, 0.02), verts=lb.verts)
        bmesh.ops.translate(lb, vec=(0.2, 0, 0.03), verts=lb.verts)
        leaf = L.obj_from_bm("Leaf", lb, leaf_mat)
        leaf.rotation_euler = (0, 0, a)
        parts.append(leaf)
    return parts


def build(out_dir):
    cake = L.make_material("Cheesecake", cake_texture(out_dir), roughness=0.55, specular=0.3)
    rose = L.make_material("Rose", L.solid_image("Rose_Color", "#f4859f", out_dir), roughness=0.5, specular=0.3)
    leaf = L.make_material("Leaf", L.solid_image("Leaf_Color", "#8fc48d", out_dir), roughness=0.6, specular=0.25)
    pearl = L.make_material("Pearl", Q.pearl_texture(out_dir), roughness=0.3, specular=0.5)
    gold = L.make_material("Gold", L.solid_image("Gold_Color", Q.GOLD, out_dir), roughness=0.45, specular=0.4)
    plate = L.make_material("Plate", L.solid_image("Plate_Color", "#fffaf4", out_dir), roughness=0.4, specular=0.35)

    PR = 0.86
    prof = [(0.0, 0.0), (PR * 0.55, 0.0), (PR * 0.6, 0.02), (PR * 0.9, 0.035), (PR, 0.09), (PR - 0.03, 0.105),
            (PR * 0.88, 0.07), (PR * 0.6, PLATE_TOP), (0.0, PLATE_TOP)]
    parts = [Q.lathe_multi("Plate", prof, [plate, gold],
                           lambda c: 1 if math.hypot(c.x, c.y) > PR * 0.95 else 0, segments=56)]

    sl = build_slice(cake)
    parts.append(sl)
    rose_parts = build_rose(rose, leaf)
    for o in rose_parts:                                  # large, hero-sized rose
        o.scale = tuple(c * 1.4 for c in o.scale)
        o.location = o.location * 1.4
    P.move(rose_parts, dx=0.64, dz=TOP - 0.025)
    parts += rose_parts
    # Graduated pearls leading from the rose toward the tip, with a gold flake.
    for x, r in ((0.38, 0.05), (0.27, 0.04), (0.18, 0.032)):
        b = Q.pearl("Pearl", pearl, r=r)
        b.location = (x, 0.0, TOP + r * 0.8)
        parts.append(b)
    f = Q.gold_flake("GoldFlake", gold, size=0.07, seed=3)
    f.location = (0.44, -0.16, TOP - 0.004)
    parts.append(f)
    # Slice sits centred on the plate.
    P.move(parts[1:], dx=-0.48, dz=PLATE_TOP - 0.005)
    # Two loose petals resting on the plate (romantic touch).
    for x, y, a in ((-0.5, -0.42, 0.4), (-0.22, -0.6, 2.1)):
        lp = petal(rose, 0.17, 0.15, cup=0.3)
        lp.rotation_euler = (math.radians(95), 0, a)
        lp.location = (x, y, PLATE_TOP + 0.02)
        parts.append(lp)
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((-0.7, -1.0, 0.75), (1.0, -0.55, 0.9)),
                          bg="#f4eee6", ground="#efe6da", margin=0.95)
    sys.exit(0 if ok else 1)
