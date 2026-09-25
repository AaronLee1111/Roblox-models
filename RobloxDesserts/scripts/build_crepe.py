"""Crepe (Harajuku style): ruffled crepe cone overflowing with whipped cream,
strawberry halves (cut side out) and a whole berry, wrapped in a striped
pastel paper sleeve and set in a little café crepe stand."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import crepe_family as C  # noqa: E402
import numpy as np  # noqa: E402

NAME = "Crepe"
CONE_H, R_TOP = 0.85, 0.34
LIFT = 0.18                     # cone apex sits inside the stand


def sleeve_texture(out_dir):
    n = 128
    U = (np.arange(n) + 0.5) / n
    stripe = ((U * 12) % 1.0) < 0.5
    rgb = np.where(stripe[None, :, None], np.array(L.srgb("#ffb3c8")), np.array(L.srgb("#fff4f7")))
    return L.image_from_array("Sleeve_Color", np.broadcast_to(rgb, (n, n, 3)).copy(), out_dir)


def build(out_dir):
    crepe = C.crepe_mat(out_dir)
    sleeve = L.make_material("Sleeve", sleeve_texture(out_dir), roughness=0.6, specular=0.2)
    stand = L.make_material("Stand", L.solid_image("Stand_Color", "#c9e6f5", out_dir), roughness=0.5, specular=0.3)
    cream = L.make_material("Cream", L.solid_image("Cream_Color", "#fff8ef", out_dir), roughness=0.7, specular=0.25)
    skin = L.make_material("Strawberry", P.strawberry_texture(out_dir), roughness=0.55, specular=0.3)
    cut = L.make_material("StrawberryCut", P.cut_texture(out_dir), roughness=0.55, specular=0.25)
    leaf = L.make_material("Leaf", L.solid_image("Leaf_Color", "#5ccb5f", out_dir), roughness=0.75, specular=0.25)

    parts = [P.lathe("Stand", [(0.0, 0.0), (0.34, 0.0), (0.36, 0.03), (0.3, 0.06), (0.1, 0.1), (0.07, 0.16),
                               (0.14, 0.2), (0.16, 0.26), (0.13, 0.26), (0.0, 0.2)], stand, segments=32)]
    cone = C.crepe_cone(crepe, r_top=R_TOP, h=CONE_H)
    cone.location.z = LIFT
    parts.append(cone)
    # Paper sleeve: a slightly larger cone band over the lower half.
    sl = []
    for t in np.linspace(0.15, 0.62, 6):
        sl.append((0.05 + (R_TOP - 0.05) * t ** 0.9 + 0.02, CONE_H * t))
    prof = [(0.0, CONE_H * 0.15)] + sl + [(sl[-1][0] - 0.02, sl[-1][1])]
    sleeve_obj = P.lathe("Sleeve", prof, sleeve, segments=36)
    me = sleeve_obj.data
    uv = me.uv_layers.active.data
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        uv[loop.index].uv = ((math.atan2(co.y, co.x) / (2 * math.pi)) % 1.0, 0.5)
    sleeve_obj.location.z = LIFT
    parts.append(sleeve_obj)

    top = LIFT + CONE_H
    for k, (x, y, r, hgt) in enumerate(((0.0, 0.0, 0.24, 0.36), (-0.12, 0.1, 0.13, 0.22), (0.11, 0.12, 0.12, 0.2))):
        d = P.cream_dollop("Cream", cream, radius=r, height=hgt)
        d.location = (x, y, top - 0.1)
        d.rotation_euler = (0, 0, k)
        parts.append(d)
    for k, a in enumerate((-1.9, -0.9, 0.2, 2.4)):          # halves standing in the cream, cut side out
        h = P.strawberry_half(skin, cut, 0.12)
        h.rotation_euler = (math.radians(-10), 0, a - math.pi / 2)
        h.location = (0.21 * math.cos(a), 0.21 * math.sin(a), top + 0.07)
        parts.append(h)
    berry = P.strawberry(skin, leaf, radius=0.12)
    P.move(berry, dx=0.02, dz=top + 0.2, tilt=(math.radians(8), 0.0))
    parts += berry
    return parts


if __name__ == "__main__":
    sys.exit(0 if C.render(NAME, build, views=((0.8, -1.0, 0.45), (0.2, -0.5, 1.3))) else 1)
