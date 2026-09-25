"""Strawberry Shortcake slice: sponge / cream+strawberry / sponge / cream, with a
piped rosette and an exaggerated strawberry on top. Stylized Roblox look."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

NAME = "StrawberryShortcake"
R = 1.0                 # slice length (apex to back arc), studs
ANGLE = 48              # slice angle, degrees
FILL = (0.26, 0.54)     # cream + strawberry filling band
TOP_CREAM = 0.76        # z where the top cream layer starts
TOP = 0.875
BULGE = 0.025           # cream layers puff out past the sponge


def slice_texture(out_dir):
    """Strawberry cross-section on the sphere's cap: pale centre, red rim."""
    h, w = 64, 16
    v = (np.arange(h) + 0.5) / h
    red = np.array(L.srgb("#f0385a"))
    pale = np.array(L.srgb("#ffb3c1"))
    # Wide pale-pink core on the outward cap (v -> 1), bold red rim and back.
    rgb = np.where((v > 0.8)[:, None], pale, red)[:, None, :].repeat(w, axis=1)
    return L.image_from_array("StrawberrySlice_Color", rgb, out_dir)


def build_body(sponge, cream):
    outline = P.wedge_outline(R, ANGLE, tip=0.12)
    rings = [(0.0, 0.03), (0.03, 0.0), (FILL[0] - 0.02, 0.0),
             (FILL[0], 0.0), (FILL[0] + 0.02, -BULGE), (FILL[1] - 0.02, -BULGE), (FILL[1], 0.0),
             (TOP_CREAM - 0.02, 0.0), (TOP_CREAM, -0.015), (TOP - 0.03, -0.015), (TOP, 0.02)]

    def mat_fn(c, kind):
        if kind == "top":
            return 1
        if kind == "bottom":
            return 0
        if math.hypot(c.x, c.y) > R * 0.93:      # frosted back
            return 1
        if FILL[0] <= c.z <= FILL[1] or c.z >= TOP_CREAM - 0.005:
            return 1
        return 0

    return P.loft("Cake", outline, rings, [sponge, cream], mat_fn)


def build_slices(mat):
    parts = []
    h = math.radians(ANGLE) / 2
    zc = (FILL[0] + FILL[1]) / 2
    for sign in (1, -1):
        d = Vector((math.cos(h), sign * math.sin(h), 0))
        n = Vector((-math.sin(h), sign * math.cos(h), 0))
        for t in (0.36, 0.62, 0.87):
            bm = L.uvsphere_bm(u=12, v=8, radius=0.108)
            for vert in bm.verts:
                vert.co.z *= 0.28
                vert.co.x *= 0.85          # slightly tall, heart-ish strawberry half
            s = L.obj_from_bm("StrawberrySlice", bm, mat)
            s.rotation_euler = Vector((0, 0, 1)).rotation_difference(n).to_euler()
            s.location = d * (t * R) + n * 0.01 + Vector((0, 0, zc))
            parts.append(s)
    return parts


def build(out_dir):
    sponge = L.make_material("Sponge", L.solid_image("Sponge_Color", "#f8c77c", out_dir),
                             roughness=0.8, specular=0.2)
    cream = L.make_material("Cream", L.solid_image("Cream_Color", "#fff8ef", out_dir),
                            roughness=0.7, specular=0.25)
    berry = L.make_material("Strawberry", P.strawberry_texture(out_dir), roughness=0.55, specular=0.3)
    leaf = L.make_material("Leaf", L.solid_image("Leaf_Color", "#5ccb5f", out_dir),
                           roughness=0.75, specular=0.25)
    slice_mat = L.make_material("StrawberrySlice", slice_texture(out_dir), roughness=0.55, specular=0.3)

    parts = [build_body(sponge, cream)]
    parts += build_slices(slice_mat)

    back = R * 0.7
    dollop = P.cream_dollop("Rosette", cream, radius=0.2, height=0.24)
    dollop.location = (back, 0, TOP - 0.02)
    parts.append(dollop)
    parts += P.move(P.strawberry(berry, leaf, radius=0.2), dx=back, dz=TOP + 0.05)
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((-0.75, -1.0, 0.7), (1.0, -0.5, 0.8)),
                          bg="#f4eee6", ground="#efe6da", margin=1.1)
    sys.exit(0 if ok else 1)
