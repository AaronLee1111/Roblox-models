"""Soufflé Pancakes: three tall, puffy pancakes on a pastel plate with maple
syrup, whipped cream and a strawberry. Stylized Roblox look."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import bmesh  # noqa: E402

NAME = "SoufflePancakes"
PR = 0.38          # pancake radius
PH = 0.34          # pancake height
SQUASH = 0.05      # how much each pancake sinks into the one below
SEG = 32
PLATE_TOP = 0.07
PUFF = 2.6         # superellipse exponent: higher = boxier, lower = rounder


def pancake_point(phi, r_scale=1.0, lift=0.0):
    """Superellipse side profile; phi in [-pi/2 (bottom), pi/2 (top)]."""
    c, s = math.cos(phi), math.sin(phi)
    x = PR * r_scale * abs(c) ** (2 / PUFF)
    z = PH / 2 + PH / 2 * math.copysign(abs(s) ** (2 / PUFF), s)
    if s > 0:
        z += 0.025 * (1 - x / PR)   # gentle domed top
    return x, z + lift


def build_pancake(top_mat, side_mat):
    bm = bmesh.new()
    rows = 10
    prof = [pancake_point(-math.pi / 2 + math.pi * k / rows) for k in range(rows + 1)]
    prof[0] = (0.0, prof[0][1])
    prof[-1] = (0.0, prof[-1][1])
    verts = [bm.verts.new((r, 0, z)) for r, z in prof]
    edges = [bm.edges.new((a, b)) for a, b in zip(verts, verts[1:])]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=2 * math.pi, steps=SEG, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.material_index = 0 if abs(f.normal.z) > 0.62 else 1   # browned top/bottom, pale sides
    return P.obj_from_bm_multi("Pancake", bm, [top_mat, side_mat])


def build_syrup(mat):
    """Wavy-edged syrup cap hugging the pancake dome, plus chunky drips."""
    bm = bmesh.new()
    rows = 6
    grid = []
    for j in range(SEG):
        a = 2 * math.pi * j / SEG
        edge_r = 0.72 + 0.12 * math.sin(5 * a) + 0.05 * math.sin(3 * a + 1)
        phi_edge = math.acos(min(1.0, edge_r ** (PUFF / 2)))   # where the profile reaches that radius
        col = []
        for k in range(rows + 1):
            phi = math.pi / 2 - (math.pi / 2 - phi_edge) * k / rows
            x, z = pancake_point(phi, r_scale=1.0)
            x += 0.012
            z += 0.012
            col.append(bm.verts.new((x * math.cos(a), x * math.sin(a), z)))
        grid.append(col)
    for j in range(SEG):
        a, b = grid[j], grid[(j + 1) % SEG]
        for k in range(rows):
            bm.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    parts = [L.obj_from_bm("Syrup", bm, mat)]
    # Drips running down the side, at the syrup's wave peaks.
    for k, a in enumerate((math.pi / 10, math.pi / 10 + 2 * math.pi * 2 / 5, math.pi / 10 + 2 * math.pi * 4 / 5)):
        db = L.uvsphere_bm(u=10, v=8, radius=1.0)
        length = 0.075 + 0.025 * k
        for v in db.verts:
            v.co.z *= length
            taper = 1.25 if v.co.z < 0 else 1.0 - 0.35 * (v.co.z / length)
            v.co.x *= taper       # narrow where it leaves the cap, round drop at the bottom
            v.co.y *= taper
        bmesh.ops.scale(db, vec=(0.03, 0.05, 1.0), verts=db.verts)   # thin radially, wide sideways
        drip = L.obj_from_bm("Drip", db, mat)
        # Hug the side: top of the drip tucks under the syrup's edge, body half-embedded.
        x, z = pancake_point(0.05)
        x_top, z_top = pancake_point(0.7)
        drip.location = ((x - 0.014) * math.cos(a), (x - 0.014) * math.sin(a), z_top - length * 0.9)
        drip.rotation_euler = (0, 0, a)
        parts.append(drip)
    return parts


OFFSETS = [(0.0, 0.0, 0.0), (0.03, -0.02, 0.05), (-0.02, 0.03, -0.04)]


def build_plate(mat):
    """The café plate shared by the whole pancake family."""
    return P.lathe("Plate", [(0.0, 0.0), (0.42, 0.0), (0.45, 0.025), (0.5, 0.035), (0.7, 0.055),
                             (0.76, 0.1), (0.765, 0.12), (0.735, 0.12), (0.68, 0.085),
                             (0.5, PLATE_TOP), (0.0, PLATE_TOP)], mat, segments=40)


def build_stack(top_mat, side_mat, count=3):
    """Slightly offset stack of puffy pancakes. Returns (parts, z of the top pancake's base).
    Toppings are placed relative to the top pancake, then moved by OFFSETS[count-1] and that z."""
    parts = []
    z = PLATE_TOP - 0.01
    for i, (dx, dy, rz) in enumerate(OFFSETS[:count]):
        pc = build_pancake(top_mat, side_mat)
        P.move([pc], dx=dx, dy=dy, dz=z, rot_z=rz)
        parts.append(pc)
        if i < count - 1:
            z += PH - SQUASH
    return parts, z


def build(out_dir):
    top_mat = L.make_material("PancakeGolden", L.solid_image("PancakeGolden_Color", "#e8a24e", out_dir),
                              roughness=0.75, specular=0.2)
    side_mat = L.make_material("PancakeFluffy", L.solid_image("PancakeFluffy_Color", "#fff0c9", out_dir),
                               roughness=0.85, specular=0.15)
    syrup = L.make_material("Syrup", L.solid_image("Syrup_Color", "#b95d20", out_dir),
                            roughness=0.35, specular=0.4)
    cream = L.make_material("Cream", L.solid_image("Cream_Color", "#fff8ef", out_dir),
                            roughness=0.7, specular=0.25)
    plate = L.make_material("Plate", L.solid_image("Plate_Color", "#bfe0f4", out_dir),
                            roughness=0.5, specular=0.3)
    berry = L.make_material("Strawberry", P.strawberry_texture(out_dir), roughness=0.55, specular=0.3)
    leaf = L.make_material("Leaf", L.solid_image("Leaf_Color", "#5ccb5f", out_dir),
                           roughness=0.75, specular=0.25)

    parts = [build_plate(plate)]
    stack, z = build_stack(top_mat, side_mat)
    parts += stack

    # Toppings, placed relative to the top pancake.
    top = []
    top += build_syrup(syrup)
    dollop = P.cream_dollop("Cream", cream, radius=0.19, height=0.27)
    dollop.location = (0.06, -0.08, PH + 0.02)
    top.append(dollop)
    sb = P.strawberry(berry, leaf, radius=0.15)
    P.move(sb, dx=0.17, dy=0.1, dz=PH - 0.02, tilt=(math.radians(10), math.radians(16)))
    top += sb
    dx, dy, rz = OFFSETS[-1]
    P.move(top, dx=dx, dy=dy, dz=z, rot_z=rz)
    parts += top
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.9, -1.0, 0.55), (0.3, -0.6, 1.3)),
                          bg="#f4eee6", ground="#efe6da", margin=1.05)
    sys.exit(0 if ok else 1)
