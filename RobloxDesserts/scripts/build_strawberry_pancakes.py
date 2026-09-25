"""Strawberry Pancakes: Soufflé Pancakes base with bright strawberry sauce,
whipped cream, strawberry halves around the top and a whole berry, on a pink plate."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import pancake_family as F  # noqa: E402
import premium_parts as Q  # noqa: E402

NAME = "StrawberryPancakes"


def build(out_dir):
    parts, place = F.base(out_dir, "#e8a24e", "#fff0c9", "#f0426a", "#ffe3ea")
    cream = F.cream_mat(out_dir)
    skin = L.make_material("Strawberry", P.strawberry_texture(out_dir), roughness=0.55, specular=0.3)
    cut = L.make_material("StrawberryCut", P.cut_texture(out_dir), roughness=0.55, specular=0.25)
    leaf = L.make_material("Leaf", L.solid_image("Leaf_Color", "#5ccb5f", out_dir), roughness=0.75, specular=0.25)

    top = []
    d = P.cream_dollop("Cream", cream, radius=0.2, height=0.28)
    d.location = (0, 0, F.PH + 0.02)
    top.append(d)
    for i in range(5):                       # ring of halves, cut side out, around the cream
        a = 2 * math.pi * i / 5 + 0.3
        h = P.strawberry_half(skin, cut, 0.11)
        h.rotation_euler = (math.radians(-20), 0, a - math.pi / 2)
        h.location = (0.27 * math.cos(a), 0.27 * math.sin(a), F.PH + 0.03)
        top.append(h)
    berry = P.strawberry(skin, leaf, radius=0.13)
    P.move(berry, dz=F.PH + 0.24)
    top += berry
    parts += place(top)
    # Two halves on the plate for a fruity, generous presentation.
    for x, y, a in ((0.5, -0.36, 0.2), (-0.48, -0.38, 2.4)):
        h = P.strawberry_half(skin, cut, 0.12)
        h.rotation_euler = (math.radians(55), 0, a)       # cut face tipped up, skin still shows
        h.location = (x, y, 0.0)
        Q.place_on(h, 0.065)
        parts.append(h)
    return parts


if __name__ == "__main__":
    sys.exit(0 if F.render(NAME, build) else 1)
