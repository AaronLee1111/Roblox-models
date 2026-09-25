"""Shared crepe-family pieces: one lacy golden crepe texture, a layered folded
crepe (the Matcha Crepe Cake's layered wedge loft, re-proportioned as a
quarter-folded crepe) and a ruffled crepe cone (lathe with a wavy rim)."""
import math

import dessert_lib as L
import cafe_parts as P
import build_souffle_pancakes as S
import numpy as np

PLATE_TOP = S.PLATE_TOP


def crepe_texture(out_dir, name="Crepe_Color", n=256, spots=60):
    """Soft golden crepe with a lace of darker toasted spots."""
    U, V = np.meshgrid((np.arange(n) + 0.5) / n, (np.arange(n) + 0.5) / n)
    rgb = np.broadcast_to(np.array(L.srgb("#f6d696")), (n, n, 3)).copy()
    rng = np.random.default_rng(17)
    toast = np.array(L.srgb("#dca25a"))
    for _ in range(spots):
        cx, cy, r = rng.uniform(0, 1, 2).tolist() + [rng.uniform(0.02, 0.05)]
        dx = np.minimum(np.abs(U - cx), 1 - np.abs(U - cx))
        dy = np.minimum(np.abs(V - cy), 1 - np.abs(V - cy))
        m = np.clip((r - np.hypot(dx, dy)) / 0.004, 0, 1)[..., None] * 0.6
        rgb = rgb + (toast - rgb) * m
    return L.image_from_array(name, rgb, out_dir)


def crepe_mat(out_dir):
    return L.make_material("Crepe", crepe_texture(out_dir), roughness=0.7, specular=0.2)


def layered_edge_mat(out_dir, fill_hex="#fff5dc", layers=4, seam=0.1):
    """Folded edge: crepe layers with a thin filling line between them (crepe-cake style)."""
    h = 256
    v = (np.arange(h) + 0.5) / h
    phase = (v * layers) % 1.0
    band = ((phase < seam) | (phase > 1 - seam)) & (v > 0.05) & (v < 0.95)
    rgb = np.where(band[:, None], np.array(L.srgb(fill_hex)), np.array(L.srgb("#eab86c")))[:, None, :].repeat(8, 1)
    return L.make_material("CrepeEdge", L.image_from_array("CrepeEdge_Color", rgb, out_dir), roughness=0.7,
                           specular=0.2)


def folded_crepe(top_mat, edge_mat, R=0.72, angle=78, layers=4, layer_h=0.045):
    """Quarter-folded crepe: layered wedge (crepe-cake loft) with puffy layer bulges."""
    outline = P.wedge_outline(R, angle, tip=0.1, arc_steps=14)
    H = layers * layer_h
    rings = [(0.0, 0.02)]
    for i in range(layers):
        z0 = i * layer_h
        if i:
            rings.append((z0, 0.012))
        rings.append((z0 + layer_h / 2, 0.0))
    rings.append((H, 0.02))
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]

    def uv_fn(co):
        if co.z > H - 1e-4 or co.z < 1e-4:
            return ((co.x - min(xs)) / (max(xs) - min(xs)), (co.y - min(ys)) / (max(ys) - min(ys)))
        return (0.5, min(max(co.z / H, 0.0), 0.995))

    return P.loft("FoldedCrepe", outline, rings, [top_mat, edge_mat],
                  lambda c, kind: 0 if kind in ("top", "bottom") else 1, uv_fn=uv_fn), H


def crepe_cone(mat, r_top=0.33, h=0.8, ruffles=7, amp=0.03, wall=0.025, seg=56):
    """Harajuku crepe cone: apex down, ruffled open rim at the top (thin double wall)."""
    prof = [(0.0, 0.0), (0.05, 0.03)]
    for t in np.linspace(0.1, 1.0, 12):
        prof.append((0.05 + (r_top - 0.05) * t ** 0.9, h * t))
    prof += [(r_top - wall, h - 0.01)]
    for t in np.linspace(1.0, 0.1, 6):
        prof.append((max(0.04, 0.05 + (r_top - 0.05) * t ** 0.9 - wall), h * t))
    obj = P.lathe("CrepeCone", prof, mat, segments=seg)
    for v in obj.data.vertices:                          # ruffle the rim (fades out toward the apex)
        r = math.hypot(v.co.x, v.co.y)
        if r < 1e-6:
            continue
        a = math.atan2(v.co.y, v.co.x)
        k = 1 + (amp / max(r, 0.05)) * math.sin(ruffles * a) * (v.co.z / h) ** 3
        v.co.x *= k
        v.co.y *= k
    me = obj.data
    uv = me.uv_layers.active.data
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        uv[loop.index].uv = ((math.atan2(co.y, co.x) / (2 * math.pi)) % 1.0, co.z / h)
    return obj


def render(name, build, views=((0.8, -1.0, 0.6), (0.2, -0.5, 1.3)), margin=1.0):
    return L.build_and_ship(name, build, views=views, bg="#f4eee6", ground="#efe6da", margin=margin)
