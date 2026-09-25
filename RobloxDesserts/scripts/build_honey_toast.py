"""Honey Toast: one extra-thick toast-family slice with a diamond-scored top
soaked in amber honey, a butter pat, a honeycomb chunk and a wooden honey
dipper, on a buttery-yellow café plate."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import premium_parts as Q  # noqa: E402
import toast_family as T  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402

NAME = "HoneyToast"
THICK = 0.3
HONEY = "#f2a91e"


def face_texture(out_dir):
    """Toasted crumb, diamond score lines filled with honey, glossy honey pool."""
    n = 512
    U, V = np.meshgrid((np.arange(n) + 0.5) / n, (np.arange(n) + 0.5) / n)
    rgb = np.broadcast_to(np.array(L.srgb("#f6d38c")), (n, n, 3)).copy()
    honey = np.array(L.srgb(HONEY))
    wob = 0.03 * np.sin(np.arctan2(V - 0.5, U - 0.5) * 5)
    pool = np.clip((0.4 + wob - np.hypot(U - 0.5, V - 0.5)) / 0.012, 0, 1)[..., None]
    rgb = rgb + (honey - rgb) * pool
    k = 7
    d1 = np.abs(((U + V) * k) % 1.0 - 0.5)
    d2 = np.abs(((U - V) * k) % 1.0 - 0.5)
    lines = (d1 > 0.43) | (d2 > 0.43)
    rgb[lines] = L.srgb("#c9780f")                           # honey-filled score lines
    glint = np.hypot((U - 0.36) / 0.07, (V - 0.64) / 0.035) < 1
    rgb[glint] = L.srgb("#ffe7a8")                           # painted glossy highlight
    return L.image_from_array("HoneyToastFace_Color", rgb, out_dir)


def honeycomb_texture(out_dir):
    n = 256
    U, V = np.meshgrid((np.arange(n) + 0.5) / n, (np.arange(n) + 0.5) / n)
    rgb = np.broadcast_to(np.array(L.srgb("#e2940f")), (n, n, 3)).copy()   # wax walls
    s = 5.0
    for row in range(-1, 8):
        for col in range(-1, 7):
            cx = (col + 0.5 * (row % 2)) / s
            cy = row * 0.866 / s
            hx, hy = np.abs(U - cx), np.abs(V - cy)
            hexd = np.maximum(hx * 0.866 + hy * 0.5, hy)      # hexagon distance
            rgb[hexd < 0.078] = L.srgb("#ffcf4a")             # honey-filled cells
    return L.image_from_array("Honeycomb_Color", rgb, out_dir)


def honeycomb(mat, r=0.17, h=0.13):
    pts = [(r * math.cos(math.pi / 3 * k + math.pi / 6), r * math.sin(math.pi / 3 * k + math.pi / 6)) for k in range(6)]
    obj = Q.rounded_extrude("Honeycomb", [np.array(p) for p in pts], h, mat, round_frac=0.2, steps=1,
                            uv_fn=lambda co: (co.x / (2 * r) + 0.5, co.y / (2 * r) + 0.5))
    return obj


def dipper(wood, honey_mat):
    parts = []
    path = [(-0.35 + 0.35 * t, 0.0, 0.02 + 0.08 * t) for t in np.linspace(0, 1, 5)]
    parts.append(P.tube("DipperHandle", path, [0.028] * len(path), wood, ring_n=10, caps=True))
    head = P.lathe("DipperHead", [(0.0, -0.08), (0.05, -0.08), (0.065, -0.06), (0.05, -0.04), (0.065, -0.02),
                                  (0.05, 0.0), (0.065, 0.02), (0.05, 0.04), (0.065, 0.06), (0.05, 0.08),
                                  (0.0, 0.08)], honey_mat, segments=16)
    head.rotation_euler = (0, math.radians(90 - 13), 0)
    head.location = (0.07, 0.0, 0.115)
    parts.append(head)
    return parts


def build(out_dir):
    face = L.make_material("ToastFace", face_texture(out_dir), roughness=0.55, specular=0.3)
    crust = T.crust_mat(out_dir, "#c47a2c")
    butter = L.make_material("Butter", L.solid_image("Butter_Color", "#ffe68a", out_dir), roughness=0.4, specular=0.35)
    comb = L.make_material("Honeycomb", honeycomb_texture(out_dir), roughness=0.35, specular=0.45)
    honey = L.make_material("Honey", L.solid_image("Honey_Color", HONEY, out_dir), roughness=0.3, specular=0.45)
    wood = L.make_material("Wood", L.solid_image("Wood_Color", "#e0ae72", out_dir), roughness=0.8, specular=0.2)

    parts = [T.plate(out_dir, "#fff0b8")]
    sl = T.bread("Toast", T.slice_outline(0.84, 0.86), THICK, face, crust)
    P.move([sl], dz=T.PLATE_TOP - 0.005, rot_z=math.radians(-12))
    parts.append(sl)
    top = T.PLATE_TOP + THICK - 0.005
    s = 0.13
    pat = Q.rounded_extrude("Butter", P.chaikin([(-s, -s), (s, -s), (s, s), (-s, s)], 1), 0.08, butter,
                            round_frac=0.4, steps=2)
    pat.location = (0.0, 0.0, top - 0.01)
    pat.rotation_euler = (0, 0, 0.6)
    parts.append(pat)
    hc = honeycomb(comb)
    hc.location = (0.5, -0.36, T.PLATE_TOP - 0.004)
    hc.rotation_euler = (0, 0, 0.3)
    parts.append(hc)
    parts += P.move(dipper(wood, honey), dx=-0.1, dy=-0.55, dz=T.PLATE_TOP, rot_z=math.radians(-10))
    # Honey drips over the front crust edge.
    import bmesh as _bm
    for k, (x, length) in enumerate(((-0.2, 0.08), (0.05, 0.12), (0.25, 0.07))):
        db = L.uvsphere_bm(u=10, v=8, radius=1.0)
        for v in db.verts:
            v.co.z *= length
            taper = 1.2 if v.co.z < 0 else 1.0
            v.co.x *= taper
            v.co.y *= taper
        _bm.ops.scale(db, vec=(0.055, 0.022, 1.0), verts=db.verts)
        drip = L.obj_from_bm("HoneyDrip", db, honey)
        drip.location = (x, -0.428, top - length * 0.2)
        parts.append(drip)
    P.move(parts[-3:], rot_z=math.radians(-12))
    return parts


if __name__ == "__main__":
    sys.exit(0 if T.render(NAME, build) else 1)
