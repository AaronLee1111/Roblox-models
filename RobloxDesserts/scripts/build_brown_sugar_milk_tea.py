"""Brown Sugar Milk Tea: chunky clear cup (one semi-transparent material),
opaque milk-tea body painted with brown-sugar 'tiger stripes', big tapioca
pearls pressed against the wall so they read, a sealed lid and a wide straw.

The pearls sit partly outside the liquid surface, so they still show even if
the cup renders opaque in Roblox."""
import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

NAME = "BrownSugarMilkTea"
SEG = 40
CUP_H = 1.3
LIQ_TOP = 1.14
PEARL_R = 0.09
LIQ_INSET = 0.065      # liquid sits this far inside the glass...
PEARL_INSET = 0.1      # ...pearl centres further in: they bulge out of the liquid but stay inside the glass
CUP = [(0.0, 0.0), (0.31, 0.0), (0.34, 0.03), (0.36, 0.2), (0.4, 0.7), (0.43, 1.15),
       (0.445, CUP_H - 0.03), (0.46, CUP_H)]


def cup_radius(z):
    rs, zs = zip(*[(r, zz) for r, zz in CUP if r > 0])
    return float(np.interp(z, zs, rs))


def glass_material(out_dir):
    """Clear pale-blue glass: alpha lives in the texture so Roblox's importer sees it."""
    img = bpy.data.images.new("CupGlass_Color", 4, 4, alpha=True)
    px = np.tile(np.array([1.0, 0.99, 0.96, 0.18], dtype=np.float32), 16)
    img.pixels.foreach_set(px)
    path = os.path.join(out_dir, "textures", "CupGlass_Color.png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    img.filepath = path
    img.pack()
    mat = L.make_material("CupGlass", img, roughness=0.1, specular=0.5)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tex = next(n for n in nodes if n.type == "TEX_IMAGE")
    links.new(tex.outputs["Alpha"], nodes["Principled BSDF"].inputs["Alpha"])
    mat.surface_render_method = "BLENDED"
    return mat


def tea_texture(out_dir):
    """u = angle, v = height/LIQ_TOP. Milk tea with wavy dark syrup streaks,
    heaviest near the bottom and thinning as they climb the wall."""
    w = h = 1024                                              # drawn at 2x, downsampled below
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    tea = np.array(L.srgb("#e8c197"))
    syrup = np.array(L.srgb("#7a3a14"))
    rgb = np.broadcast_to(tea, (h, w, 3)).copy()
    for k in range(7):
        uc = (k + 0.3 * math.sin(k * 2.1)) / 7
        top = 0.55 + 0.3 * ((k * 37) % 7) / 7
        wave = uc + 0.035 * np.sin(2 * np.pi * (V * 2.2 + k * 0.4))
        du = np.minimum(np.abs(U - wave), 1 - np.abs(U - wave))
        width = 0.045 * np.clip(1 - V / top, 0, 1) ** 0.6
        rgb[(du < width) & (V < top)] = syrup
    rgb[V < 0.08] = syrup                                     # syrup pooled at the bottom
    rgb = rgb.reshape(h // 2, 2, w // 2, 2, 3).mean(axis=(1, 3))
    return L.image_from_array("MilkTea_Color", rgb, out_dir)


def build(out_dir):
    glass = glass_material(out_dir)
    tea = L.make_material("MilkTea", tea_texture(out_dir), roughness=0.6, specular=0.25)
    pearl = L.make_material("TapiocaPearl", L.solid_image("TapiocaPearl_Color", "#3b2016", out_dir),
                            roughness=0.2, specular=0.6)
    lid = L.make_material("Lid", L.solid_image("Lid_Color", "#fff6ec", out_dir), roughness=0.5, specular=0.3)
    straw = L.make_material("Straw", L.solid_image("Straw_Color", "#ff9fbd", out_dir), roughness=0.45,
                            specular=0.3)

    parts = [P.lathe("Cup", CUP, glass, segments=SEG)]
    liq = [(0.0, 0.02)] + [(cup_radius(z) - LIQ_INSET, z) for z in np.linspace(0.03, LIQ_TOP, 10)] + [(0.0, LIQ_TOP)]
    body = P.lathe("Tea", liq, tea, segments=SEG)
    me = body.data
    uv = me.uv_layers.active.data
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        uv[loop.index].uv = ((math.atan2(co.y, co.x) / (2 * math.pi)) % 1.0, co.z / LIQ_TOP)
    parts.append(body)

    # Pearls: a full bottom layer plus a scattered second layer, all against the wall.
    rng = np.random.default_rng(4)
    for layer, (count, z) in enumerate(((10, 0.11), (9, 0.28), (5, 0.45))):
        for i in range(count):
            a = 2 * math.pi * (i + 0.5 * layer + rng.uniform(-0.15, 0.15)) / count
            zz = z + rng.uniform(-0.02, 0.02)
            r = cup_radius(zz) - PEARL_INSET
            p = L.obj_from_bm("Pearl", L.uvsphere_bm(u=14, v=8, radius=PEARL_R), pearl)
            p.location = (r * math.cos(a), r * math.sin(a), zz)
            parts.append(p)

    # Sealed lid with a soft rolled edge.
    rt = cup_radius(CUP_H)
    lid_obj = P.lathe("Lid", [(0.0, CUP_H + 0.025), (rt - 0.03, CUP_H + 0.02), (rt + 0.015, CUP_H + 0.005),
                              (rt + 0.02, CUP_H - 0.02), (rt - 0.02, CUP_H - 0.025), (0.0, CUP_H - 0.02)],
                      lid, segments=SEG)
    parts.append(lid_obj)

    # Wide straw: from near the bottom, out through the lid, tilted, angle-cut look via a cap.
    base = Vector((0.08, 0.05, 0.12))
    tip = Vector((-0.12, 0.16, CUP_H + 0.5))
    path = [base.lerp(tip, t) for t in np.linspace(0, 1, 6)]
    parts.append(P.tube("Straw", path, [0.075] * len(path), straw, ring_n=16, caps=True))
    return parts


def glb_alpha_modes(path):
    with open(path, "rb") as f:
        data = f.read()
    length = struct.unpack_from("<I", data, 12)[0]
    doc = json.loads(data[20:20 + length])
    return {m["name"]: m.get("alphaMode", "OPAQUE") for m in doc.get("materials", [])}


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.7, -1.0, 0.45), (0.2, -0.6, 1.2)),
                          bg="#f4eee6", ground="#efe6da", margin=1.0)
    modes = glb_alpha_modes(os.path.join(L.ROOT, NAME, f"{NAME}.glb"))
    print("ALPHA", modes)
    ok = ok and modes.get("CupGlass") == "BLEND"
    sys.exit(0 if ok else 1)
