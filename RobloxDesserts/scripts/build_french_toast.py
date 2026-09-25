"""French Toast: two thick golden custard-soaked slices (toast-family bread)
overlapping on the café plate, with a butter pat, maple syrup drizzle,
powdered sugar, strawberry halves and blueberries."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import premium_parts as Q  # noqa: E402
import toast_family as T  # noqa: E402
import numpy as np  # noqa: E402

NAME = "FrenchToast"
THICK = 0.2


def face_texture(out_dir):
    """Golden egg-soaked face with browned griddle patches and powdered sugar."""
    n = 512
    U, V = np.meshgrid((np.arange(n) + 0.5) / n, (np.arange(n) + 0.5) / n)
    rgb = np.broadcast_to(np.array(L.srgb("#f3c35e")), (n, n, 3)).copy()
    rng = np.random.default_rng(9)
    brown = np.array(L.srgb("#d0873a"))
    for _ in range(14):
        cx, cy, r = rng.uniform(0.15, 0.85), rng.uniform(0.15, 0.85), rng.uniform(0.06, 0.13)
        m = np.clip((r - np.hypot(U - cx, (V - cy) * 1.2)) / 0.03, 0, 1)[..., None] * 0.8
        rgb = rgb + (brown - rgb) * m
    sugar = np.zeros((n, n))
    for _ in range(90):
        cx, cy, r = rng.uniform(0.1, 0.6), rng.uniform(0.35, 0.95), rng.uniform(0.006, 0.014)
        sugar = np.maximum(sugar, np.hypot(U - cx, V - cy) < r)
    rgb[sugar > 0] = L.srgb("#fffaf3")
    # Maple syrup zig-zag painted onto the face (follows any tilt, never floats).
    pts = P.chaikin([(0.2, 0.2), (0.35, 0.8), (0.5, 0.25), (0.65, 0.8), (0.8, 0.3)], 3, closed=False)
    d = np.full(U.shape, 9.0)
    for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
        ex, ey = u1 - u0, v1 - v0
        t = np.clip(((U - u0) * ex + (V - v0) * ey) / (ex * ex + ey * ey), 0, 1)
        d = np.minimum(d, np.hypot(U - u0 - t * ex, V - v0 - t * ey))
    rgb[d < 0.03] = L.srgb("#8a3f12")
    return L.image_from_array("FrenchToast_Color", rgb, out_dir)


def build(out_dir):
    face = L.make_material("ToastFace", face_texture(out_dir), roughness=0.65, specular=0.25)
    crust = T.crust_mat(out_dir, "#b86c2a")
    butter = L.make_material("Butter", L.solid_image("Butter_Color", "#ffe68a", out_dir), roughness=0.4, specular=0.35)
    skin = L.make_material("Strawberry", P.strawberry_texture(out_dir), roughness=0.55, specular=0.3)
    cut = L.make_material("StrawberryCut", P.cut_texture(out_dir), roughness=0.55, specular=0.25)
    blue = L.make_material("Blueberry", L.solid_image("Blueberry_Color", "#5d6fd8", out_dir), roughness=0.45,
                           specular=0.3)

    parts = [T.plate(out_dir, "#bfe0f4")]
    outline = T.slice_outline(0.72, 0.74)
    s1 = T.bread("Toast", outline, THICK, face, crust)
    P.move([s1], dx=-0.14, dy=0.08, dz=T.PLATE_TOP - 0.005, rot_z=math.radians(20))
    s2 = T.bread("Toast", outline, THICK, face, crust)
    P.move([s2], dx=0.14, dy=-0.1, dz=T.PLATE_TOP + THICK * 0.72, rot_z=math.radians(-25),
           tilt=(math.radians(-7), math.radians(8)))
    parts += [s1, s2]
    top = T.PLATE_TOP + THICK * 1.72

    s = 0.11
    pat = Q.rounded_extrude("Butter", P.chaikin([(-s, -s), (s, -s), (s, s), (-s, s)], 1), 0.07, butter,
                            round_frac=0.4, steps=2)
    pat.location = (0.14, -0.06, top - 0.02)
    pat.rotation_euler = (math.radians(-7), math.radians(8), 0.5)
    parts.append(pat)
    for x, y, a in ((-0.5, -0.38, 0.4), (0.48, 0.38, 2.4)):
        h = P.strawberry_half(skin, cut, 0.12)
        h.rotation_euler = (math.radians(60), 0, a)
        h.location = (x, y, 0)
        Q.place_on(h, T.PLATE_TOP - 0.005)
        parts.append(h)
    for x, y in ((-0.35, -0.5), (0.58, 0.18), (0.4, -0.5)):
        b = L.obj_from_bm("Blueberry", L.uvsphere_bm(u=14, v=8, radius=0.065), blue)
        b.location = (x, y, T.PLATE_TOP + 0.055)
        parts.append(b)
    return parts


if __name__ == "__main__":
    sys.exit(0 if T.render(NAME, build) else 1)
