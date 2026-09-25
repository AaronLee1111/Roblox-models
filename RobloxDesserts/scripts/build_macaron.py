"""Macaron pair: oversized pastel macarons, one lying flat and one standing on
its edge. Domed shells with a puffy ruffled 'foot', thick bulging cream filling.
Stylized, collectible Roblox look."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

NAME = "Macaron"
R = 0.42           # shell radius
H = 0.2            # shell height
F = 0.12           # filling thickness
SEG = 56
# Shell profile (r, z, is_foot) from the dome centre down to the flat base.
SHELL = [(0.0, 1.0, 0), (0.3, 0.97, 0), (0.55, 0.9, 0), (0.78, 0.76, 0), (0.93, 0.58, 0),
         (1.0, 0.42, 0), (1.05, 0.32, 1), (1.09, 0.2, 1), (1.06, 0.08, 1), (0.97, 0.0, 1), (0.0, 0.0, 0)]


def shell_texture(out_dir, name, hex_shell, hex_foot):
    """v = profile row: dome colour, lighter puffy foot near the base."""
    h = 64
    v = (np.arange(h) + 0.5) / h
    rgb = np.where((v > 0.56)[:, None], np.array(L.srgb(hex_foot)), np.array(L.srgb(hex_shell)))
    return L.image_from_array(name, rgb[:, None, :].repeat(8, axis=1), out_dir)


def build_shell(mat, dome=1.0):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    rows = []
    n = len(SHELL)
    for k, (r, z, foot) in enumerate(SHELL):
        row = []
        for j in range(SEG):
            a = 2 * math.pi * j / SEG
            rr = r * R
            if foot:   # puffy, slightly irregular ruffle
                rr += R * 0.045 * (0.6 * math.sin(14 * a) + 0.4 * math.sin(9 * a + 1.0))
            zz = z * H if z <= 0.42 else (0.42 + (z - 0.42) * dome) * H
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), zz)))
        rows.append(row)
    for k in range(n - 1):
        for j in range(SEG):
            j2 = (j + 1) % SEG
            f = bm.faces.new((rows[k][j], rows[k + 1][j], rows[k + 1][j2], rows[k][j2]))
            for loop, kk in zip(f.loops, (k, k + 1, k + 1, k)):
                loop[uv].uv = (0.5, kk / (n - 1))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.obj_from_bm("Shell", bm, mat)


def build_macaron(shell_mat, fill_mat):
    """Assembled macaron, base on z=0, centred on the origin."""
    bottom = build_shell(shell_mat, dome=0.45)       # flatter underside so it sits nicely
    for v in bottom.data.vertices:                    # mirror in mesh data (no negative scale)
        v.co.z = -v.co.z
    bottom.data.flip_normals()
    bottom.location.z = H * (0.42 + 0.58 * 0.45)
    fill = P.lathe("Filling", [(0.0, 0.0), (R * 0.9, 0.0), (R * 0.97, F * 0.3), (R * 0.98, F * 0.6),
                               (R * 0.92, F), (0.0, F)], fill_mat, segments=SEG)
    fill.location.z = bottom.location.z - 0.01
    top = build_shell(shell_mat)
    top.location.z = fill.location.z + F - 0.01
    return [bottom, fill, top]


def build(out_dir):
    pink = L.make_material("ShellPink", shell_texture(out_dir, "ShellPink_Color", "#ffa8c5", "#ffc4d7"),
                           roughness=0.55, specular=0.25)
    lav = L.make_material("ShellLavender", shell_texture(out_dir, "ShellLavender_Color", "#c9b5f5", "#ddd0fa"),
                          roughness=0.55, specular=0.25)
    cream = L.make_material("Filling", L.solid_image("Filling_Color", "#fff4e4", out_dir),
                            roughness=0.6, specular=0.25)

    flat = build_macaron(pink, cream)
    P.move(flat, dx=-0.34, dy=0.1)
    stand = build_macaron(lav, cream)
    # Stand the lavender one on its edge, leaning back a touch, beside the pink one.
    total_h = max(o.location.z for o in stand) + H
    P.move(stand, dz=-total_h / 2)                    # centre it before rotating
    P.move(stand, rot_z=math.radians(-65), tilt=(math.radians(78), 0.0))   # three-quarter: filling shows
    bpy.context.view_layer.update()
    min_z = min((o.matrix_world @ Vector(c)).z for o in stand for c in o.bound_box)
    P.move(stand, dx=0.42, dy=-0.05, dz=-min_z)
    return flat + stand


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.3, -1.0, 0.55), (0.9, -0.6, 0.9)),
                          bg="#f4eee6", ground="#efe6da", margin=0.95)
    sys.exit(0 if ok else 1)
