"""Belgian Waffle: thick square waffle (Croffle waffle-grid base) with deep
pockets, maple syrup pooled in some pockets and drizzled over the top, a butter pat and a light
powdered-sugar dusting, on the café plate."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dessert_lib as L  # noqa: E402
import cafe_parts as P  # noqa: E402
import premium_parts as Q  # noqa: E402
import waffle_family as F  # noqa: E402

NAME = "BelgianWaffle"
DRIZZLE = [(-0.85, -0.6), (-0.6, 0.7), (-0.3, -0.7), (0.0, 0.75), (0.3, -0.7), (0.6, 0.7), (0.85, -0.55)]
SYRUP_POCKETS = {(1, 1), (2, 1), (1, 2), (2, 2), (0, 2), (3, 1), (2, 3)}


def build(out_dir):
    parts, top_at = F.base(out_dir, "#bfe0f4",
                           fill=lambda i, j: "#a4501a" if (i, j) in SYRUP_POCKETS else None,
                           drizzle=("#7e3810", 0.03, DRIZZLE))
    butter = L.make_material("Butter", L.solid_image("Butter_Color", "#ffe68a", out_dir), roughness=0.4, specular=0.35)

    c = top_at(0.0, 0.0)
    s = 0.13
    pat = Q.rounded_extrude("Butter", P.chaikin([(-s, -s), (s, -s), (s, s), (-s, s)], 1), 0.08, butter,
                            round_frac=0.4, steps=2)
    pat.location = (c.x, c.y, c.z - 0.012)
    pat.rotation_euler = (0.06, -0.05, 0.7)
    parts.append(pat)
    return parts


if __name__ == "__main__":
    sys.exit(0 if F.render(NAME, build) else 1)
