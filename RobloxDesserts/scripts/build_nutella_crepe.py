"""Nutella Crepe: a quarter-folded crepe (crepe-family layered fold) with
hazelnut-chocolate spread peeking out between the layers and drizzled over
the top, banana slices, hazelnuts, powdered sugar and a cream dollop, on the
café plate."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import crepe_family as C  # noqa: E402
import build_souffle_pancakes as S  # noqa: E402
import numpy as np  # noqa: E402

NAME = "NutellaCrepe"
SPREAD = "#5a2d17"


def top_texture(out_dir):
    """Crepe top: lacy crepe, a bold hazelnut-chocolate zig-zag and sugar dots."""
    img = C.crepe_texture(out_dir, "CrepeTop_Base", n=512, spots=35)
    n = img.size[0]
    rgb = np.array(img.pixels[:]).reshape(n, n, 4)[..., :3]
    U, V = np.meshgrid((np.arange(n) + 0.5) / n, (np.arange(n) + 0.5) / n)
    pts = P.chaikin([(0.3, 0.3), (0.45, 0.75), (0.6, 0.3), (0.72, 0.68), (0.85, 0.35), (0.95, 0.6)], 3,
                    closed=False)
    d = np.full(U.shape, 9.0)
    for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
        ex, ey = u1 - u0, v1 - v0
        t = np.clip(((U - u0) * ex + (V - v0) * ey) / (ex * ex + ey * ey), 0, 1)
        d = np.minimum(d, np.hypot(U - u0 - t * ex, V - v0 - t * ey))
    rgb[d < 0.042] = L.srgb(SPREAD)
    rng = np.random.default_rng(3)
    for _ in range(60):
        cx, cy = rng.uniform(0.15, 0.95), rng.uniform(0.1, 0.9)
        rgb[np.hypot(U - cx, V - cy) < 0.009] = (1.0, 0.99, 0.96)
    return L.image_from_array("CrepeTop_Color", rgb, out_dir)


def banana_slice(mat, r=0.075):
    obj = P.lathe("Banana", [(0.0, 0.0), (r - 0.01, 0.0), (r, 0.01), (r, 0.03), (r - 0.01, 0.04), (0.0, 0.04)],
                  mat, segments=16)
    return obj


def build(out_dir):
    top_mat = L.make_material("CrepeTop", top_texture(out_dir), roughness=0.7, specular=0.2)
    edge_mat = C.layered_edge_mat(out_dir, fill_hex=SPREAD, seam=0.17)
    plate = L.make_material("Plate", L.solid_image("Plate_Color", "#c9e6f5", out_dir), roughness=0.5, specular=0.3)
    banana = L.make_material("Banana", L.solid_image("Banana_Color", "#ffe57a", out_dir), roughness=0.6, specular=0.25)
    nut = L.make_material("Hazelnut", L.solid_image("Hazelnut_Color", "#b0713a", out_dir), roughness=0.55, specular=0.3)
    cream = L.make_material("Cream", L.solid_image("Cream_Color", "#fff8ef", out_dir), roughness=0.7, specular=0.25)

    parts = [S.build_plate(plate)]
    fold, H = C.folded_crepe(top_mat, edge_mat, R=0.95, angle=80, layers=4, layer_h=0.06)
    P.move([fold], dx=-0.45, dy=0.0, dz=C.PLATE_TOP - 0.005, rot_z=math.radians(-15))
    parts.append(fold)
    top = C.PLATE_TOP + H
    for k, (x, y) in enumerate(((0.1, -0.1), (0.26, 0.06), (0.36, -0.16))):
        b = banana_slice(banana)
        b.location = (x, y, top - 0.01)
        b.rotation_euler = (0.1 * k, -0.08, 0)
        parts.append(b)
    spread = L.make_material("Spread", L.solid_image("Spread_Color", SPREAD, out_dir), roughness=0.35,
                             specular=0.4)
    d = P.cream_dollop("NutellaSwirl", spread, radius=0.15, height=0.2)
    d.location = (-0.12, 0.02, top - 0.01)
    parts.append(d)
    c = P.cream_dollop("Cream", cream, radius=0.1, height=0.14)
    c.location = (0.46, 0.1, top - 0.02)
    parts.append(c)
    for x, y in ((0.52, 0.3), (0.5, -0.42), (-0.4, -0.45), (0.42, 0.44)):
        h = L.obj_from_bm("Hazelnut", L.uvsphere_bm(u=12, v=8, radius=0.055), nut)
        h.scale = (1, 1, 1.15)
        h.location = (x, y, C.PLATE_TOP + 0.055)
        parts.append(h)
    for x, y in ((0.55, -0.1), (-0.5, 0.42)):
        b = banana_slice(banana)
        b.location = (x, y, C.PLATE_TOP - 0.004)
        parts.append(b)
    return parts


if __name__ == "__main__":
    sys.exit(0 if C.render(NAME, build, views=((0.8, -1.0, 0.7), (0.2, -0.5, 1.3))) else 1)
