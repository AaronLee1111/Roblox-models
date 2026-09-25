"""Moonlight Mochi (premium): three satin mochi (navy, lilac, cream) topped with a
gold crescent and stars, in front of a big standing crescent moon, on a deep
navy plate with a lilac rim and a painted star-sprinkle night sky."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import premium_parts as Q  # noqa: E402
import numpy as np  # noqa: E402

NAME = "MoonlightMochi"
PLATE_R = 0.82
PLATE_TOP = 0.07
MOCHI_R = 0.3


def plate_texture(out_dir):
    """Top-down: navy night sky with cream sparkles and dots, lilac rim band."""
    n = 1024
    a = (np.arange(n) + 0.5) / n * 2 - 1
    X, Y = np.meshgrid(a, a)
    r = np.hypot(X, Y)
    rgb = np.broadcast_to(np.array(L.srgb("#2c3566")), (n, n, 3)).copy()
    rgb[r > 0.84] = L.srgb("#b9a6ee")                              # lilac rim
    rgb[(r > 0.8) & (r <= 0.84)] = L.srgb("#ffe08a")               # thin gold line
    rng = np.random.default_rng(12)
    cream = np.array(L.srgb("#fff3d0"))
    for _ in range(26):                                            # 4-point sparkles
        cx, cy = rng.uniform(-0.72, 0.72, 2)
        if math.hypot(cx, cy) > 0.74:
            continue
        s = rng.uniform(0.025, 0.05)
        dx, dy = np.abs(X - cx) / s, np.abs(Y - cy) / s
        star = np.sqrt(dx) + np.sqrt(dy) < 1.0                     # astroid-shaped sparkle
        rgb[star] = cream
    for _ in range(40):                                            # tiny dots
        cx, cy = rng.uniform(-0.75, 0.75, 2)
        if math.hypot(cx, cy) > 0.76:
            continue
        rgb[np.hypot(X - cx, Y - cy) < 0.009] = cream
    rgb = rgb.reshape(n // 2, 2, n // 2, 2, 3).mean(axis=(1, 3))
    return L.image_from_array("NightPlate_Color", rgb, out_dir)


def build_plate(mat):
    R = PLATE_R
    prof = [(0.0, 0.0), (R * 0.55, 0.0), (R * 0.6, 0.02), (R * 0.9, 0.04), (R, 0.1), (R - 0.03, 0.115),
            (R * 0.88, 0.075), (R * 0.6, PLATE_TOP), (0.0, PLATE_TOP)]
    obj = P.lathe("Plate", prof, mat, segments=56)
    L.planar_uv(obj, 0, 1, (-R, R, -R, R))
    return obj


def stand_up(obj):
    """Rotate an XY-extruded motif to stand upright (in the XZ plane, facing -Y)."""
    obj.rotation_euler = (math.radians(90), 0, obj.rotation_euler.z)
    return obj


def build(out_dir):
    plate = L.make_material("NightPlate", plate_texture(out_dir), roughness=0.4, specular=0.35)
    mats = {
        "navy": L.make_material("Mochi_Navy", Q.shine_texture("Mochi_Navy_Color", "#4a5699", out_dir,
                                                              shade_hex="#353f78"), roughness=0.4, specular=0.35),
        "lilac": L.make_material("Mochi_Lilac", Q.shine_texture("Mochi_Lilac_Color", "#c9b6f3", out_dir,
                                                                shade_hex="#ad95e8"), roughness=0.4, specular=0.35),
        "cream": L.make_material("Mochi_Cream", Q.shine_texture("Mochi_Cream_Color", "#fff1d6", out_dir,
                                                                shade_hex="#f1d9b6"), roughness=0.4, specular=0.35),
    }
    moon = L.make_material("MoonGold", L.solid_image("MoonGold_Color", "#ffd96b", out_dir),
                           roughness=0.45, specular=0.35)

    parts = [build_plate(plate)]

    # Big crescent moon standing behind the mochi.
    big = Q.crescent("Moon", moon, R=0.38, width=0.48, flat=0.45)
    stand_up(big)
    big.rotation_euler.z = math.radians(-10)
    big.location = (0.02, 0.38, 0)
    Q.place_on(big, PLATE_TOP - 0.02)
    parts.append(big)

    # Three mochi in a gentle arc in front, each with an upright topper.
    layout = [("navy", (-0.36, -0.08), "crescent"), ("lilac", (0.0, -0.3), "star"),
              ("cream", (0.37, -0.06), "star")]
    for color, (x, y), topper in layout:
        m = Q.mochi(f"Mochi_{color}", mats[color], r=MOCHI_R)
        m.location = (x, y, PLATE_TOP)
        parts.append(m)
        top_z = PLATE_TOP + m.dimensions.z
        if topper == "crescent":
            t = Q.crescent("MiniMoon", moon, R=0.12, width=0.55, flat=0.55, steps=14, ring_n=8)
        else:
            t = Q.rounded_extrude("MiniStar", Q.star_outline(0.105, r_in=0.5), 0.045, moon,
                                  round_frac=0.4, steps=2)
        stand_up(t)
        t.rotation_euler.z = math.radians(15 if x > 0 else -15)
        t.location = (x, y, 0)
        Q.place_on(t, top_z - 0.04)
        parts.append(t)

    # A few little stars resting on the plate.
    for k, (x, y, s) in enumerate(((0.5, 0.36, 0.07), (-0.5, 0.34, 0.06), (0.22, -0.56, 0.055))):
        st = Q.rounded_extrude("PlateStar", Q.star_outline(s, r_in=0.5), 0.025, moon, round_frac=0.4, steps=1)
        st.location = (x, y, PLATE_TOP - 0.004)
        st.rotation_euler = (0, 0, 0.5 * k)
        parts.append(st)
    return parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.3, -1.0, 0.6), (0.1, -0.45, 1.3)),
                          bg="#f4eee6", ground="#efe6da", margin=0.95)
    sys.exit(0 if ok else 1)
