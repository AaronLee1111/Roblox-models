"""Golden Macaron (premium): an oversized cream-and-gold macaron with a thick
golden filling, a beaded gold border around the dome and a small
crown (pearl tips, ruby), presented on a gold-rimmed cream pedestal
with sparkle stars. Gold is a flat warm yellow, never metallic."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import premium_parts as Q  # noqa: E402
import build_macaron as M  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402

NAME = "GoldenMacaron"
M.R, M.H, M.F = 0.5, 0.24, 0.2          # oversized, extra-thick filling
PED_TOP = 0.36


def dome_z(r):
    """Height of the top shell's dome above its base at radius r."""
    rows = [(rf, zf) for rf, zf, foot in M.SHELL if not foot and rf <= 1.0][:6]
    rs, zs = zip(*sorted(rows))
    return float(np.interp(r / M.R, rs, zs)) * M.H


def build_pedestal(cream, gold):
    prof = [(0.0, 0.0), (0.32, 0.0), (0.34, 0.02), (0.3, 0.05), (0.14, 0.09), (0.09, 0.14),
            (0.09, 0.24), (0.16, 0.28), (0.62, 0.31), (0.7, 0.335), (0.72, PED_TOP), (0.69, PED_TOP + 0.012),
            (0.6, PED_TOP - 0.005), (0.0, PED_TOP - 0.005)]
    return Q.lathe_multi("Pedestal", prof, [cream, gold],
                         lambda c: 1 if (abs(c.x) ** 2 + abs(c.y) ** 2) ** 0.5 > 0.66 or c.z < 0.03 else 0,
                         segments=48)


def build_crown(gold, pearl, gem_mat):
    parts = []
    rb, hb = 0.16, 0.085
    band = P.lathe("CrownBand", [(rb - 0.02, 0.0), (rb, 0.0), (rb + 0.01, hb * 0.5), (rb, hb),
                                 (rb - 0.02, hb), (rb - 0.02, 0.0)], gold, segments=24)
    parts.append(band)
    for i in range(5):
        a = 2 * math.pi * i / 5 + math.pi / 2
        cb = bmesh.new()
        bmesh.ops.create_cone(cb, cap_ends=True, segments=6, radius1=0.055, radius2=0.0, depth=0.13)
        bmesh.ops.scale(cb, vec=(1.0, 0.55, 1.0), verts=cb.verts)           # flat, blade-like point
        spike = L.obj_from_bm("CrownPoint", cb, gold)
        spike.location = (rb * math.cos(a), rb * math.sin(a), hb + 0.055)
        spike.rotation_euler = (0, 0, a + math.pi / 2)
        parts.append(spike)
        b = Q.pearl("CrownPearl", pearl, r=0.034)
        b.location = (rb * math.cos(a), rb * math.sin(a), hb + 0.13)
        parts.append(b)
    g = Q.gem("CrownGem", gem_mat, r=0.055)
    g.rotation_euler = (math.radians(90), 0, 0)                            # table faces -Y (front)
    g.location = (0, -rb - 0.012, hb * 0.5)
    parts.append(g)
    return parts


def build(out_dir):
    shell = L.make_material("ShellCream", M.shell_texture(out_dir, "ShellCream_Color", "#ffefd2", "#fff8ea"),
                            roughness=0.55, specular=0.25)
    filling = L.make_material("GoldFilling", L.solid_image("GoldFilling_Color", "#f2a53a", out_dir),
                              roughness=0.55, specular=0.25)
    gold = L.make_material("Gold", L.solid_image("Gold_Color", Q.GOLD, out_dir), roughness=0.45, specular=0.4)
    cream = L.make_material("Pedestal", L.solid_image("Pedestal_Color", "#fffaf0", out_dir),
                            roughness=0.4, specular=0.35)
    pearl = L.make_material("Pearl", Q.pearl_texture(out_dir), roughness=0.3, specular=0.5)
    ruby = L.make_material("Ruby", L.solid_image("Ruby_Color", "#e0265e", out_dir), roughness=0.25, specular=0.5)

    parts = [build_pedestal(cream, gold)]
    mac = M.build_macaron(shell, filling)
    P.move(mac, dz=PED_TOP - 0.005)
    parts += mac
    top_base = mac[2].location.z                 # top shell base (after move)

    # Beaded gold border around the dome: clean, readable, and 'patisserie premium'.
    ring_r = M.R * 0.74
    for i in range(14):
        t = 2 * math.pi * i / 14
        x, y = ring_r * math.cos(t), ring_r * math.sin(t)
        bead = L.obj_from_bm("GoldBead", L.uvsphere_bm(u=10, v=6, radius=0.035), gold)
        bead.location = (x, y, top_base + dome_z(ring_r) + 0.022)
        parts.append(bead)

    crown = build_crown(gold, pearl, ruby)
    P.move(crown, dz=top_base + M.H - 0.035, rot_z=math.radians(-20), tilt=(math.radians(-6), 0.0))
    parts += crown

    # Sparkle stars on the pedestal rim.
    for k, (a, s) in enumerate(((math.radians(-60), 0.09), (math.radians(-125), 0.065))):
        st = Q.rounded_extrude("Sparkle", Q.star_outline(s, r_in=0.35, points=4), 0.03, gold,
                               round_frac=0.3, steps=1)
        st.location = (0.6 * math.cos(a), 0.6 * math.sin(a), PED_TOP - 0.01)
        st.rotation_euler = (0, 0, 0.3 * k)
        parts.append(st)
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.45, -1.0, 0.65), (0.2, -0.5, 1.3)),
                          bg="#f4eee6", ground="#efe6da", margin=0.95)
    sys.exit(0 if ok else 1)
