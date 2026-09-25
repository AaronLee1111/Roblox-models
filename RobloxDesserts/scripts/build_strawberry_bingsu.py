"""Strawberry Bingsu: mint bowl, shaved-ice mound with strawberry sauce and a
condensed-milk ribbon, rings of strawberry halves (cut side out), a pink
strawberry scoop and a whole strawberry on top."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import bingsu_common as B  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "StrawberryBingsu"
HALF_R = 0.16


def build(out_dir):
    bowl = L.make_material("Bowl", B.bowl_texture(out_dir, "#bfe8d3"), roughness=0.5, specular=0.3)
    ice = L.make_material("ShavedIce", B.ice_texture(out_dir, "ShavedIce_Color", "#f2466b", seed=8),
                          roughness=0.85, specular=0.15)
    skin = L.make_material("Strawberry", P.strawberry_texture(out_dir), roughness=0.55, specular=0.3)
    cut = L.make_material("StrawberryCut", P.cut_texture(out_dir), roughness=0.6, specular=0.25)
    scoop_mat = L.make_material("StrawberryScoop", L.solid_image("StrawberryScoop_Color", "#ffb3c7", out_dir),
                                roughness=0.7, specular=0.2)
    leaf = L.make_material("Leaf", L.solid_image("Leaf_Color", "#5ccb5f", out_dir),
                           roughness=0.75, specular=0.25)

    parts = [B.build_bowl(bowl), B.build_mound(ice)]
    for count, s, off in ((7, 0.5, 0.0), (4, 0.76, 0.45)):
        for i in range(count):
            th = 2 * math.pi * i / count + off
            h = P.strawberry_half(skin, cut, HALF_R)
            # Cut face outward, standing on the slope; lift keeps the skin side in the snow.
            h.matrix_world = B.frame_on_mound(th, s, lift=0.06, tilt_up=0.8, spin=0.15 * math.sin(2 * i))
            parts.append(h)

    top = B.crown_z()
    sc = B.scoop(scoop_mat)
    sc.location = (0, 0, top + 0.13)
    parts.append(sc)
    berry = P.strawberry(skin, leaf, radius=0.16)
    P.move(berry, dz=top + 0.25, tilt=(math.radians(8), math.radians(-6)))
    parts += berry
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.9, -1.0, 0.7), (0.25, -0.5, 1.4)),
                          bg="#f4eee6", ground="#efe6da", margin=1.05)
    sys.exit(0 if ok else 1)
