"""Mango Bingsu: pastel-blue bowl, shaved-ice mound with mango sauce and a
condensed-milk ribbon, chunky mango cubes, mango scoop and mint."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import bingsu_common as B  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "MangoBingsu"
CUBE = 0.16            # mango cube size (studs) - chunky so it reads at distance


def mango_cube(mat, size=CUBE, radius=0.3, n=3):
    """Rounded box: flat faces, soft rounded edges (reads as a clean fruit cube)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=n - 1, use_grid_fill=True)
    inner = 1 - radius
    for vert in bm.verts:
        p = vert.co.copy()
        q = Vector((max(-inner, min(inner, p.x)), max(-inner, min(inner, p.y)), max(-inner, min(inner, p.z))))
        d = p - q
        vert.co = q + (d.normalized() * radius if d.length > 1e-6 else d)
        vert.co *= size / 2
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.obj_from_bm("MangoCube", bm, mat)


def build(out_dir):
    bowl = L.make_material("Bowl", B.bowl_texture(out_dir, "#b9dbf5"), roughness=0.5, specular=0.3)
    ice = L.make_material("ShavedIce", B.ice_texture(out_dir, "ShavedIce_Color", "#ff9d1f"),
                          roughness=0.85, specular=0.15)
    mango = L.make_material("Mango", L.solid_image("Mango_Color", "#ffb52e", out_dir),
                            roughness=0.5, specular=0.3)
    scoop_mat = L.make_material("MangoScoop", L.solid_image("MangoScoop_Color", "#ffe39a", out_dir),
                                roughness=0.7, specular=0.2)
    leaf = L.make_material("Mint", L.solid_image("Mint_Color", "#4fc463", out_dir),
                           roughness=0.7, specular=0.25)

    parts = [B.build_bowl(bowl), B.build_mound(ice)]
    rings = [(8, 0.5, 0.0), (7, 0.74, 0.4)]         # heaped around the crown (count, s, offset)
    for count, s, off in rings:
        for i in range(count):
            th = 2 * math.pi * i / count + off
            c = mango_cube(mango)
            c.matrix_world = B.frame_on_mound(th, s, lift=CUBE * 0.3, spin=0.3 * math.sin(3 * i))
            parts.append(c)

    top = B.crown_z()
    sc = B.scoop(scoop_mat)
    sc.location = (0, 0, top + 0.13)
    parts.append(sc)
    # Mint sprig tucked against the side of the scoop, not sprouting from its top.
    for k, a in enumerate((-0.35, 0.35)):
        m = B.mint_leaf(leaf, size=0.17)
        m.matrix_world = (Matrix.Translation((0.1, -0.08, top + 0.2)) @ Matrix.Rotation(-0.6 + a, 4, "Z")
                          @ Matrix.Rotation(math.radians(-30), 4, "Y"))
        parts.append(m)
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.9, -1.0, 0.7), (0.25, -0.5, 1.4)),
                          bg="#f4eee6", ground="#efe6da", margin=1.05)
    sys.exit(0 if ok else 1)
