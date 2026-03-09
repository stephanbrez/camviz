from __future__ import annotations

import math
import time

from .conventions import (
    CAMERA_PRESET_KEYS,
    CAMERA_PRESET_LABELS,
    CAMERA_PRESETS,
    WORLD_PRESET_KEYS,
    WORLD_PRESET_LABELS,
    WORLD_PRESETS,
    convention_matrix,
)
from .inspection import diagnostics_markdown, interpret_pose
from .math3d import format_matrix, quaternion_from_matrix, split_rt
from .models import AxisConvention, AxisDirection, InspectConfig
from .parsing import parse_custom_axis_convention


AXIS_OPTIONS: tuple[AxisDirection, ...] = ("+x", "-x", "+y", "-y", "+z", "-z")


def launch_viewer(config: InspectConfig) -> None:
    try:
        import numpy as np
        import viser
    except ImportError as exc:  # pragma: no cover - exercised manually
        raise RuntimeError(
            "The viewer dependency is not installed. Run `uv sync` "
            "or `uv run camviz ...`."
        ) from exc

    server = viser.ViserServer(host=config.host, port=config.port)
    # We render the selected world convention explicitly at the origin.
    # Leaving viser's built-in world axes enabled causes duplicated axes.
    server.scene.world_axes.visible = False

    matrix_markdown = server.gui.add_markdown(
        "\n".join(["## Input Matrix", "", "```text", format_matrix(config.matrix), "```"])
    )
    diagnostics = server.gui.add_markdown("")

    pose_type = server.gui.add_dropdown(
        "Pose Type",
        options=("cam2world", "world2cam"),
        initial_value=config.pose_type,
    )
    world_preset_options = tuple(WORLD_PRESET_LABELS[key] for key in WORLD_PRESET_KEYS)
    camera_preset_options = tuple(CAMERA_PRESET_LABELS[key] for key in CAMERA_PRESET_KEYS)
    world_label_to_key = {WORLD_PRESET_LABELS[key]: key for key in WORLD_PRESET_KEYS}
    camera_label_to_key = {CAMERA_PRESET_LABELS[key]: key for key in CAMERA_PRESET_KEYS}
    world_preset = server.gui.add_dropdown(
        "World Convention",
        options=world_preset_options,
        initial_value=WORLD_PRESET_LABELS[
            config.world_convention.name if config.world_convention.name in WORLD_PRESETS else "custom"
        ],
    )
    camera_preset = server.gui.add_dropdown(
        "Camera Convention",
        options=camera_preset_options,
        initial_value=CAMERA_PRESET_LABELS[
            config.camera_convention.name if config.camera_convention.name in CAMERA_PRESETS else "custom"
        ],
    )
    axis_scale = server.gui.add_number("Axis Scale", initial_value=0.75, min=0.1, step=0.05)
    frustum_scale = server.gui.add_number("Frustum Scale", initial_value=0.6, min=0.05, step=0.05)

    world_axes_handles = _add_axis_controls(server, "World", config.world_convention)
    camera_axes_handles = _add_axis_controls(server, "Camera", config.camera_convention)

    scene_handles: dict[str, object] = {}
    syncing_controls = False

    def active_world_convention() -> AxisConvention:
        world_preset_key = world_label_to_key[world_preset.value]
        if world_preset_key != "custom":
            return WORLD_PRESETS[world_preset_key]
        return parse_custom_axis_convention(_axis_spec_from_handles(world_axes_handles))

    def active_camera_convention() -> AxisConvention:
        camera_preset_key = camera_label_to_key[camera_preset.value]
        if camera_preset_key != "custom":
            return CAMERA_PRESETS[camera_preset_key]
        return parse_custom_axis_convention(_axis_spec_from_handles(camera_axes_handles))

    def sync_control_state() -> None:
        _apply_preset_to_axis_controls(
            world_axes_handles,
            world_label_to_key[world_preset.value],
            WORLD_PRESETS,
        )
        _apply_preset_to_axis_controls(
            camera_axes_handles,
            camera_label_to_key[camera_preset.value],
            CAMERA_PRESETS,
        )

    def update_scene() -> None:
        nonlocal scene_handles, syncing_controls
        if syncing_controls:
            return

        syncing_controls = True
        sync_control_state()
        try:
            current_config = InspectConfig(
                matrix=config.matrix,
                pose_type=pose_type.value,
                world_convention=active_world_convention(),
                camera_convention=active_camera_convention(),
                intrinsics=config.intrinsics,
                no_browser=config.no_browser,
                host=config.host,
                port=config.port,
            )
            interpretation = interpret_pose(current_config)
            diagnostics.content = diagnostics_markdown(current_config, interpretation)

            for handle in scene_handles.values():
                if hasattr(handle, "remove"):
                    handle.remove()
            scene_handles = {}

            rotation, translation = split_rt(interpretation.canonical_cam2world)
            camera_quaternion = quaternion_from_matrix(rotation)
            scene_handles["grid"] = server.scene.add_grid(
                "/ground_grid",
                width=20.0,
                height=20.0,
                plane="xy",
                cell_size=0.5,
                section_size=2.0,
                infinite_grid=True,
            )
            scene_handles["camera_frame"] = server.scene.add_frame(
                "/camera_frame",
                axes_length=axis_scale.value,
                axes_radius=max(axis_scale.value * 0.03, 0.01),
                wxyz=camera_quaternion,
                position=translation,
            )
            fov, aspect = _frustum_parameters(current_config.intrinsics)
            scene_handles["camera_frustum"] = server.scene.add_camera_frustum(
                "/camera_frustum",
                fov=fov,
                aspect=aspect,
                scale=frustum_scale.value,
                color=(47, 111, 237),
                wxyz=camera_quaternion,
                position=translation,
            )
            scene_handles["camera_top_arrow"] = server.scene.add_line_segments(
                "/camera_top_arrow",
                points=np.array(_camera_top_arrow_segments(), dtype=float),
                colors=(255, 140, 0),
                line_width=3.5,
                scale=frustum_scale.value,
                wxyz=camera_quaternion,
                position=translation,
            )
            selected_world_quaternion = quaternion_from_matrix(convention_matrix(current_config.world_convention))
            scene_handles["world_convention"] = server.scene.add_frame(
                "/selected_world_convention",
                axes_length=axis_scale.value * 0.6,
                axes_radius=max(axis_scale.value * 0.02, 0.008),
                origin_color=(255, 128, 0),
                wxyz=selected_world_quaternion,
                position=(0.0, 0.0, 0.0),
            )
        finally:
            syncing_controls = False

    for handle in (
        pose_type,
        world_preset,
        camera_preset,
        axis_scale,
        frustum_scale,
        *world_axes_handles.values(),
        *camera_axes_handles.values(),
    ):
        handle.on_update(lambda _: update_scene())

    update_scene()

    print("Press Ctrl+C to exit.")

    if not config.no_browser:
        try:
            import webbrowser

            webbrowser.open(_server_http_url(server))
        except Exception:
            pass

    while True:
        time.sleep(1.0)


def _add_axis_controls(server: object, prefix: str, convention: AxisConvention) -> dict[str, object]:
    gui = server.gui
    return {
        "x": gui.add_dropdown(f"{prefix} X Axis", options=AXIS_OPTIONS, initial_value=convention.x),
        "y": gui.add_dropdown(f"{prefix} Y Axis", options=AXIS_OPTIONS, initial_value=convention.y),
        "z": gui.add_dropdown(f"{prefix} Z Axis", options=AXIS_OPTIONS, initial_value=convention.z),
    }


def _axis_spec_from_handles(handles: dict[str, object]) -> str:
    return ",".join(f"{axis}={handles[axis].value}" for axis in ("x", "y", "z"))


def _apply_preset_to_axis_controls(
    handles: dict[str, object],
    preset_name: str,
    presets: dict[str, AxisConvention],
) -> None:
    is_custom = preset_name == "custom"
    for handle in handles.values():
        if handle.disabled != (not is_custom):
            handle.disabled = not is_custom
    if not is_custom:
        preset = presets[preset_name]
        _set_control_value(handles["x"], preset.x)
        _set_control_value(handles["y"], preset.y)
        _set_control_value(handles["z"], preset.z)


def _set_control_value(handle: object, value: object) -> None:
    if handle.value != value:
        handle.value = value


def _frustum_parameters(intrinsics: object) -> tuple[float, float]:
    if intrinsics is None:
        return math.radians(60.0), 16.0 / 9.0
    aspect = intrinsics.width / intrinsics.height
    fov = 2.0 * math.atan((intrinsics.height * 0.5) / intrinsics.fy)
    return fov, aspect


def _camera_top_arrow_segments() -> tuple[tuple[tuple[float, float, float], tuple[float, float, float]], ...]:
    tip = (0.0, -0.85, 0.2)
    base = (0.0, -0.25, 0.2)
    left_head = (-0.12, -0.62, 0.2)
    right_head = (0.12, -0.62, 0.2)
    return (
        (base, tip),
        (left_head, tip),
        (right_head, tip),
    )


def _server_http_url(server: object) -> str:
    host = server.get_host()
    if host == "0.0.0.0":
        host = "localhost"
    return f"http://{host}:{server.get_port()}"
