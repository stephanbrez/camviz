from __future__ import annotations

import unittest

from camviz.conventions import WORLD_PRESETS
from camviz.viewer import _apply_preset_to_axis_controls, _camera_top_arrow_segments


class _FakeHandle:
    def __init__(self, value: str, *, disabled: bool = False) -> None:
        self._value = value
        self.disabled = disabled
        self.value_assignments = 0

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        self._value = new_value
        self.value_assignments += 1


class ViewerTests(unittest.TestCase):
    def test_apply_preset_skips_reassigning_matching_values(self) -> None:
        handles = {
            "x": _FakeHandle("+x"),
            "y": _FakeHandle("+y"),
            "z": _FakeHandle("+z"),
        }

        _apply_preset_to_axis_controls(handles, "rh_z_up", WORLD_PRESETS)

        self.assertEqual(handles["x"].value_assignments, 0)
        self.assertEqual(handles["y"].value_assignments, 0)
        self.assertEqual(handles["z"].value_assignments, 0)
        self.assertTrue(all(handle.disabled for handle in handles.values()))

    def test_camera_top_arrow_points_up_in_camera_local_space(self) -> None:
        segments = _camera_top_arrow_segments()
        self.assertEqual(len(segments), 3)
        base, tip = segments[0]
        self.assertLess(tip[1], base[1])
        self.assertEqual(tip[2], base[2])


if __name__ == "__main__":
    unittest.main()
