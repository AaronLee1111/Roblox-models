"""Shared toast-family builder: one stylized bread geometry (classic slice with
domed 'shoulders', or a tall brick loaf), crust on the sides, crumb on the
cut faces, rounded edges. French, Honey and Shibuya Toast all build on it and
use the pancake family's café plate."""
import math

import dessert_lib as L
import cafe_parts as P
import build_souffle_pancakes as S
import numpy as np

PLATE_TOP = S.PLATE_TOP


def slice_outline(w=0.8, h=0.82, steps=14):
    """Classic bread-slice silhouette (CCW, centred): straight lower body with a
    puffy, squarish domed crown. Kept convex so rounded offsets never pinch."""
    y0 = h / 2 - 0.34 * h                                # where the crown starts
    ry = h / 2 - y0
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2)]
    for k in range(steps + 1):                           # crown: half-superellipse, right to left
        t = math.pi * k / steps
        c, sn = math.cos(t), math.sin(t)
        pts.append((w / 2 * math.copysign(abs(c) ** 0.45, c), y0 + ry * abs(sn) ** 0.7))
    return P.chaikin(pts, 2)


def rounded_rect(w, d, r, steps=5):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, -d / 2 + r, -90), (w / 2 - r, d / 2 - r, 0),
                       (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180)):
        for k in range(steps + 1):
            a = math.radians(a0 + 90 * k / steps)
            pts.append(np.array((cx + r * math.cos(a), cy + r * math.sin(a))))
    return pts


def bread(name, outline, thick, crumb_mat, crust_mat, round_frac=0.3, steps=2, bounds=None):
    """Extrude an outline into bread: rounded edges, crust material on the sides,
    crumb material (planar-UV'd) on the top and bottom faces."""
    b = thick * round_frac
    rings = []
    for k in range(steps + 1):
        a = math.pi / 2 * k / steps
        rings.append((b - b * math.cos(a), b - b * math.sin(a)))
    for k in range(steps + 1):
        a = math.pi / 2 * k / steps
        rings.append((thick - b + b * math.sin(a), b - b * math.cos(a)))
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    bx = bounds or (min(xs) - b, max(xs) + b, min(ys) - b, max(ys) + b)

    def uv_fn(co):
        return ((co.x - bx[0]) / (bx[1] - bx[0]), (co.y - bx[2]) / (bx[3] - bx[2]))

    return P.loft(name, outline, rings, [crumb_mat, crust_mat],
                  lambda c, kind: 0 if kind in ("top", "bottom") else 1, uv_fn=uv_fn)


def plate(out_dir, hex_color):
    m = L.make_material("Plate", L.solid_image("Plate_Color", hex_color, out_dir), roughness=0.5, specular=0.3)
    return S.build_plate(m)


def crust_mat(out_dir, hex_color="#c98236"):
    return L.make_material("Crust", L.solid_image("Crust_Color", hex_color, out_dir), roughness=0.75, specular=0.2)


def render(name, build, views=((0.8, -1.0, 0.75), (0.2, -0.5, 1.3))):
    return L.build_and_ship(name, build, views=views, bg="#f4eee6", ground="#efe6da", margin=1.0)
