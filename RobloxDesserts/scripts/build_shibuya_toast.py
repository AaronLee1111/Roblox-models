"""Shibuya Toast: the toast family's bread as a tall brick loaf, its top
crowned with golden toast cubes, a vanilla ice-cream scoop (bingsu scoop),
whipped cream, strawberries, mint and a caramel glaze dripping down the sides."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import premium_parts as Q  # noqa: E402
import toast_family as T  # noqa: E402
import bingsu_common as B  # noqa: E402
import numpy as np  # noqa: E402
import bmesh  # noqa: E402

NAME = "ShibuyaToast"
W, H = 0.8, 0.56


def toast_cube(face, crust, s=0.17):
    c = T.bread("ToastCube", T.rounded_rect(s, s, s * 0.28, steps=3), s, face, crust, round_frac=0.28, steps=2)
    return c


def build(out_dir):
    top_face = L.make_material("ToastTop", L.solid_image("ToastTop_Color", "#f8dca2", out_dir), roughness=0.6,
                               specular=0.25)
    cube_face = L.make_material("CubeCrumb", L.solid_image("CubeCrumb_Color", "#f6c56a", out_dir),
                                roughness=0.65, specular=0.25)
    crust = T.crust_mat(out_dir, "#dc9a48")
    cream = L.make_material("Cream", L.solid_image("Cream_Color", "#fff8ef", out_dir), roughness=0.7, specular=0.25)
    vanilla = L.make_material("Vanilla", L.solid_image("Vanilla_Color", "#fff1c9", out_dir), roughness=0.7,
                              specular=0.2)
    skin = L.make_material("Strawberry", P.strawberry_texture(out_dir), roughness=0.55, specular=0.3)
    cut = L.make_material("StrawberryCut", P.cut_texture(out_dir), roughness=0.55, specular=0.25)
    leaf = L.make_material("Mint", L.solid_image("Mint_Color", "#4fc463", out_dir), roughness=0.7, specular=0.25)

    parts = [T.plate(out_dir, "#c9d7f7")]
    loaf = T.bread("Loaf", T.rounded_rect(W, W, 0.14), H, top_face, crust, round_frac=0.15, steps=2)
    loaf.location.z = T.PLATE_TOP - 0.005
    parts.append(loaf)
    top = T.PLATE_TOP + H - 0.01

    cubes = [(-0.2, -0.2, 0.3), (0.2, -0.22, -0.2), (-0.22, 0.18, 0.1), (0.22, 0.2, 0.4), (0.0, -0.3, 0.9)]
    for x, y, r in cubes:
        c = toast_cube(cube_face, crust)
        c.location = (x, y, top - 0.01)
        c.rotation_euler = (0.1 * math.sin(r * 5), 0.1 * math.cos(r * 5), r)
        parts.append(c)
    sc = B.scoop(vanilla, radius=0.2)
    sc.location = (0.0, 0.03, top + 0.2)
    parts.append(sc)
    d = P.cream_dollop("Cream", cream, radius=0.15, height=0.2)
    d.location = (0.24, -0.02, top + 0.14)
    parts.append(d)
    for k, a in enumerate((-2.0, 2.5)):
        h = P.strawberry_half(skin, cut, 0.13)
        h.rotation_euler = (math.radians(20), 0, a)
        h.location = (0.26 * math.cos(a), 0.26 * math.sin(a), top + 0.18)
        parts.append(h)
    berry = P.strawberry(skin, leaf, radius=0.11)
    P.move(berry, dx=0.02, dy=0.0, dz=top + 0.36)
    parts += berry
    m = B.mint_leaf(leaf, size=0.13)
    m.location = (-0.06, -0.06, top + 0.33)
    m.rotation_euler = (0, math.radians(-30), 3.9)
    parts.append(m)
    # Caramel dripping from the top edge down the two front faces.
    caramel = L.make_material("Caramel", L.solid_image("Caramel_Color", "#b8661f", out_dir), roughness=0.3,
                              specular=0.45)
    for face_axis, sign in (("y", -1), ("x", 1)):
        for k, (t, length) in enumerate(((-0.25, 0.16), (0.02, 0.26), (0.26, 0.12))):
            db = L.uvsphere_bm(u=10, v=8, radius=1.0)
            for v in db.verts:
                v.co.z *= length
                taper = 1.2 if v.co.z < 0 else 1.0
                v.co.x *= taper
                v.co.y *= taper
            bmesh.ops.scale(db, vec=(0.07, 0.024, 1.0), verts=db.verts)
            drip = L.obj_from_bm("CaramelDrip", db, caramel)
            edge = W / 2 + 0.005
            if face_axis == "y":
                drip.location = (t, sign * edge, top - length * 0.85)
            else:
                drip.location = (sign * edge, t, top - length * 0.85)
                drip.rotation_euler = (0, 0, math.pi / 2)
            parts.append(drip)
    # Caramel glaze cap poured over the loaf top; the drips hang from its edge.
    cap = T.bread("CaramelCap", T.rounded_rect(W + 0.03, W + 0.03, 0.155), 0.05, caramel, caramel, round_frac=0.5)
    cap.location.z = top - 0.04
    parts.append(cap)
    return parts


if __name__ == "__main__":
    sys.exit(0 if T.render(NAME, build, views=((0.8, -1.0, 0.6), (0.2, -0.5, 1.3))) else 1)
