"""Hanami Dango: pink, white and green mochi balls on a wooden skewer."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402

NAME = "Dango"
BALL_R = 0.3
SPACING = 0.5            # centre-to-centre, slightly less than a diameter so balls press together
SKEWER_R = 0.06
BALLS = [("Dango_Pink", "#f497b3"), ("Dango_White", "#fbf4ea"), ("Dango_Green", "#9ccf7e")]


def gradient_texture(name, hex_color, out_dir):
    """Soft top-to-bottom shading baked into the colour so it reads in flat Roblox lighting."""
    h, w = 64, 16
    c = np.array(L.srgb(hex_color))
    v = np.linspace(0, 1, h)[:, None, None]
    rgb = c * (0.9 + 0.1 * v) + (1 - c) * 0.08 * v
    return L.image_from_array(name, np.broadcast_to(rgb, (h, w, 3)).copy(), out_dir)


def build_ball(mat, x, seed):
    rng = np.random.default_rng(seed)
    bm = L.uvsphere_bm(u=24, v=14, radius=BALL_R)
    wob = rng.uniform(-1, 1, 3)
    for vert in bm.verts:
        co = vert.co
        co.x *= 0.9                     # pressed against neighbours
        # Gentle hand-rolled irregularity (low frequency so the silhouette stays clean).
        n = co.normalized()
        co += n * BALL_R * 0.06 * (wob[0] * n.x * n.y + wob[1] * n.z * n.x + wob[2] * (n.z ** 2 - 0.3))
        # Soft sag: flatter bottom, sitting on the table.
        co.z *= 0.94
        if co.z < -BALL_R * 0.62:
            co.z = -BALL_R * 0.62 + (co.z + BALL_R * 0.62) * 0.25
            co.x *= 1.03
            co.y *= 1.03
    # Rotate UV-sphere poles along the skewer axis would put seams on show; keep poles up/down.
    obj = L.obj_from_bm(mat.name, bm, mat)
    obj.location = (x, 0, 0)
    return obj


def build_skewer(mat, x0, x1):
    bm = bmesh.new()
    length = x1 - x0
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=SKEWER_R, radius2=SKEWER_R,
                          depth=length)
    # Sharpen the far end into a point.
    tip = [v for v in bm.verts if v.co.z > 0]
    bmesh.ops.scale(bm, vec=(0.35, 0.35, 1), verts=tip)
    bmesh.ops.translate(bm, vec=(0, 0, 0.06), verts=tip)
    obj = L.obj_from_bm("Skewer", bm, mat)
    obj.rotation_euler = (0, math.radians(90), 0)
    obj.location = ((x0 + x1) / 2, 0, 0)
    return obj


def build(out_dir):
    parts = []
    xs = [(i - 1) * SPACING for i in range(3)]
    for i, ((name, color), x) in enumerate(zip(BALLS, xs)):
        mat = L.make_material(name, gradient_texture(f"{name}_Color", color, out_dir),
                              roughness=0.28, specular=0.6, clearcoat=0.35)
        parts.append(build_ball(mat, x, seed=i + 3))
    wood = L.make_material("Skewer_Wood", L.solid_image("Skewer_Color", "#d8b384", out_dir), roughness=0.8)
    parts.append(build_skewer(wood, xs[0] - 0.85, xs[-1] + 0.42))
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.35, -1.0, 0.55), (1.0, -0.4, 1.1)),
                          bg="#f4eee6", ground="#efe6da", margin=1.0)
    sys.exit(0 if ok else 1)
