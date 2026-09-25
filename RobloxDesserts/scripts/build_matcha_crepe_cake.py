"""Matcha Crepe Cake slice: stacked pale-green crepes with cream seams, a
matcha-dusted top and piped cream rosettes. Stylized Roblox look.

The layering is carried by a gentle geometric ripple (each crepe bulges, each
cream seam is recessed) plus a matching stripe texture, so it reads without
modelling every crepe separately."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import numpy as np  # noqa: E402

NAME = "MatchaCrepeCake"
R = 1.0
ANGLE = 48
LAYERS = 8
LAYER_H = 0.092
H = LAYERS * LAYER_H
SEAM_INSET = 0.01        # cream seams sit slightly inside the crepe bulge
CREAM_FRAC = 0.24        # fraction of each layer that is cream (drawn at the seam)


def layer_texture(out_dir):
    """Vertical strip indexed by v = z / H: crepe green with cream seams."""
    h = 512
    v = (np.arange(h) + 0.5) / h
    crepe = np.array(L.srgb("#c3dc9a"))
    cream = np.array(L.srgb("#fff5dc"))
    phase = (v * LAYERS) % 1.0
    # Cream centred on each seam (phase ~ 0/1); bottom edge stays crepe.
    seam = (phase < CREAM_FRAC / 2) | (phase > 1 - CREAM_FRAC / 2)
    seam &= (v > 0.02)
    rgb = np.where(seam[:, None], cream, crepe)[:, None, :].repeat(8, axis=1)
    return L.image_from_array("CrepeLayers_Color", rgb, out_dir)


def dusted_cream_texture(out_dir):
    """Cream with a bold matcha-dusted tip (dollop UVs: v = height up the swirl)."""
    h = 64
    v = (np.arange(h) + 0.5) / h
    cream = np.array(L.srgb("#fff8ef"))
    matcha = np.array(L.srgb("#8db35f"))
    rgb = np.where((v > 0.72)[:, None], matcha, cream)[:, None, :].repeat(8, axis=1)
    return L.image_from_array("DustedCream_Color", rgb, out_dir)


def build_body(layers_mat, top_mat):
    outline = P.wedge_outline(R, ANGLE, tip=0.12)
    rings = [(0.0, 0.03)]
    for i in range(LAYERS):
        z0 = i * LAYER_H
        if i:
            rings.append((z0, SEAM_INSET))
        rings.append((z0 + LAYER_H / 2, 0.0))
    rings.append((H, 0.03))   # soft top edge

    def mat_fn(c, kind):
        return 1 if kind == "top" else 0

    return P.loft("Cake", outline, rings, [layers_mat, top_mat], mat_fn,
                  uv_fn=lambda co: (0.5, min(max(co.z / H, 0.0), 1.0)))


def build(out_dir):
    layers_mat = L.make_material("CrepeLayers", layer_texture(out_dir), roughness=0.75, specular=0.2)
    top_mat = L.make_material("MatchaTop", L.solid_image("MatchaTop_Color", "#8db35f", out_dir),
                              roughness=0.85, specular=0.15)
    cream = L.make_material("Cream", dusted_cream_texture(out_dir), roughness=0.7, specular=0.25)

    parts = [build_body(layers_mat, top_mat)]
    # Three piped rosettes along the back arc.
    half = math.radians(ANGLE) / 2
    for k, a in enumerate((-0.55, 0.0, 0.55)):
        ang = a * half
        r = R * 0.8
        d = P.cream_dollop("Rosette", cream, radius=0.12 if k != 1 else 0.14,
                           height=0.17 if k != 1 else 0.21)
        d.location = (r * math.cos(ang), r * math.sin(ang), H - 0.015)
        d.rotation_euler = (0, 0, 0.4 * k)
        parts.append(d)
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((-0.75, -1.0, 0.7), (1.0, -0.5, 0.9)),
                          bg="#f4eee6", ground="#efe6da", margin=1.1)
    sys.exit(0 if ok else 1)
