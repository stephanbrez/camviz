from __future__ import annotations

from .models import AxisConvention, AxisDirection

_AXIS_TO_VECTOR: dict[AxisDirection, tuple[int, int, int]] = {
    "+x": (1, 0, 0),
    "-x": (-1, 0, 0),
    "+y": (0, 1, 0),
    "-y": (0, -1, 0),
    "+z": (0, 0, 1),
    "-z": (0, 0, -1),
}

WORLD_PRESETS: dict[str, AxisConvention] = {
    "rh_z_up": AxisConvention("rh_z_up", x="+x", y="+y", z="+z"),
    "rh_y_up": AxisConvention("rh_y_up", x="+x", y="+z", z="-y"),
    "lh_z_up": AxisConvention("lh_z_up", x="+x", y="-y", z="+z"),
    "lh_y_up": AxisConvention("lh_y_up", x="+x", y="+z", z="+y"),
    "blender": AxisConvention("blender", x="+x", y="+y", z="+z"),
    "maya": AxisConvention("maya", x="+x", y="+z", z="-y"),
    "unity": AxisConvention("unity", x="+x", y="+z", z="+y"),
    "unreal": AxisConvention("unreal", x="+y", y="+x", z="+z"),
    "robotics": AxisConvention("robotics", x="+y", y="-x", z="+z"),
    "pytorch3d": AxisConvention("pytorch3d", x="-x", y="+z", z="+y"),
}
WORLD_PRESET_LABELS: dict[str, str] = {
    "rh_z_up": "Generic RH-Z-up",
    "rh_y_up": "Generic RH-Y-up",
    "lh_z_up": "Generic LH-Z-up",
    "lh_y_up": "Generic LH-Y-up",
    "blender": "Blender (RH-Z-up)",
    "maya": "Maya (RH-Y-up)",
    "unity": "Unity (LH-Y-up)",
    "unreal": "Unreal (LH-Z-up)",
    "robotics": "Robotics / ROS (RH, X-forward, Y-left, Z-up)",
    "pytorch3d": "PyTorch3D (RH, X-left, Y-up)",
    "custom": "Custom",
}

CAMERA_PRESETS: dict[str, AxisConvention] = {
    "opencv": AxisConvention("opencv", x="+x", y="+y", z="+z"),
    "opengl": AxisConvention("opengl", x="+x", y="-y", z="-z"),
    "pytorch3d": AxisConvention("pytorch3d", x="-x", y="-y", z="+z"),
    "blender_camera": AxisConvention("blender_camera", x="+x", y="-y", z="-z"),
    "maya_camera": AxisConvention("maya_camera", x="+x", y="-y", z="-z"),
    "robotics_optical": AxisConvention("robotics_optical", x="+x", y="+y", z="+z"),
    "unity_camera": AxisConvention("unity_camera", x="+x", y="-y", z="+z"),
    "unreal_camera": AxisConvention("unreal_camera", x="+z", y="+x", z="-y"),
}
CAMERA_PRESET_LABELS: dict[str, str] = {
    "opencv": "OpenCV (Rgt=+X, Up=-Y, Fwd=+Z)",
    "opengl": "OpenGL / Blender (Rgt=+X, Up=+Y, Fwd=-Z)",
    "pytorch3d": "PyTorch3D (Rgt=-X, Up=+Y, Fwd=+Z)",
    "blender_camera": "OpenGL / Blender (Rgt=+X, Up=+Y, Fwd=-Z)",
    "maya_camera": "Maya Camera (Rgt=+X, Up=+Y, Fwd=-Z)",
    "robotics_optical": "Robotics / ROS Optical (Rgt=+X, Up=-Y, Fwd=+Z)",
    "unity_camera": "Unity Camera (Rgt=+X, Up=+Y, Fwd=+Z)",
    "unreal_camera": "Unreal Camera (Rgt=+Y, Up=+Z, Fwd=+X)",
    "custom": "Custom",
}


def axis_vector(axis: AxisDirection) -> tuple[int, int, int]:
    return _AXIS_TO_VECTOR[axis]


def convention_matrix(convention: AxisConvention) -> tuple[tuple[float, float, float], ...]:
    """Columns are the source frame axes expressed in canonical coordinates."""
    cols = [axis_vector(convention.x), axis_vector(convention.y), axis_vector(convention.z)]
    return (
        (float(cols[0][0]), float(cols[1][0]), float(cols[2][0])),
        (float(cols[0][1]), float(cols[1][1]), float(cols[2][1])),
        (float(cols[0][2]), float(cols[1][2]), float(cols[2][2])),
    )


def determinant3(matrix: tuple[tuple[float, float, float], ...]) -> float:
    return (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )


def handedness_label(convention: AxisConvention) -> str:
    det = determinant3(convention_matrix(convention))
    return "RH" if det > 0 else "LH"


def up_axis_label(convention: AxisConvention) -> str:
    for axis_name, direction in (("X", convention.x), ("Y", convention.y), ("Z", convention.z)):
        vector = axis_vector(direction)
        if vector[2] == 1:
            return f"{axis_name}-up"
        if vector[2] == -1:
            return f"-{axis_name}-up"
    return "no-z-up"


def convention_summary(convention: AxisConvention) -> str:
    return (
        f"{handedness_label(convention)} | "
        f"x={convention.x}, y={convention.y}, z={convention.z}"
    )


def preset_display_label(kind: str, preset_name: str) -> str:
    if kind == "world":
        return WORLD_PRESET_LABELS[preset_name]
    return CAMERA_PRESET_LABELS[preset_name]
