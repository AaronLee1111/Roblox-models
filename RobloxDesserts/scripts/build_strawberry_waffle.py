"""Strawberry Waffle: the Belgian waffle base with strawberry sauce drizzled
over the top and pooled in pockets, whipped cream, a ring of strawberry halves
(cut side up) and a whole berry, on the strawberry family's blush plate."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import premium_parts as Q  # noqa: E402
import waffle_family as F  # noqa: E402

NAME = "StrawberryWaffle"
SAUCE = "#e8355a"
DRIZZLE = [(-0.85, 0.55), (-0.55, -0.7), (-0.25, 0.7), (0.05, -0.75), (0.35, 0.7), (0.65, -0.7), (0.85, 0.5)]
POCKETS = {(1, 1), (2, 1), (1, 2), (2, 2)}          # interior only (edge pockets are flattened)


def build(out_dir):
    parts, top_at = F.base(out_dir, "#ffe3ea", fill=lambda i, j: SAUCE if (i, j) in POCKETS else None,
                           sugar_dots=0, drizzle=(SAUCE, 0.03, DRIZZLE))
    cream = F.cream_mat(out_dir)
    skin = L.make_material("Strawberry", P.strawberry_texture(out_dir), roughness=0.55, specular=0.3)
    cut = L.make_material("StrawberryCut", P.cut_texture(out_dir), roughness=0.55, specular=0.25)
    leaf = L.make_material("Leaf", L.solid_image("Leaf_Color", "#5ccb5f", out_dir), roughness=0.75, specular=0.25)

    c = top_at(0.0, 0.0)
    d = P.cream_dollop("Cream", cream, radius=0.22, height=0.3)
    d.location = (c.x, c.y, c.z - 0.03)
    parts.append(d)
    berry = P.strawberry(skin, leaf, radius=0.14)
    P.move(berry, dx=c.x, dy=c.y, dz=c.z + 0.2)
    parts += berry
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.6
        p = top_at(0.6 * math.cos(a), 0.6 * math.sin(a))
        h = P.strawberry_half(skin, cut, 0.12)
        h.rotation_euler = (math.radians(82), 0, a + 0.35 + math.pi / 2)   # lying down, cut face up
        h.location = (p.x, p.y, 0.0)
        Q.place_on(h, p.z - 0.05)
        parts.append(h)
    return parts


if __name__ == "__main__":
    sys.exit(0 if F.render(NAME, build) else 1)
