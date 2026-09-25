"""Shared pancake-family builder, based on the Soufflé Pancakes asset: same
puffy stack, plate, syrup-cap-with-drips and material style. Variants only
change colours and toppings."""
import dessert_lib as L
import cafe_parts as P
import build_souffle_pancakes as S

PH = S.PH


def base(out_dir, top_hex, side_hex, sauce_hex, plate_hex, sauce=True):
    """Plate + three-pancake stack (+ optional sauce cap with drips).
    Returns (parts, place) where place(objs) moves toppings built relative to
    the top pancake (its base at z=0) onto the stack."""
    top_mat = L.make_material("PancakeTop", L.solid_image("PancakeTop_Color", top_hex, out_dir),
                              roughness=0.75, specular=0.2)
    side_mat = L.make_material("PancakeSide", L.solid_image("PancakeSide_Color", side_hex, out_dir),
                               roughness=0.85, specular=0.15)
    plate = L.make_material("Plate", L.solid_image("Plate_Color", plate_hex, out_dir),
                            roughness=0.5, specular=0.3)
    parts = [S.build_plate(plate)]
    stack, z = S.build_stack(top_mat, side_mat)
    parts += stack
    dx, dy, rz = S.OFFSETS[-1]

    def place(objs):
        return P.move(objs, dx=dx, dy=dy, dz=z, rot_z=rz)

    if sauce:
        sauce_mat = L.make_material("Sauce", L.solid_image("Sauce_Color", sauce_hex, out_dir),
                                    roughness=0.35, specular=0.4)
        parts += place(S.build_syrup(sauce_mat))
    return parts, place


def cream_mat(out_dir):
    return L.make_material("Cream", L.solid_image("Cream_Color", "#fff8ef", out_dir), roughness=0.7, specular=0.25)


def render(name, build):
    return L.build_and_ship(name, build, views=((0.9, -1.0, 0.55), (0.3, -0.6, 1.3)),
                            bg="#f4eee6", ground="#efe6da", margin=1.05)
