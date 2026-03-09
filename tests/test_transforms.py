from __future__ import annotations

import unittest

from camviz.conventions import CAMERA_PRESET_LABELS, CAMERA_PRESETS, WORLD_PRESET_LABELS, WORLD_PRESETS
from camviz.inspection import interpret_pose
from camviz.models import InspectConfig


IDENTITY = (
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 1.0),
)


class TransformTests(unittest.TestCase):
    def test_identity_cam2world_stays_identity_in_canonical_frame(self) -> None:
        config = InspectConfig(
            matrix=IDENTITY,
            pose_type="cam2world",
            world_convention=WORLD_PRESETS["rh_z_up"],
            camera_convention=CAMERA_PRESETS["opencv"],
            intrinsics=None,
            no_browser=True,
            host="127.0.0.1",
            port=8080,
        )
        interpretation = interpret_pose(config)
        self.assertEqual(interpretation.canonical_cam2world, IDENTITY)
        self.assertFalse(interpretation.inversion_applied)

    def test_world2cam_inverse_matches_cam2world(self) -> None:
        cam2world = (
            (0.0, -1.0, 0.0, 1.0),
            (1.0, 0.0, 0.0, 2.0),
            (0.0, 0.0, 1.0, 3.0),
            (0.0, 0.0, 0.0, 1.0),
        )
        world2cam = (
            (0.0, 1.0, 0.0, -2.0),
            (-1.0, 0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0, -3.0),
            (0.0, 0.0, 0.0, 1.0),
        )

        cam2world_result = interpret_pose(
            InspectConfig(
                matrix=cam2world,
                pose_type="cam2world",
                world_convention=WORLD_PRESETS["rh_z_up"],
                camera_convention=CAMERA_PRESETS["opencv"],
                intrinsics=None,
                no_browser=True,
                host="127.0.0.1",
                port=8080,
            )
        )
        world2cam_result = interpret_pose(
            InspectConfig(
                matrix=world2cam,
                pose_type="world2cam",
                world_convention=WORLD_PRESETS["rh_z_up"],
                camera_convention=CAMERA_PRESETS["opencv"],
                intrinsics=None,
                no_browser=True,
                host="127.0.0.1",
                port=8080,
            )
        )

        self.assertEqual(cam2world_result.canonical_cam2world, world2cam_result.canonical_cam2world)
        self.assertTrue(world2cam_result.inversion_applied)

    def test_opengl_camera_flips_y_and_z_relative_to_opencv(self) -> None:
        opencv_result = interpret_pose(
            InspectConfig(
                matrix=IDENTITY,
                pose_type="cam2world",
                world_convention=WORLD_PRESETS["rh_z_up"],
                camera_convention=CAMERA_PRESETS["opencv"],
                intrinsics=None,
                no_browser=True,
                host="127.0.0.1",
                port=8080,
            )
        )
        opengl_result = interpret_pose(
            InspectConfig(
                matrix=IDENTITY,
                pose_type="cam2world",
                world_convention=WORLD_PRESETS["rh_z_up"],
                camera_convention=CAMERA_PRESETS["opengl"],
                intrinsics=None,
                no_browser=True,
                host="127.0.0.1",
                port=8080,
            )
        )

        self.assertEqual(opencv_result.canonical_cam2world[0][0], 1.0)
        self.assertEqual(opengl_result.canonical_cam2world[0][0], 1.0)
        self.assertEqual(opengl_result.canonical_cam2world[1][1], -1.0)
        self.assertEqual(opengl_result.canonical_cam2world[2][2], -1.0)

    def test_left_handed_world_preset_changes_world_basis(self) -> None:
        rh = interpret_pose(
            InspectConfig(
                matrix=IDENTITY,
                pose_type="cam2world",
                world_convention=WORLD_PRESETS["rh_z_up"],
                camera_convention=CAMERA_PRESETS["opencv"],
                intrinsics=None,
                no_browser=True,
                host="127.0.0.1",
                port=8080,
            )
        )
        lh = interpret_pose(
            InspectConfig(
                matrix=IDENTITY,
                pose_type="cam2world",
                world_convention=WORLD_PRESETS["lh_z_up"],
                camera_convention=CAMERA_PRESETS["opencv"],
                intrinsics=None,
                no_browser=True,
                host="127.0.0.1",
                port=8080,
            )
        )

        self.assertEqual(rh.canonical_cam2world[1][1], 1.0)
        self.assertEqual(lh.canonical_cam2world[1][1], -1.0)

    def test_named_world_presets_keep_unity_and_unreal_distinct(self) -> None:
        self.assertEqual(WORLD_PRESET_LABELS["maya"], "Maya (RH-Y-up)")
        self.assertEqual(WORLD_PRESET_LABELS["unity"], "Unity (LH-Y-up)")
        self.assertEqual(WORLD_PRESET_LABELS["unreal"], "Unreal (LH-Z-up)")
        self.assertEqual(WORLD_PRESET_LABELS["pytorch3d"], "PyTorch3D (RH, X-left, Y-up)")
        self.assertNotEqual(WORLD_PRESETS["unity"], WORLD_PRESETS["unreal"])
        self.assertEqual(WORLD_PRESETS["pytorch3d"].x, "-x")
        self.assertEqual(WORLD_PRESETS["pytorch3d"].y, "+z")

    def test_named_camera_presets_include_common_aliases(self) -> None:
        self.assertEqual(
            CAMERA_PRESET_LABELS["opengl"],
            "OpenGL / Blender (Rgt=+X, Up=+Y, Fwd=-Z)",
        )
        self.assertEqual(
            CAMERA_PRESET_LABELS["robotics_optical"],
            "Robotics / ROS Optical (Rgt=+X, Up=-Y, Fwd=+Z)",
        )
        self.assertEqual(CAMERA_PRESET_LABELS["blender_camera"], CAMERA_PRESET_LABELS["opengl"])
        self.assertEqual(CAMERA_PRESETS["opencv"].x, CAMERA_PRESETS["robotics_optical"].x)
        self.assertEqual(CAMERA_PRESETS["opencv"].y, CAMERA_PRESETS["robotics_optical"].y)
        self.assertEqual(CAMERA_PRESETS["opencv"].z, CAMERA_PRESETS["robotics_optical"].z)


if __name__ == "__main__":
    unittest.main()
