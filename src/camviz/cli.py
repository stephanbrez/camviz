from __future__ import annotations

import argparse

from .conventions import CAMERA_PRESET_KEYS, WORLD_PRESET_KEYS
from .inspection import diagnostics_markdown, interpret_pose
from .models import InspectConfig
from .parsing import parse_axis_convention, parse_intrinsics, parse_matrix_input


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="camviz",
        description="Inspect a camera pose matrix under different coordinate conventions.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Visualize one camera pose matrix.")
    inspect_parser.add_argument(
        "--matrix",
        required=True,
        help="A 4x4 matrix in Python/JSON list notation, or a path to a file containing one.",
    )
    inspect_parser.add_argument("--pose-type", choices=("cam2world", "world2cam"), default="cam2world")
    inspect_parser.add_argument(
        "--camera-convention",
        choices=CAMERA_PRESET_KEYS,
        default="opencv",
    )
    inspect_parser.add_argument(
        "--world-convention",
        choices=WORLD_PRESET_KEYS,
        default="blender",
    )
    inspect_parser.add_argument("--camera-axes", help="Custom camera axes, e.g. x=+x,y=-y,z=+z.")
    inspect_parser.add_argument("--world-axes", help="Custom world axes, e.g. x=+x,y=+z,z=-y.")
    inspect_parser.add_argument(
        "--intrinsics",
        help="fx,fy,cx,cy,width,height for a true frustum. Otherwise a normalized frustum is used.",
    )
    inspect_parser.add_argument("--host", default="127.0.0.1")
    inspect_parser.add_argument("--port", type=int, default=8080)
    inspect_parser.add_argument("--no-browser", action="store_true")
    inspect_parser.add_argument(
        "--text-only",
        action="store_true",
        help="Print diagnostics without launching the interactive viewer.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "inspect":
        config = InspectConfig(
            matrix=parse_matrix_input(args.matrix),
            pose_type=args.pose_type,
            world_convention=parse_axis_convention(args.world_convention, args.world_axes, kind="world"),
            camera_convention=parse_axis_convention(args.camera_convention, args.camera_axes, kind="camera"),
            intrinsics=parse_intrinsics(args.intrinsics),
            no_browser=args.no_browser,
            host=args.host,
            port=args.port,
        )
        if args.text_only:
            print(diagnostics_markdown(config, interpret_pose(config)))
            return

        from .viewer import launch_viewer

        launch_viewer(config)
