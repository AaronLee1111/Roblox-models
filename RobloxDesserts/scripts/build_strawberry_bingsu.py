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
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "StrawberryBingsu"
HALF_R = 0.16


def cut_texture(out_dir):
    """Strawberry cross-section: white heart core, pale-pink flesh, red rim."""
    n = 128
    a = (np.arange(n) + 0.5) / n * 2 - 1
    X, Z = np.meshgrid(a, a)
    r = np.hypot(X / 0.95, Z)
    rgb = np.broadcast_to(np.array(L.srgb("#f0385a")), (n, n, 3)).copy()
    rgb[r < 0.78] = L.srgb("#ff9fb2")
    core = (X / 0.22) ** 2 + ((Z - 0.1) / 0.5) ** 2 < 1
    rgb[core] = L.srgb("#ffe3e8")
    return L.image_from_array("StrawberryCut_Color", rgb, out_dir)


def strawberry_half(skin, cut):
    """Berry shape (tip up), halved along Y; the cut face (+Y) gets the cut material."""
    bm = L.uvsphere_bm(u=16, v=10, radius=HALF_R)
    for vert in bm.verts:
        co = vert.co
        t = min(1.0, max(0.0, (co.z / HALF_R + 1) / 2))
        radial = 0.35 + 0.65 * t ** 0.45
        co.x *= radial
        co.y *= radial
        co.z *= 1.2
        if co.z > HALF_R:
            co.z = HALF_R + (co.z - HALF_R) * 0.6
        co.z = -co.z                                  # tip up
    bmesh.ops.reverse_faces(bm, faces=bm.faces)       # mirroring flipped the winding
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, 1, 0),
                                 clear_outer=True)
    cut_edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    new = bmesh.ops.holes_fill(bm, edges=cut_edges, sides=0)["faces"]
    bmesh.ops.triangulate(bm, faces=new)
    uv = bm.loops.layers.uv.verify()
    cap = [f for f in bm.faces if f.normal.y > 0.9]
    xs = [v.co.x for f in cap for v in f.verts]
    zs = [v.co.z for f in cap for v in f.verts]
    for f in cap:
        f.material_index = 1
        for loop in f.loops:
            co = loop.vert.co
            loop[uv].uv = ((co.x - min(xs)) / (max(xs) - min(xs)), (co.z - min(zs)) / (max(zs) - min(zs)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return P.obj_from_bm_multi("StrawberryHalf", bm, [skin, cut])


def build(out_dir):
    bowl = L.make_material("Bowl", B.bowl_texture(out_dir, "#bfe8d3"), roughness=0.5, specular=0.3)
    ice = L.make_material("ShavedIce", B.ice_texture(out_dir, "ShavedIce_Color", "#f2466b", seed=8),
                          roughness=0.85, specular=0.15)
    skin = L.make_material("Strawberry", P.strawberry_texture(out_dir), roughness=0.55, specular=0.3)
    cut = L.make_material("StrawberryCut", cut_texture(out_dir), roughness=0.6, specular=0.25)
    scoop_mat = L.make_material("StrawberryScoop", L.solid_image("StrawberryScoop_Color", "#ffb3c7", out_dir),
                                roughness=0.7, specular=0.2)
    leaf = L.make_material("Leaf", L.solid_image("Leaf_Color", "#5ccb5f", out_dir),
                           roughness=0.75, specular=0.25)

    parts = [B.build_bowl(bowl), B.build_mound(ice)]
    for count, s, off in ((7, 0.5, 0.0), (4, 0.76, 0.45)):
        for i in range(count):
            th = 2 * math.pi * i / count + off
            h = strawberry_half(skin, cut)
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
