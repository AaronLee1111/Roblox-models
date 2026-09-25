"""Matcha Latte: rounded ceramic cup on a pastel saucer, matcha with a foam heart."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402

NAME = "MatchaLatte"
SEG = 48                 # radial segments for lathed parts
SAUCER_TOP = 0.075       # z of the saucer's inner floor, where the cup sits

# Lathe profiles (radius, z), traced outer bottom -> rim -> inner bottom.
CUP_OUTER = [(0.0, 0.0), (0.22, 0.0), (0.26, 0.015), (0.31, 0.09), (0.37, 0.24), (0.405, 0.4),
             (0.415, 0.54), (0.41, 0.66), (0.40, 0.73)]
CUP_RIM = [(0.393, 0.752), (0.378, 0.758), (0.365, 0.745)]
CUP_INNER = [(0.36, 0.7), (0.365, 0.56), (0.35, 0.4), (0.31, 0.25), (0.24, 0.13), (0.0, 0.11)]
SAUCER = [(0.0, 0.0), (0.26, 0.0), (0.28, 0.025), (0.34, 0.035), (0.56, 0.06), (0.68, 0.1),
          (0.715, 0.13), (0.705, 0.145), (0.665, 0.125), (0.55, 0.09), (0.36, SAUCER_TOP),
          (0.0, SAUCER_TOP)]
LIQUID_Z = 0.68


def lathe(name, profile, mat, z0=0.0, segments=SEG):
    bm = bmesh.new()
    verts = [bm.verts.new((r, 0, z + z0)) for r, z in profile]
    edges = [bm.edges.new((a, b)) for a, b in zip(verts, verts[1:])]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=2 * math.pi, steps=segments, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.obj_from_bm(name, bm, mat)


def outer_radius(z):
    rs, zs = zip(*[(r, zz) for r, zz in CUP_OUTER if r > 0])
    return float(np.interp(z, zs, rs))


def build_handle(mat, z0):
    """Chunky D-shaped loop whose ends sink into the cup wall."""
    bm = bmesh.new()
    steps, ring_n = 18, 10
    zc, hz, w = 0.44, 0.17, 0.2
    a_n, a_b = 0.036, 0.055           # tube half-size: across the loop / along Y
    path = []
    for i in range(steps + 1):
        t = -math.pi / 2 + math.pi * i / steps
        z = zc + hz * math.sin(t)
        x = outer_radius(z) - 0.02 + w * math.cos(t) ** 0.8
        path.append(np.array((x, 0.0, z)))
    rings = []
    for i, p in enumerate(path):
        tan = path[min(i + 1, steps)] - path[max(i - 1, 0)]
        tan /= np.linalg.norm(tan)
        nrm = np.cross(tan, (0, 1, 0))
        ring = []
        for j in range(ring_n):
            a = 2 * math.pi * j / ring_n
            co = p + nrm * a_n * math.cos(a) + np.array((0, 1, 0)) * a_b * math.sin(a)
            ring.append(bm.verts.new((co[0], co[1], co[2] + z0)))
        rings.append(ring)
    for r1, r2 in zip(rings, rings[1:]):
        for j in range(ring_n):
            k = (j + 1) % ring_n
            bm.faces.new((r1[j], r1[k], r2[k], r2[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.obj_from_bm("Handle", bm, mat)


def foam_texture(out_dir):
    n = 1024  # rendered at 2x then box-downsampled for clean anti-aliased edges
    u = (np.arange(n) + 0.5) / n * 2 - 1
    X, Y = np.meshgrid(u, u)
    r = np.hypot(X, Y)
    matcha = np.array(L.srgb("#9fc46a"))
    matcha_light = np.array(L.srgb("#bcd88d"))
    foam = np.array(L.srgb("#fbf6e9"))
    rgb = np.broadcast_to(matcha, (n, n, 3)).copy()
    # Lighter microfoam ring near the cup wall.
    ring = np.clip((r - 0.8) / 0.12, 0, 1)[..., None]
    rgb = rgb + (np.array(L.srgb("#e6eccb")) - rgb) * ring
    rgb = rgb + (matcha_light - rgb) * np.clip((r - 0.62) / 0.2, 0, 1)[..., None] * (1 - ring) * 0.6
    # Latte-art heart (implicit curve), point toward -Y (towards the viewer).
    hx, hy = X / 0.5, (Y - 0.08) / 0.5
    heart = (hx ** 2 + hy ** 2 - 1) ** 3 - hx ** 2 * hy ** 3 <= 0
    rgb[heart] = foam
    # Pulled-through stem line typical of a poured heart.
    stem = (np.abs(X) < 0.022 * (1 + Y)) & (Y < -0.3) & (Y > -0.78)
    rgb[stem] = foam
    rgb = rgb.reshape(n // 2, 2, n // 2, 2, 3).mean(axis=(1, 3))
    return L.image_from_array("Matcha_Foam_Color", rgb, out_dir)


def cup_texture(out_dir):
    """Vertical strip mapped by height: cream glaze with a pastel pink band."""
    h = 128
    z = (np.arange(h) + 0.5) / h
    cream = np.array(L.srgb("#f7efe3"))
    pink = np.array(L.srgb("#f2b8c3"))
    band = ((z > 0.72) & (z < 0.8)) | ((z > 0.83) & (z < 0.85))
    rgb = np.where(band[:, None], pink, cream)[:, None, :].repeat(8, axis=1)
    return L.image_from_array("Cup_Color", rgb, out_dir)


def build_foam(mat, z0):
    """Slightly domed disc sitting inside the cup."""
    bm = bmesh.new()
    rad = float(np.interp(LIQUID_Z, [z for _, z in CUP_INNER[::-1]], [r for r, _ in CUP_INNER[::-1]])) + 0.008
    rings = 6
    center = bm.verts.new((0, 0, LIQUID_Z + 0.02 + z0))
    prev = None
    for i in range(1, rings + 1):
        rr = rad * i / rings
        dz = 0.02 * (1 - (i / rings) ** 2)
        ring = [bm.verts.new((rr * math.cos(2 * math.pi * j / SEG), rr * math.sin(2 * math.pi * j / SEG),
                              LIQUID_Z + dz + z0)) for j in range(SEG)]
        for j in range(SEG):
            k = (j + 1) % SEG
            if prev is None:
                bm.faces.new((center, ring[j], ring[k]))
            else:
                bm.faces.new((prev[j], ring[j], ring[k], prev[k]))
        prev = ring
    obj = L.obj_from_bm("Foam", bm, mat)
    L.planar_uv(obj, 0, 1, (-rad, rad, -rad, rad))
    return obj


def build(out_dir):
    cup_mat = L.make_material("Cup_Ceramic", cup_texture(out_dir),
                              roughness=0.25, specular=0.5, clearcoat=0.4)
    saucer_mat = L.make_material("Saucer_Ceramic", L.solid_image("Saucer_Color", "#f2c4cc", out_dir),
                                 roughness=0.25, specular=0.5, clearcoat=0.4)
    foam_mat = L.make_material("Matcha_Foam", foam_texture(out_dir), roughness=0.55, specular=0.3)

    saucer = lathe("Saucer", SAUCER, saucer_mat)
    cup = lathe("Cup", CUP_OUTER + CUP_RIM + CUP_INNER, cup_mat, z0=SAUCER_TOP)
    cup_h = max(z for _, z in CUP_RIM)
    L.planar_uv(cup, 0, 2, (-1, 1, SAUCER_TOP, SAUCER_TOP + cup_h))
    handle = build_handle(cup_mat, SAUCER_TOP)
    L.planar_uv(handle, 0, 2, (-1, 1, -10, 10))  # v ~ 0.5 everywhere -> plain cream, below the band
    foam = build_foam(foam_mat, SAUCER_TOP)
    return [saucer, cup, handle, foam]


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.8, -1.0, 0.8), (0.3, -0.5, 1.6)),
                          bg="#f4eee6", ground="#efe6da", margin=1.05)
    sys.exit(0 if ok else 1)
