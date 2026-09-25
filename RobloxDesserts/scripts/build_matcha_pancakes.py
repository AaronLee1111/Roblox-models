"""Matcha Pancakes: Soufflé Pancakes base in matcha green, with a condensed-milk
glaze, matcha-dusted cream, a quenelle of red bean paste and white mochi balls,
on a cream plate. Japanese-café counterpart to the strawberry version."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import premium_parts as Q  # noqa: E402
import pancake_family as F  # noqa: E402
import build_matcha_crepe_cake as C  # noqa: E402  (reuse its matcha-dusted cream texture)

NAME = "MatchaPancakes"


def red_bean(mat):
    """Anko quenelle: smooth oval scoop studded with a few whole beans."""
    parts = []
    bm = L.uvsphere_bm(u=18, v=10, radius=1.0)
    for v in bm.verts:
        v.co.x *= 0.15
        v.co.y *= 0.1
        v.co.z *= 0.075
    parts.append(L.obj_from_bm("RedBean", bm, mat))
    for k, (x, y) in enumerate(((0.07, 0.05), (-0.05, 0.06), (0.0, -0.05), (-0.09, -0.02), (0.1, -0.03))):
        b = L.uvsphere_bm(u=8, v=6, radius=0.028)
        for v in b.verts:
            v.co.x *= 1.35
        bean = L.obj_from_bm("Bean", b, mat)
        bean.location = (x, y, 0.055 - 0.02 * abs(x) / 0.1)
        bean.rotation_euler = (0, 0, k)
        parts.append(bean)
    return parts


def build(out_dir):
    parts, place = F.base(out_dir, "#7fa653", "#e2edc8", "#fff6df", "#fff3dd")   # condensed-milk glaze
    cream = L.make_material("Cream", C.dusted_cream_texture(out_dir), roughness=0.7, specular=0.25)
    bean_mat = L.make_material("RedBean", L.solid_image("RedBean_Color", "#7a3342", out_dir),
                               roughness=0.5, specular=0.3)
    mochi = L.make_material("Shiratama", Q.shine_texture("Shiratama_Color", "#fffaf2", out_dir,
                                                         shade_hex="#efe4d4", size=128),
                            roughness=0.4, specular=0.35)

    top = []
    d = P.cream_dollop("Cream", cream, radius=0.19, height=0.27)
    d.location = (0.03, 0.1, F.PH + 0.02)
    top.append(d)
    rb = red_bean(bean_mat)
    P.move(rb, dx=-0.17, dy=-0.06, dz=F.PH + 0.05, rot_z=0.9)
    top += rb
    for k, a in enumerate((-1.25, -0.55, 0.15)):   # front-right, facing the viewer
        m = Q.mochi("Shiratama", mochi, r=0.075, squash=0.85, u=14, v=8)
        m.location = (0.25 * math.cos(a), 0.25 * math.sin(a), F.PH + 0.02)
        top.append(m)
    parts += place(top)
    return parts


if __name__ == "__main__":
    sys.exit(0 if F.render(NAME, build) else 1)
