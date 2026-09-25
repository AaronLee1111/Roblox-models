"""Croffle: croissant dough pressed in a waffle iron. Chunky crescent with tapered horns,
golden-brown with real waffle ridges, layered croissant edges, powdered sugar,
a cream dollop and blueberries, on the café plate. Stylized Roblox look.

The body is one closed surface built on a grid aligned to the waffle pockets,
so ridges are real geometry without a dense mesh."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402

NAME = "Croffle"
LEN, WID = 1.35, 0.78      # studs
HALF_T = 0.155             # half thickness at the centre
NX, NY = 5, 3              # waffle pockets
DEPTH = 0.05               # pocket depth
CELL = [0.0, 0.14, 0.3, 0.7, 0.86]   # grid lines inside each pocket cell
SQ = 4.0                   # superellipse exponent of the outline (rounded rectangle)
BEND = 0.16                # crescent bend (studs at the tips)
ARCH = 0.05                # ends droop by this much
TAPER = 0.45               # croissant taper toward the horn tips (0 = plain rounded rectangle)
HORN = 0.35                # how much thinner the tips get
BODY_NAME = "Croffle"


def pocket_frac(p):
    """0 on a ridge, 1 on a pocket floor, linear on the slopes (p = position in cell)."""
    p = np.asarray(p, float)
    up = np.clip((p - 0.14) / 0.16, 0, 1)
    down = np.clip((0.86 - p) / 0.16, 0, 1)
    return np.minimum(up, down)


def axis_values(n):
    vals = [(-1 + 2 * (c + p) / n) for c in range(n) for p in CELL] + [1.0]
    vals += [-0.985, -0.955, 0.955, 0.985]           # extra rows to round the edge
    return sorted(set(round(v, 6) for v in vals))


def local(v, n):
    g = (v + 1) / 2 * n
    return g - min(math.floor(g), n - 1)


def superellipse_map(u, v):
    m = max(abs(u), abs(v))
    if m == 0:
        return 0.0, 0.0, 0.0
    s = (abs(u) ** SQ + abs(v) ** SQ) ** (1 / SQ)
    k = m / s
    return u * k, v * k, m          # m = "radius" in the square param (1 on the boundary)


def place(u, v, side):
    """Param (u, v) on top (+1) or bottom (-1) surface -> 3D point."""
    uu, vv, m = superellipse_map(u, v)
    x = uu * LEN / 2
    y = vv * WID / 2 * (1 - TAPER * uu ** 4)         # croissant taper toward the horn tips
    rim = (1 - min(m, 1.0) ** 6) ** 0.35
    dome = 0.05 * (1 - m ** 2)
    horn = 1 - HORN * uu ** 4                        # tips are thinner too
    z = side * (HALF_T * horn * rim + dome * (1 if side > 0 else 0.4))
    pocket = float(min(pocket_frac(local(u, NX)), pocket_frac(local(v, NY))))
    z -= side * DEPTH * pocket * (1 - m ** 8) * (1.0 if side > 0 else 0.6)
    y += BEND * uu ** 2                               # crescent curve
    z -= ARCH * uu ** 2                               # ends droop slightly
    return (x, y, z), m


def waffle_texture(out_dir, name="Croffle_Color", sugar_dots=170, ridge_hex="#b8692b", floor_hex="#ebb05c",
                   fill=None, drizzle=None):
    """fill(ix, iy) -> hex or None: colours the floor of individual pockets
    (syrup / sauce pooled in the waffle holes).
    drizzle = (hex, width, [(u, v), ...]): a sauce line painted over the top in
    param space (u, v in [-1, 1]), so it hugs every ridge and pocket."""
    n = 512
    a = (np.arange(n) + 0.5) / n
    A, B = np.meshgrid(a, a)                          # A -> u, B -> v (rows = v)
    fx = pocket_frac((A * NX) % 1.0)
    fy = pocket_frac((B * NY) % 1.0)
    pocket = np.minimum(fx, fy)[..., None]
    ridge = np.array(L.srgb(ridge_hex))
    floor = np.array(L.srgb(floor_hex))
    rgb = ridge + (floor - ridge) * pocket
    if fill:
        ix = np.minimum((A * NX).astype(int), NX - 1)
        iy = np.minimum((B * NY).astype(int), NY - 1)
        deep = np.minimum(pocket_frac((A * NX) % 1.0 * 0.8 + 0.1), pocket_frac((B * NY) % 1.0 * 0.8 + 0.1)) > 0.99
        for i in range(NX):
            for j in range(NY):
                c = fill(i, j)
                if c:
                    rgb[(ix == i) & (iy == j) & deep] = L.srgb(c)
                    # Painted glint so pooled syrup reads as glossy liquid, not a hole.
                    lx, ly = (A * NX) % 1.0, (B * NY) % 1.0
                    glint = (ix == i) & (iy == j) & (np.hypot((lx - 0.36) / 0.09, (ly - 0.64) / 0.05) < 1)
                    rgb[glint] = rgb[glint] * 0.3 + 0.7
    # Bold powdered-sugar dusting in a diagonal band.
    rng = np.random.default_rng(5)
    sugar = np.zeros((n, n))
    yy, xx = np.mgrid[0:n, 0:n]
    # Dusting: many small-to-medium dots, densest on the side away from the cream.
    for _ in range(sugar_dots):
        cx = rng.uniform(0.05, 0.62) * n
        cy = rng.uniform(0.1, 0.9) * n
        rad = rng.uniform(4, 9)
        sugar = np.maximum(sugar, np.clip((rad - np.hypot(xx - cx, yy - cy)) / 1.5, 0, 1))
    rgb = rgb + (np.array(L.srgb("#fffaf3")) - rgb) * (sugar * 0.9)[..., None]
    if drizzle:
        hexc, width, pts = drizzle
        pts = [((u + 1) / 2, (v + 1) / 2) for u, v in P.chaikin(pts, 3, closed=False)]
        d = np.full(A.shape, 9.0)
        for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
            ex, ey = u1 - u0, v1 - v0
            t = np.clip(((A - u0) * ex + (B - v0) * ey) / (ex * ex + ey * ey + 1e-12), 0, 1)
            d = np.minimum(d, np.hypot(A - u0 - t * ex, B - v0 - t * ey))
        rgb[d < width] = L.srgb(hexc)
    return L.image_from_array(name, rgb, out_dir)


def edge_texture(out_dir):
    """Flaky croissant layers on the rim: v = height."""
    h = 128
    v = (np.arange(h) + 0.5) / h
    light = np.array(L.srgb("#f3c67e"))
    dark = np.array(L.srgb("#c9803a"))
    stripe = ((v * 5) % 1.0) < 0.5
    rgb = np.where(stripe[:, None], light, dark)[:, None, :].repeat(8, axis=1)
    return L.image_from_array("CroffleEdge_Color", rgb, out_dir)


def build_body(top_mat, edge_mat):
    us, vs = axis_values(NX), axis_values(NY)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    top, bot, rad = {}, {}, {}
    for i, u in enumerate(us):
        for j, v in enumerate(vs):
            co, m = place(u, v, +1)
            vt = bm.verts.new(co)
            top[i, j] = vt
            rad[vt] = m
            on_edge = i in (0, len(us) - 1) or j in (0, len(vs) - 1)
            if on_edge:
                bot[i, j] = vt                    # top and bottom share the rim
            else:
                vb = bm.verts.new(place(u, v, -1)[0])
                bot[i, j] = vb
                rad[vb] = m
    param = {}
    for (i, j), vt in top.items():
        param[vt] = ((us[i] + 1) / 2, (vs[j] + 1) / 2)
    for (i, j), vb in bot.items():
        param.setdefault(vb, ((us[i] + 1) / 2, (vs[j] + 1) / 2))
    zs = [vv.co.z for vv in bm.verts]
    z0, z1 = min(zs), max(zs)
    for i in range(len(us) - 1):
        for j in range(len(vs) - 1):
            for grid, flip in ((top, False), (bot, True)):
                q = [grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]]
                if flip:
                    q.reverse()
                f = bm.faces.new(q)
                edge = min(rad[vv] for vv in q) > 0.95
                f.material_index = 1 if edge else 0
                for loop in f.loops:
                    co = loop.vert.co
                    if edge:
                        ang = math.atan2(co.y, co.x) / (2 * math.pi) + 0.5
                        loop[uv].uv = (ang, (co.z - z0) / (z1 - z0))
                    else:
                        loop[uv].uv = param[loop.vert]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return P.obj_from_bm_multi(BODY_NAME, bm, [top_mat, edge_mat])


def build(out_dir):
    # Refined croissant silhouette: stronger taper to pointed horns and a deeper curve.
    global TAPER, HORN, BEND, ARCH
    TAPER, HORN, BEND, ARCH = 0.78, 0.6, 0.3, 0.06
    top_mat = L.make_material("CroffleWaffle", waffle_texture(out_dir, sugar_dots=110), roughness=0.7,
                              specular=0.25)
    edge_mat = L.make_material("CroffleLayers", edge_texture(out_dir), roughness=0.75, specular=0.2)
    cream = L.make_material("Cream", L.solid_image("Cream_Color", "#fff8ef", out_dir),
                            roughness=0.7, specular=0.25)
    blue = L.make_material("Blueberry", L.solid_image("Blueberry_Color", "#6f78d8", out_dir),
                           roughness=0.5, specular=0.3)
    plate = L.make_material("Plate", L.solid_image("Plate_Color", "#fff3dd", out_dir), roughness=0.5, specular=0.3)

    body = build_body(top_mat, edge_mat)
    parts = [body]
    ux = 0.45
    (x, y, z), _ = place(ux, 0.0, +1)
    d = P.cream_dollop("Cream", cream, radius=0.18, height=0.25)
    d.location = (x, y, z - 0.03)
    parts.append(d)
    for k, (du, dv) in enumerate(((0.2, -0.45), (0.05, 0.5), (-0.18, -0.3))):
        (bx, by, bz), _ = place(ux + du, dv, +1)
        bb = L.uvsphere_bm(u=14, v=8, radius=0.075)
        for vert in bb.verts:
            vert.co.z *= 0.9
        b = L.obj_from_bm("Blueberry", bb, blue)
        b.location = (bx, by, bz + 0.045)
        parts.append(b)
    # Present it on the waffle/pancake family's café plate, centred.
    import build_souffle_pancakes as S
    P.move(parts, dy=-BEND * 0.5, dz=S.PLATE_TOP + HALF_T * 0.85 + ARCH)
    return [S.build_plate(plate)] + parts


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.5, -1.0, 0.8), (0.1, -0.35, 1.2)),
                          bg="#f4eee6", ground="#efe6da", margin=1.05)
    sys.exit(0 if ok else 1)
