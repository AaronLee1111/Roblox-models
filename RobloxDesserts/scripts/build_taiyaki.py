"""Taiyaki: puffy, golden fish-shaped pastry lying on its side.

The body is lofted from cross-section rings along the fish's length (X), with
the side profile in Y and the puffy thickness in Z (up). The waffle / scale
pattern is painted into a planar texture with a fake emboss so it reads
without adding tiny geometry.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402

NAME = "Taiyaki"
LENGTH = 1.7
RINGS = 56
SEGMENTS = 32
TEX = 512

# Side profile control points: s (0 = nose, 1 = tail tip) -> upper / lower edge (studs).
TOP = [(0, 0.0), (0.02, 0.16), (0.08, 0.30), (0.18, 0.40), (0.32, 0.44), (0.42, 0.47),
       (0.52, 0.45), (0.62, 0.32), (0.72, 0.17), (0.78, 0.16), (0.88, 0.30), (0.96, 0.40), (1.0, 0.42)]
BOT = [(0, 0.0), (0.02, 0.15), (0.08, 0.28), (0.18, 0.37), (0.32, 0.40), (0.46, 0.40),
       (0.56, 0.37), (0.64, 0.28), (0.72, 0.17), (0.78, 0.16), (0.88, 0.30), (0.96, 0.40), (1.0, 0.42)]
# Half thickness: puffy body, thinner tail.
THICK = [(0, 0.0), (0.03, 0.10), (0.12, 0.16), (0.35, 0.18), (0.58, 0.15), (0.72, 0.10),
         (0.85, 0.085), (0.96, 0.065), (1.0, 0.0)]


_GRID = np.linspace(0, 1, 2001)
_CACHE = {}


def curve(points, s):
    """Smooth curve through control points: dense linear interpolation, then a
    Gaussian blur (endpoints pinned) so the outline has no kinks or plateaus."""
    key = id(points)
    if key not in _CACHE:
        xs, ys = zip(*points)
        dense = np.interp(_GRID, xs, ys)
        sigma = 0.025 * (len(_GRID) - 1)
        k = np.exp(-0.5 * (np.arange(-4 * sigma, 4 * sigma + 1) / sigma) ** 2)
        k /= k.sum()
        pad = len(k) // 2
        padded = np.concatenate([2 * dense[0] - dense[pad:0:-1], dense, 2 * dense[-1] - dense[-2:-pad - 2:-1]])
        smooth = np.convolve(padded, k, "valid")
        # Blend back to exact endpoints (nose / tail tip must stay at zero thickness).
        w = np.clip(np.minimum(_GRID, 1 - _GRID) / 0.02, 0, 1)
        _CACHE[key] = dense * (1 - w) + smooth * w
    return np.interp(np.clip(s, 0, 1), _GRID, _CACHE[key])


def profile(s):
    top, bot = curve(TOP, s), curve(BOT, s)
    return (top - bot) / 2, (top + bot) / 2  # centre offset, half height


def tail_notch(s, ny):
    """Pull the middle of the tail back to form a soft fork."""
    w = np.clip((s - 0.86) / 0.14, 0, 1) ** 2
    return -0.13 * w * (1 - ny ** 2)


# ----------------------------------------------------------------- texture

def pastry_texture(out_dir, bounds):
    x0, x1, y0, y1 = bounds
    u = (np.arange(TEX) + 0.5) / TEX
    X, Y = np.meshgrid(x0 + u * (x1 - x0), y0 + u * (y1 - y0))   # rows = V (bottom->top)
    s = X / LENGTH + 0.5
    c, h = profile(s)
    ny = (Y - c) / np.maximum(h, 1e-3)
    edge = np.abs(ny)

    gold = np.array(L.srgb("#cc8a3e"))
    light = np.array(L.srgb("#e4ab5f"))
    toast = np.array(L.srgb("#94541f"))
    line_dark = np.array(L.srgb("#94501d"))
    line_hi = np.array(L.srgb("#f6c983"))

    rgb = np.broadcast_to(gold, (TEX, TEX, 3)).copy()
    puff = np.clip(1 - edge, 0, 1)[..., None] * np.clip(1 - np.abs(s - 0.35) / 0.4, 0, 1)[..., None]
    rgb = rgb + (light - rgb) * puff * 0.7
    rim = np.clip((edge - 0.72) / 0.28, 0, 1)[..., None]
    rgb = rgb + (toast - rgb) * rim * 0.85
    # Toasty mottling (low frequency).
    rng = np.random.default_rng(11)
    noise = rng.uniform(-1, 1, (TEX, TEX))
    k = np.ones(41) / 41
    for _ in range(3):  # repeated box blur ~ Gaussian: soft, blob-free toasting
        noise = np.apply_along_axis(lambda r: np.convolve(r, k, "same"), 0, noise)
        noise = np.apply_along_axis(lambda r: np.convolve(r, k, "same"), 1, noise)
    noise /= np.abs(noise).max()
    rgb = rgb + (toast - rgb) * np.clip(noise, 0, 1)[..., None] * 0.25

    px = (x1 - x0) / TEX  # studs per pixel
    W = 3.0 * px          # line half-width

    def stroke(dist, mask):
        """Embossed groove: dark line with a light edge just below/right."""
        m = (np.abs(dist) < W) & mask
        hi = (dist > W) & (dist < W * 2.4) & mask
        rgb[hi] = rgb[hi] * 0.4 + line_hi * 0.6
        rgb[m] = line_dark

    sx = s * LENGTH  # position along body in studs (s-space, used for shapes)
    # Gill arc.
    gc = (0.08 * LENGTH, 0.0)
    r = np.hypot(sx - gc[0], (Y - c) - gc[1])
    stroke(r - 0.26, (sx > gc[0] + 0.1) & (edge < 0.85))
    # Scales: three offset rows of big scallops.
    for row, nyc in enumerate((0.45, 0.0, -0.45)):
        for col in range(3):
            cx = (0.40 + col * 0.11 + (0.055 if row == 1 else 0)) * LENGTH
            cy = c + nyc * h
            rr = np.hypot(sx - cx, Y - cy)
            stroke(rr - 0.1, (sx > cx) & (edge < 0.82) & (s < 0.7))
    # Tail rays.
    for t in (-0.6, -0.2, 0.2, 0.6):
        dist = (Y - c) - t * h * np.clip((s - 0.74) / 0.26, 0, 1) * 0.9
        stroke(dist, (s > 0.8) & (s < 0.97) & (edge < 0.9))
    # Fin stripes on the dorsal bump.
    for f in (0.40, 0.46, 0.52):
        dist = (sx - f * LENGTH) - (ny - 0.8) * 0.06
        stroke(dist, (ny > 0.8) & (edge < 0.97) & (s > 0.36) & (s < 0.58))
    # Eye: embossed ring with a dark pupil.
    ex, ey = 0.12 * LENGTH, 0.0
    er = np.hypot(sx - ex, (Y - c) - (0.28 * h + ey))
    stroke(er - 0.055, np.ones_like(er, bool))
    rgb[er < 0.028] = np.array(L.srgb("#6b3f1d"))
    # Smile.
    mr = np.hypot(sx - 0.0 * LENGTH, (Y - c) + 0.02)
    stroke(mr - 0.09, (sx > 0.04) & (sx < 0.1) & ((Y - c) < -0.02) & ((Y - c) > -0.09))

    return L.image_from_array("Taiyaki_Color", rgb, out_dir)


# ------------------------------------------------------------------- mesh

def build_body(mat):
    bm = bmesh.new()
    rings = []
    ss = (1 - np.cos(np.linspace(0, np.pi, RINGS))) / 2      # denser at nose and tail tip
    for s in ss:
        c, h = profile(s)
        t = curve(THICK, s)
        ring = []
        for j in range(SEGMENTS):
            th = 2 * math.pi * j / SEGMENTS
            ny = math.cos(th)
            sz = math.sin(th)
            # Pillow cross-section with a slight moulded seam at the rim.
            z = t * math.copysign(abs(sz) ** 0.75, sz)
            y = c + h * ny * (1 + 0.02 * math.exp(-(sz / 0.18) ** 2))
            x = (s - 0.5) * LENGTH + tail_notch(s, ny)
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for j in range(SEGMENTS):
            k = (j + 1) % SEGMENTS
            bm.faces.new((a[j], a[k], b[k], b[j]))
    # Nose and tail rings are degenerate (zero thickness): weld them shut.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.obj_from_bm("Taiyaki", bm, mat)


def build(out_dir):
    ymax = max(y for _, y in TOP) * 1.06
    bounds = (-LENGTH / 2 - 0.02, LENGTH / 2 + 0.02, -ymax, ymax)
    mat = L.make_material("Taiyaki_Pastry", pastry_texture(out_dir, bounds), roughness=0.6, specular=0.4)
    body = build_body(mat)
    L.planar_uv(body, 0, 1, bounds)
    return [body]


if __name__ == "__main__":
    ok = L.build_and_ship(NAME, build, views=((0.25, -0.55, 1.1), (0.9, -1.0, 0.45)),
                          bg="#f4eee6", ground="#efe6da", margin=1.0, smooth_angle=180)
    sys.exit(0 if ok else 1)
