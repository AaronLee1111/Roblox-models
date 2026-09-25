"""Hanami Dango: pink, white and green mochi balls on a wooden skewer.

Stylized Roblox pass: chunkier balls and skewer, flat saturated pastels."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402

NAME = "Dango"
BALL_R = 0.34
SPACING = 0.56           # centre-to-centre, slightly less than a diameter so balls press together
SKEWER_R = 0.08
BALLS = [("Dango_Pink", "#ff9cbd"), ("Dango_White", "#fff5e6"), ("Dango_Green", "#8fd38a")]




def build_ball(mat, x, seed):
    rng = np.random.default_rng(seed)
    bm = L.uvsphere_bm(u=24, v=14, radius=BALL_R)
    wob = rng.uniform(-1, 1, 3)
    for vert in bm.verts:
        co = vert.co
        co.x *= 0.88                    # pressed against neighbours
        # Gentle hand-rolled irregularity (low frequency so the silhouette stays clean).
        n = co.normalized()
        co += n * BALL_R * 0.03 * (wob[0] * n.x * n.y + wob[1] * n.z * n.x + wob[2] * (n.z ** 2 - 0.3))
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
    bmesh.ops.scale(bm, vec=(0.5, 0.5, 1), verts=tip)
    bmesh.ops.translate(bm, vec=(0, 0, 0.05), verts=tip)
    obj = L.obj_from_bm("Skewer", bm, mat)
    obj.rotation_euler = (0, math.radians(90), 0)
    obj.location = ((x0 + x1) / 2, 0, 0)
    return obj


def build(out_dir):
    parts = []
    xs = [(i - 1) * SPACING for i in range(3)]
    for i, ((name, color), x) in enumerate(zip(BALLS, xs)):
        mat = L.make_material(name, L.solid_image(f"{name}_Color", color, out_dir),
                              roughness=0.45, specular=0.3)
        parts.append(build_ball(mat, x, seed=i + 3))
    wood = L.make_material("Skewer_Wood", L.solid_image("Skewer_Color", "#e0ae72", out_dir),
                          roughness=0.8, specular=0.2)
    parts.append(build_skewer(wood, xs[0] - 0.8, xs[-1] + 0.45))
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.35, -1.0, 0.55), (1.0, -0.4, 1.1)),
                          bg="#f4eee6", ground="#efe6da", margin=1.0)
    sys.exit(0 if ok else 1)
