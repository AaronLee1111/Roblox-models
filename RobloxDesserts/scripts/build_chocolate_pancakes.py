"""Chocolate Pancakes: Soufflé Pancakes base in cocoa, with dark chocolate
sauce, whipped cream, a chocolate wafer, chocolate chips and blueberries, on a
lilac plate. The richest, darkest of the pancake family."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import premium_parts as Q  # noqa: E402
import pancake_family as F  # noqa: E402
import bmesh  # noqa: E402

NAME = "ChocolatePancakes"


def choc_chip(mat, r=0.035):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r * 0.15, depth=r * 1.3)
    bmesh.ops.translate(bm, vec=(0, 0, r * 0.65), verts=bm.verts)
    return L.obj_from_bm("ChocChip", bm, mat)


def wafer(mat):
    """Chunky rounded chocolate wafer square, stuck upright in the cream."""
    s = 0.15
    outline = P.chaikin([(-s, -s), (s, -s), (s, s), (-s, s)], 2)
    w = Q.rounded_extrude("Wafer", outline, 0.035, mat, round_frac=0.4, steps=1)
    w.rotation_euler = (math.radians(72), 0, math.radians(40))
    return w


def build(out_dir):
    parts, place = F.base(out_dir, "#a0673f", "#dcb58e", "#3f1d10", "#d9ccf4")
    cream = F.cream_mat(out_dir)
    dark = L.make_material("DarkChocolate", L.solid_image("DarkChocolate_Color", "#3e1f12", out_dir),
                           roughness=0.4, specular=0.35)
    blue = L.make_material("Blueberry", L.solid_image("Blueberry_Color", "#5d6fd8", out_dir),
                           roughness=0.45, specular=0.3)

    top = []
    d = P.cream_dollop("Cream", cream, radius=0.19, height=0.27)
    d.location = (0.04, 0.02, F.PH + 0.02)
    top.append(d)
    wf = wafer(dark)
    wf.location = (-0.2, -0.08, F.PH + 0.16)
    top.append(wf)
    for k, a in enumerate((0.3, 1.5, 2.6, 3.8, 5.0)):
        c = choc_chip(dark)
        c.location = (0.27 * math.cos(a), 0.27 * math.sin(a), F.PH + 0.015)
        top.append(c)
    for k, a in enumerate((-2.2, 0.3)):                 # either side of the cream
        b = L.obj_from_bm("Blueberry", L.uvsphere_bm(u=14, v=8, radius=0.065), blue)
        b.location = (0.26 * math.cos(a), 0.26 * math.sin(a), F.PH + 0.06)
        top.append(b)
    parts += place(top)
    # Chips and berries scattered on the plate.
    for x, y in ((0.52, -0.3), (-0.45, -0.45), (0.58, 0.18), (-0.55, 0.2)):
        c = choc_chip(dark, r=0.06)
        c.location = (x, y, 0.065)
        parts.append(c)
    b = L.obj_from_bm("Blueberry", L.uvsphere_bm(u=14, v=8, radius=0.065), blue)
    b.location = (0.45, -0.48, 0.12)
    parts.append(b)
    return parts


if __name__ == "__main__":
    sys.exit(0 if F.render(NAME, build) else 1)
