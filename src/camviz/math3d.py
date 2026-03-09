from __future__ import annotations

import math


Matrix3 = tuple[tuple[float, float, float], ...]
Matrix4 = tuple[tuple[float, float, float, float], ...]
Vector3 = tuple[float, float, float]
QuaternionWxyz = tuple[float, float, float, float]


def matmul3(a: Matrix3, b: Matrix3) -> Matrix3:
    return tuple(
        tuple(sum(a[row][k] * b[k][col] for k in range(3)) for col in range(3))
        for row in range(3)
    )


def matvec3(a: Matrix3, v: Vector3) -> Vector3:
    return tuple(sum(a[row][k] * v[k] for k in range(3)) for row in range(3))


def transpose3(matrix: Matrix3) -> Matrix3:
    return tuple(tuple(matrix[col][row] for col in range(3)) for row in range(3))


def matrix4_from_rt(rotation: Matrix3, translation: Vector3) -> Matrix4:
    return (
        (rotation[0][0], rotation[0][1], rotation[0][2], translation[0]),
        (rotation[1][0], rotation[1][1], rotation[1][2], translation[1]),
        (rotation[2][0], rotation[2][1], rotation[2][2], translation[2]),
        (0.0, 0.0, 0.0, 1.0),
    )


def split_rt(matrix: Matrix4) -> tuple[Matrix3, Vector3]:
    rotation: Matrix3 = tuple(tuple(matrix[row][col] for col in range(3)) for row in range(3))
    translation: Vector3 = (matrix[0][3], matrix[1][3], matrix[2][3])
    return rotation, translation


def invert_rigid_transform(matrix: Matrix4) -> Matrix4:
    rotation, translation = split_rt(matrix)
    rotation_t = transpose3(rotation)
    inverted_translation = tuple(-value for value in matvec3(rotation_t, translation))
    return matrix4_from_rt(rotation_t, inverted_translation)


def remap_transform_cam2world(
    transform: Matrix4,
    world_basis_in_canonical: Matrix3,
    camera_basis_in_canonical: Matrix3,
) -> Matrix4:
    rotation, translation = split_rt(transform)
    mapped_rotation = matmul3(
        world_basis_in_canonical,
        matmul3(rotation, transpose3(camera_basis_in_canonical)),
    )
    mapped_translation = matvec3(world_basis_in_canonical, translation)
    return matrix4_from_rt(mapped_rotation, mapped_translation)


def remap_transform_world2cam(
    transform: Matrix4,
    world_basis_in_canonical: Matrix3,
    camera_basis_in_canonical: Matrix3,
) -> Matrix4:
    rotation, translation = split_rt(transform)
    mapped_rotation = matmul3(
        camera_basis_in_canonical,
        matmul3(rotation, transpose3(world_basis_in_canonical)),
    )
    mapped_translation = matvec3(camera_basis_in_canonical, translation)
    return matrix4_from_rt(mapped_rotation, mapped_translation)


def determinant3(matrix: Matrix3) -> float:
    return (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )


def is_close(a: float, b: float, *, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol


def is_rigid_transform(matrix: Matrix4, *, tol: float = 1e-5) -> bool:
    rotation, bottom_translation = split_rt(matrix)[0], matrix[3]
    should_be_identity = matmul3(transpose3(rotation), rotation)
    identity = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    orthonormal = all(
        is_close(should_be_identity[row][col], identity[row][col], tol=tol)
        for row in range(3)
        for col in range(3)
    )
    bottom_ok = all(is_close(bottom_translation[idx], value, tol=tol) for idx, value in enumerate((0.0, 0.0, 0.0, 1.0)))
    determinant_ok = abs(abs(determinant3(rotation)) - 1.0) <= tol
    return orthonormal and bottom_ok and determinant_ok


def quaternion_from_matrix(rotation: Matrix3) -> QuaternionWxyz:
    trace = rotation[0][0] + rotation[1][1] + rotation[2][2]
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        w = 0.25 * s
        x = (rotation[2][1] - rotation[1][2]) / s
        y = (rotation[0][2] - rotation[2][0]) / s
        z = (rotation[1][0] - rotation[0][1]) / s
    elif rotation[0][0] > rotation[1][1] and rotation[0][0] > rotation[2][2]:
        s = math.sqrt(1.0 + rotation[0][0] - rotation[1][1] - rotation[2][2]) * 2.0
        w = (rotation[2][1] - rotation[1][2]) / s
        x = 0.25 * s
        y = (rotation[0][1] + rotation[1][0]) / s
        z = (rotation[0][2] + rotation[2][0]) / s
    elif rotation[1][1] > rotation[2][2]:
        s = math.sqrt(1.0 + rotation[1][1] - rotation[0][0] - rotation[2][2]) * 2.0
        w = (rotation[0][2] - rotation[2][0]) / s
        x = (rotation[0][1] + rotation[1][0]) / s
        y = 0.25 * s
        z = (rotation[1][2] + rotation[2][1]) / s
    else:
        s = math.sqrt(1.0 + rotation[2][2] - rotation[0][0] - rotation[1][1]) * 2.0
        w = (rotation[1][0] - rotation[0][1]) / s
        x = (rotation[0][2] + rotation[2][0]) / s
        y = (rotation[1][2] + rotation[2][1]) / s
        z = 0.25 * s
    norm = math.sqrt(w * w + x * x + y * y + z * z)
    if norm == 0.0:
        return (1.0, 0.0, 0.0, 0.0)
    return (w / norm, x / norm, y / norm, z / norm)


def format_matrix(matrix: tuple[tuple[float, ...], ...], *, precision: int = 4) -> str:
    rows = []
    for row in matrix:
        rows.append("[" + ", ".join(f"{value:.{precision}f}" for value in row) + "]")
    return "\n".join(rows)
