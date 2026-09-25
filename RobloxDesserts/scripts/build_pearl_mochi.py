"""Pearl Mochi (premium): a pyramid of four satin mochi (cream, lilac, pale pink)
each crowned with a pearl and gold-leaf flake, on a jewel-amethyst lacquer tray
with a gold rim and a draped pearl strand."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import premium_parts as Q  # noqa: E402
import numpy as np  # noqa: E402

NAME = "PearlMochi"
TRAY_W, TRAY_D, TRAY_T, CORNER = 1.9, 1.2, 0.1, 0.32
MOCHI_R = 0.3


def rounded_rect(w, d, rad, steps=6):
    pts = []
    for cx, cy, a0 in ((w / 2 - rad, -d / 2 + rad, -90), (w / 2 - rad, d / 2 - rad, 0),
                       (-w / 2 + rad, d / 2 - rad, 90), (-w / 2 + rad, -d / 2 + rad, 180)):
        for k in range(steps + 1):
            a = math.radians(a0 + 90 * k / steps)
            pts.append(np.array((cx + rad * math.cos(a), cy + rad * math.sin(a))))
    return pts


def build(out_dir):
    mats = {
        "cream": L.make_material("Mochi_Cream", Q.shine_texture("Mochi_Cream_Color", "#fff3dc", out_dir,
                                                                shade_hex="#f3dcbc"), roughness=0.4, specular=0.35),
        "lilac": L.make_material("Mochi_Lilac", Q.shine_texture("Mochi_Lilac_Color", "#d4c0f5", out_dir,
                                                                shade_hex="#b9a0ea"), roughness=0.4, specular=0.35),
        "pink": L.make_material("Mochi_Pink", Q.shine_texture("Mochi_Pink_Color", "#ffc9da", out_dir,
                                                              shade_hex="#f7a9c3"), roughness=0.4, specular=0.35),
    }
    pearl = L.make_material("Pearl", Q.pearl_texture(out_dir), roughness=0.3, specular=0.5)
    gold = L.make_material("Gold", L.solid_image("Gold_Color", Q.GOLD, out_dir), roughness=0.45, specular=0.4)
    tray = L.make_material("Tray", L.solid_image("Tray_Color", "#6a3a8f", out_dir), roughness=0.35, specular=0.4)

    parts = []
    outline = rounded_rect(TRAY_W, TRAY_D, CORNER)
    parts.append(Q.rounded_extrude("Tray", outline, TRAY_T, tray, round_frac=0.3, steps=2))
    rim = [np.array(p) for p in P.offset_outline(outline, 0.04)]
    parts.append(P.tube("TrayRim", [(p[0], p[1], TRAY_T + 0.005) for p in rim], [0.035] * len(rim), gold,
                        ring_n=8, closed=True))
    top = TRAY_T

    # Mochi pyramid, left of centre.
    cx = -0.35
    base = [("lilac", -90), ("pink", 30), ("cream", 150)]
    for color, ang in base:
        a = math.radians(ang)
        m = Q.mochi(f"Mochi_{color}", mats[color], r=MOCHI_R)
        m.location = (cx + 0.27 * math.cos(a), 0.27 * math.sin(a), top)
        parts.append(m)
    crown = Q.mochi("Mochi_top", mats["cream"], r=MOCHI_R * 0.92)
    crown.location = (cx, 0.0, top + 0.22)
    parts.append(crown)

    # Pearl + gold flake on each mochi.
    for m in parts[-4:]:
        is_top = m is crown
        pr = 0.085 if is_top else 0.065
        zt = m.location.z + (m.dimensions.z if m.dimensions.z else 0.35)
        b = Q.pearl("Pearl", pearl, r=pr)
        b.location = (m.location.x, m.location.y, zt + pr * 0.55)
        parts.append(b)
        f = Q.gold_flake("GoldFlake", gold, size=0.07, seed=int(m.location.x * 100) % 7)
        f.location = (m.location.x + 0.09, m.location.y - 0.04, zt - 0.03)
        f.rotation_euler = (math.radians(-12), math.radians(14), 0)
        parts.append(f)

    # Draped pearl necklace: a loose loop on the right, pearls alternating with
    # small gold beads, a larger drop pearl at the bottom of the loop.
    pr, gr = 0.06, 0.03
    cx2, cy2, rx, ry = 0.5, 0.02, 0.34, 0.4
    n = 22
    for i in range(n):
        t = 2 * math.pi * i / n
        wob = 1 + 0.08 * math.sin(3 * t)
        x, y = cx2 + rx * wob * math.cos(t), cy2 + ry * wob * math.sin(t)
        if i % 2 == 0:
            big = i == 16                          # bottom-front of the loop
            r = pr * (1.35 if big else 1.0)
            b = Q.pearl("StrandPearl", pearl, r=r)
            b.location = (x, y, top + r)
        else:
            b = L.obj_from_bm("GoldBead", L.uvsphere_bm(u=8, v=6, radius=gr), gold)
            b.location = (x, y, top + gr)
        parts.append(b)
    clasp = Q.gem("Clasp", gold, r=0.06)
    clasp.location = (cx2 + rx * 1.08, cy2, top + 0.045)
    parts.append(clasp)
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.55, -1.0, 0.75), (0.1, -0.45, 1.3)),
                          bg="#f4eee6", ground="#efe6da", margin=0.95)
    sys.exit(0 if ok else 1)
