from __future__ import annotations

import ast
import re
from pathlib import Path

from .conventions import CAMERA_PRESETS, WORLD_PRESETS
from .models import AxisConvention, AxisDirection, Intrinsics

_AXIS_SPEC_PATTERN = re.compile(r"([xyzXYZ])\s*=\s*([+-][xyzXYZ])")
_VALID_DIRECTIONS = {"+x", "-x", "+y", "-y", "+z", "-z"}


def parse_matrix_input(raw: str) -> tuple[tuple[float, float, float, float], ...]:
    path = Path(raw)
    if path.exists():
        return parse_matrix_text(path.read_text())
    return parse_matrix_text(raw)


def parse_matrix_text(text: str) -> tuple[tuple[float, float, float, float], ...]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("Matrix input is empty.")

    if stripped[0] not in "[{":
        raise ValueError(
            "Inline matrices must use list notation like "
            "`[[1, 0, 0, 1], [0, 1, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1]]` "
            "or be provided via a file path."
        )

    try:
        parsed = ast.literal_eval(stripped)
    except (SyntaxError, ValueError) as exc:
        raise ValueError(
            "Matrix input must be a valid Python/JSON literal in list notation."
        ) from exc

    matrix = _coerce_matrix_literal(parsed)
    _validate_shape(matrix)
    return matrix


def _coerce_matrix_literal(parsed: object) -> tuple[tuple[float, float, float, float], ...]:
    if isinstance(parsed, dict):
        if "matrix" in parsed:
            parsed = parsed["matrix"]
        else:
            raise ValueError("JSON object input must contain a 'matrix' field.")

    if isinstance(parsed, list) and len(parsed) == 16:
        return tuple(
            tuple(float(parsed[row * 4 + col]) for col in range(4))
            for row in range(4)
        )

    if isinstance(parsed, list) and len(parsed) == 4 and all(isinstance(row, list) and len(row) == 4 for row in parsed):
        return tuple(tuple(float(value) for value in row) for row in parsed)

    raise ValueError(
        "Matrix literal must be either a flat list of 16 values or a 4x4 nested list."
    )


def _validate_shape(matrix: tuple[tuple[float, ...], ...]) -> None:
    if len(matrix) != 4 or any(len(row) != 4 for row in matrix):
        raise ValueError("Expected a 4x4 matrix.")


def parse_intrinsics(raw: str | None) -> Intrinsics | None:
    if raw is None:
        return None
    values = [float(token) for token in re.split(r"[\s,]+", raw.strip()) if token]
    if len(values) != 6:
        raise ValueError("Intrinsics must contain fx, fy, cx, cy, width, height.")
    fx, fy, cx, cy, width, height = values
    if fx <= 0 or fy <= 0 or width <= 0 or height <= 0:
        raise ValueError("fx, fy, width, and height must be positive.")
    return Intrinsics(fx=fx, fy=fy, cx=cx, cy=cy, width=width, height=height)


def parse_axis_convention(
    preset_name: str,
    custom_axes: str | None,
    *,
    kind: str,
) -> AxisConvention:
    preset_table = WORLD_PRESETS if kind == "world" else CAMERA_PRESETS
    if preset_name != "custom":
        return preset_table[preset_name]
    if custom_axes is None:
        raise ValueError(f"{kind.capitalize()} custom convention requires --{kind}-axes.")
    return parse_custom_axis_convention(custom_axes, name="custom")


def parse_custom_axis_convention(spec: str, *, name: str = "custom") -> AxisConvention:
    mapping: dict[str, AxisDirection] = {}
    for axis_name, direction in _AXIS_SPEC_PATTERN.findall(spec):
        normalized_axis = axis_name.lower()
        normalized_direction = direction.lower()
        if normalized_direction not in _VALID_DIRECTIONS:
            raise ValueError(f"Invalid axis direction '{direction}'.")
        mapping[normalized_axis] = normalized_direction  # type: ignore[assignment]

    if set(mapping) != {"x", "y", "z"}:
        raise ValueError("Custom axis mapping must define x=..., y=..., and z=....")

    return AxisConvention(name=name, x=mapping["x"], y=mapping["y"], z=mapping["z"])
