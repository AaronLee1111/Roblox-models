"""Fruit Tart: fluted pastry shell, domed custard, a petal ring of kiwi and
orange slices, strawberry halves (cut side up) in the centre and blueberries.
Stylized Roblox look: few, large, readable fruit pieces."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402

NAME = "FruitTart"
FLUTES = 18
SEG = FLUTES * 6
CUSTARD_Z = 0.2
SLICE_R, SLICE_T = 0.125, 0.04

# Shell profile (r, z, fluted?) from the outer bottom centre, over the rim, to the inner floor.
SHELL = [(0.0, 0.0, 0), (0.44, 0.0, 0), (0.49, 0.02, 1), (0.535, 0.07, 1), (0.555, 0.15, 1),
         (0.56, 0.205, 1), (0.545, 0.24, 1), (0.515, 0.25, 1), (0.49, 0.23, 0), (0.48, 0.17, 0),
         (0.0, 0.16, 0)]


def build_shell(mat):
    bm = bmesh.new()
    grid = []
    for r, z, fluted in SHELL:
        row = []
        for j in range(SEG):
            a = 2 * math.pi * j / SEG
            # Rounded scallops: broad soft lobes with gentle valleys (not a zigzag).
            lobe = abs(math.cos(FLUTES * a / 2)) ** 0.6
            rr = r + (0.03 * (lobe - 0.5) if fluted else 0.0)
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        grid.append(row)
    for a_row, b_row in zip(grid, grid[1:]):
        for j in range(SEG):
            k = (j + 1) % SEG
            bm.faces.new((a_row[j], a_row[k], b_row[k], b_row[j]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.obj_from_bm("Shell", bm, mat)


def build_custard(mat):
    prof = [(0.0, CUSTARD_Z + 0.03), (0.2, CUSTARD_Z + 0.026), (0.36, CUSTARD_Z + 0.014),
            (0.46, CUSTARD_Z - 0.005), (0.5, CUSTARD_Z - 0.03)]
    return P.lathe("Custard", prof, mat, segments=40)


def slice_atlas(out_dir):
    """Left half: kiwi slice. Right half: orange wheel. Each drawn in a unit disc."""
    h, w = 256, 512
    rgb = np.ones((h, w, 3))
    a = (np.arange(h) + 0.5) / h * 2 - 1
    X, Y = np.meshgrid(a, a)
    r = np.hypot(X, Y)
    ang = np.arctan2(Y, X)
    # Kiwi.
    k = np.broadcast_to(np.array(L.srgb("#7fc94b")), (h, h, 3)).copy()
    k[(np.cos(ang * 14) > 0.75) & (r > 0.4) & (r < 0.86)] = L.srgb("#9bd96a")   # soft radial rays
    k[r > 0.9] = L.srgb("#9c7b3e")                                              # skin
    k[r < 0.3] = L.srgb("#f1f4c4")                                              # pale core
    for i in range(12):                                                         # bold seed ring
        t = 2 * math.pi * i / 12
        k[(X - 0.43 * math.cos(t)) ** 2 / 0.05 ** 2 + (Y - 0.43 * math.sin(t)) ** 2 / 0.075 ** 2 < 1] = \
            L.srgb("#2f2a26")
    # Orange.
    o = np.broadcast_to(np.array(L.srgb("#ffb347")), (h, h, 3)).copy()
    seg_line = np.abs(np.sin(ang * 5)) < 0.09
    o[seg_line & (r < 0.84)] = L.srgb("#ffe4b0")
    o[(r > 0.84) & (r <= 0.9)] = L.srgb("#fff1d8")                              # pith
    o[r > 0.9] = L.srgb("#ff8f1f")                                              # rind
    o[r < 0.12] = L.srgb("#ffe4b0")
    rgb[:, :h] = k
    rgb[:, h:] = o
    return L.image_from_array("FruitSlices_Color", rgb, out_dir)


def fruit_slice(mat, kind):
    """Rounded disc; top/bottom UVs map into the kiwi or orange half of the atlas."""
    R, T = SLICE_R, SLICE_T
    prof = [(0.0, 0.0), (R - 0.012, 0.0), (R, 0.012), (R, T - 0.012), (R - 0.012, T), (0.0, T)]
    obj = P.lathe("Slice", prof, mat, segments=24)
    off = 0.0 if kind == "kiwi" else 0.5
    me = obj.data
    uv = me.uv_layers.active.data
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        uv[loop.index].uv = (off + (co.x / (2 * R) + 0.5) * 0.5, co.y / (2 * R) + 0.5)
    return obj


def build(out_dir):
    crust = L.make_material("TartCrust", L.solid_image("TartCrust_Color", "#eaad5f", out_dir),
                            roughness=0.8, specular=0.2)
    custard = L.make_material("Custard", L.solid_image("Custard_Color", "#ffe59b", out_dir),
                              roughness=0.6, specular=0.25)
    skin = L.make_material("Strawberry", P.strawberry_texture(out_dir), roughness=0.5, specular=0.3)
    cut = L.make_material("StrawberryCut", P.cut_texture(out_dir), roughness=0.55, specular=0.25)
    slices = L.make_material("FruitSlices", slice_atlas(out_dir), roughness=0.5, specular=0.3)
    blue = L.make_material("Blueberry", L.solid_image("Blueberry_Color", "#5d6fd8", out_dir),
                           roughness=0.45, specular=0.3)

    parts = [build_shell(crust), build_custard(custard)]
    top = CUSTARD_Z + 0.01
    # Petal ring of alternating kiwi / orange slices, outer edge lifted.
    for i in range(8):
        a = 2 * math.pi * i / 8
        s = fruit_slice(slices, "kiwi" if i % 2 == 0 else "orange")
        P.move([s], dx=0.33 * math.cos(a), dy=0.33 * math.sin(a), dz=top - 0.005, rot_z=a,
               tilt=(0.0, math.radians(-18)))
        parts.append(s)
    # Strawberry halves, cut side up, tips pointing outward.
    for i in range(3):
        a = 2 * math.pi * i / 3 + math.pi / 6
        h = P.strawberry_half(skin, cut, 0.13)
        h.rotation_euler = (math.radians(55), 0, 0)          # cut face (+Y) tipped up, skin still shows
        P.move([h], dx=0.16 * math.cos(a), dy=0.16 * math.sin(a), dz=top + 0.05, rot_z=a + math.pi / 2)
        parts.append(h)
    # Blueberries tucked between the halves.
    for i in range(3):
        a = 2 * math.pi * i / 3 + math.pi / 6 + math.pi / 3
        b = L.obj_from_bm("Blueberry", L.uvsphere_bm(u=14, v=8, radius=0.06), blue)
        b.location = (0.15 * math.cos(a), 0.15 * math.sin(a), top + 0.05)
        parts.append(b)
    b = L.obj_from_bm("Blueberry", L.uvsphere_bm(u=14, v=8, radius=0.06), blue)
    b.location = (0, 0, top + 0.06)
    parts.append(b)
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.8, -1.0, 0.9), (0.15, -0.35, 1.3)),
                          bg="#f4eee6", ground="#efe6da", margin=0.95)
    sys.exit(0 if ok else 1)
