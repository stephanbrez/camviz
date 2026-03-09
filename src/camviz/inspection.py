from __future__ import annotations

from .conventions import convention_matrix
from .math3d import (
    Matrix4,
    determinant3,
    format_matrix,
    invert_rigid_transform,
    is_rigid_transform,
    remap_transform_cam2world,
    remap_transform_world2cam,
    split_rt,
)
from .models import AxisConvention, InspectConfig, Intrinsics, PoseInterpretation


def interpret_pose(config: InspectConfig) -> PoseInterpretation:
    world_basis = convention_matrix(config.world_convention)
    camera_basis = convention_matrix(config.camera_convention)
    input_rotation = tuple(tuple(config.matrix[row][col] for col in range(3)) for row in range(3))
    is_rigid = is_rigid_transform(config.matrix)

    if config.pose_type == "cam2world":
        canonical_cam2world = remap_transform_cam2world(config.matrix, world_basis, camera_basis)
        inversion_applied = False
    else:
        canonical_world2cam = remap_transform_world2cam(config.matrix, world_basis, camera_basis)
        canonical_cam2world = invert_rigid_transform(canonical_world2cam)
        inversion_applied = True

    canonical_world2cam = invert_rigid_transform(canonical_cam2world)
    return PoseInterpretation(
        canonical_cam2world=canonical_cam2world,
        canonical_world2cam=canonical_world2cam,
        input_rotation_determinant=determinant3(input_rotation),
        input_was_rigid=is_rigid,
        inversion_applied=inversion_applied,
    )


def diagnostics_markdown(
    config: InspectConfig,
    interpretation: PoseInterpretation,
) -> str:
    rotation, translation = split_rt(interpretation.canonical_cam2world)
    up_vector = (-rotation[0][1], -rotation[1][1], -rotation[2][1])
    intrinsics = _format_intrinsics(config.intrinsics)
    return "\n".join(
        [
            "## Pose Diagnostics",
            "",
            f"- Pose type: `{config.pose_type}`",
            f"- Inversion applied: `{interpretation.inversion_applied}`",
            f"- Input is rigid: `{interpretation.input_was_rigid}`",
            f"- Input rotation determinant: `{interpretation.input_rotation_determinant:.6f}`",
            f"- World axes: {_axis_mapping_markup(config.world_convention)}",
            f"- Camera axes: {_axis_mapping_markup(config.camera_convention)}",
            f"- Intrinsics: `{intrinsics}`",
            "",
            "### Camera Origin In World",
            "",
            f"`({translation[0]:.4f}, {translation[1]:.4f}, {translation[2]:.4f})`",
            "",
            "### Camera Basis In World",
            "",
            f"- Rgt: `({rotation[0][0]:.4f}, {rotation[1][0]:.4f}, {rotation[2][0]:.4f})`",
            f"- Up: `({up_vector[0]:.4f}, {up_vector[1]:.4f}, {up_vector[2]:.4f})`",
            f"- Fwd: `({rotation[0][2]:.4f}, {rotation[1][2]:.4f}, {rotation[2][2]:.4f})`",
            "",
            "### Pose Matrix In World",
            "",
            "```text",
            format_matrix(interpretation.canonical_cam2world),
            "```",
        ]
    )


def _format_intrinsics(intrinsics: Intrinsics | None) -> str:
    if intrinsics is None:
        return "normalized debug frustum"
    return (
        f"fx={intrinsics.fx:.3f}, fy={intrinsics.fy:.3f}, cx={intrinsics.cx:.3f}, "
        f"cy={intrinsics.cy:.3f}, width={intrinsics.width:.1f}, height={intrinsics.height:.1f}"
    )


def _axis_mapping_markup(convention: AxisConvention) -> str:
    parts = [
        _axis_assignment("🔴", "X", convention.x),
        _axis_assignment("🟢", "Y", convention.y),
        _axis_assignment("🔵", "Z", convention.z),
    ]
    return " ".join(parts)


def _axis_assignment(marker: str, axis_name: str, direction: str) -> str:
    return f"**{marker} {axis_name}={direction.upper()}**"
