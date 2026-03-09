from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AxisDirection = Literal["+x", "-x", "+y", "-y", "+z", "-z"]
PoseType = Literal["cam2world", "world2cam"]
WorldConventionName = Literal["rh_z_up", "rh_y_up", "lh_z_up", "lh_y_up", "custom"]
CameraConventionName = Literal["opencv", "opengl", "pytorch3d", "custom"]


@dataclass(frozen=True)
class AxisConvention:
    name: str
    x: AxisDirection
    y: AxisDirection
    z: AxisDirection


@dataclass(frozen=True)
class Intrinsics:
    fx: float
    fy: float
    cx: float
    cy: float
    width: float
    height: float


@dataclass(frozen=True)
class InspectConfig:
    matrix: tuple[tuple[float, ...], ...]
    pose_type: PoseType
    world_convention: AxisConvention
    camera_convention: AxisConvention
    intrinsics: Intrinsics | None
    no_browser: bool
    host: str
    port: int


@dataclass(frozen=True)
class PoseInterpretation:
    canonical_cam2world: tuple[tuple[float, ...], ...]
    canonical_world2cam: tuple[tuple[float, ...], ...]
    input_rotation_determinant: float
    input_was_rigid: bool
    inversion_applied: bool
