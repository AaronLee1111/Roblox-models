"""Shared waffle-family builder, based on the Croffle asset's waffle-grid body
(real ridge geometry + pocket-aligned texture), re-proportioned into a thick
square Belgian waffle and presented on the pancake family's café plate."""
import dessert_lib as L
import cafe_parts as P
import build_croffle as W
import build_souffle_pancakes as S
import numpy as np


def belgian_shape():
    W.LEN, W.WID = 1.12, 1.12
    W.HALF_T, W.DEPTH = 0.16, 0.065
    W.NX, W.NY = 4, 4
    W.SQ = 5.0
    W.BEND = W.ARCH = W.TAPER = W.HORN = 0.0
    W.BODY_NAME = "Waffle"


def edge_texture(out_dir):
    """Plain toasty golden rim (no croissant layering, unlike the Croffle)."""
    return L.solid_image("WaffleEdge_Color", "#d99a4c", out_dir)


def base(out_dir, plate_hex, fill=None, sugar_dots=60, drizzle=None):
    """Plate + Belgian waffle. Returns (parts, top_at) where top_at(u, v) gives the
    waffle's top surface point for param u, v in [-1, 1]."""
    belgian_shape()
    top_mat = L.make_material("Waffle", W.waffle_texture(out_dir, "Waffle_Color", sugar_dots=sugar_dots,
                                                         ridge_hex="#c98236", floor_hex="#f2c06c", fill=fill,
                                                         drizzle=drizzle),
                              roughness=0.7, specular=0.25)
    edge_mat = L.make_material("WaffleEdge", edge_texture(out_dir), roughness=0.75, specular=0.2)
    plate = L.make_material("Plate", L.solid_image("Plate_Color", plate_hex, out_dir), roughness=0.5, specular=0.3)
    body = W.build_body(top_mat, edge_mat)
    lift = S.PLATE_TOP + W.HALF_T * 0.75
    body.location.z = lift
    body.rotation_euler.z = 0.35                         # diamond-ish angle reads better in 3/4 view

    def top_at(u, v):
        from mathutils import Matrix, Vector
        (x, y, z), _ = W.place(u, v, +1)
        return Matrix.Translation((0, 0, lift)) @ Matrix.Rotation(0.35, 4, "Z") @ Vector((x, y, z))

    return [S.build_plate(plate), body], top_at


def cream_mat(out_dir):
    return L.make_material("Cream", L.solid_image("Cream_Color", "#fff8ef", out_dir), roughness=0.7, specular=0.25)


def render(name, build):
    return L.build_and_ship(name, build, views=((0.8, -1.0, 0.75), (0.2, -0.5, 1.3)),
                            bg="#f4eee6", ground="#efe6da", margin=1.0)
