from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from camviz.cli import main
from camviz.parsing import parse_axis_convention, parse_intrinsics, parse_matrix_input


class ParsingTests(unittest.TestCase):
    def test_parse_inline_matrix_list_literal(self) -> None:
        matrix = parse_matrix_input("[[1, 0, 0, 1], [0, 1, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1]]")
        self.assertEqual(matrix[0][3], 1.0)
        self.assertEqual(matrix[1][3], 2.0)
        self.assertEqual(matrix[2][3], 3.0)

    def test_rejects_bare_inline_numeric_matrix(self) -> None:
        with self.assertRaises(ValueError):
            parse_matrix_input("1 0 0 1 0 1 0 2 0 0 1 3 0 0 0 1")

    def test_parse_json_matrix_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "pose.json"
            path.write_text("[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]")
            matrix = parse_matrix_input(str(path))
        self.assertEqual(matrix[3][3], 1.0)

    def test_custom_axes_require_all_dimensions(self) -> None:
        with self.assertRaises(ValueError):
            parse_axis_convention("custom", "x=+x,y=+y", kind="world")

    def test_intrinsics_validate_positive_scale_terms(self) -> None:
        with self.assertRaises(ValueError):
            parse_intrinsics("0,1,0,0,100,100")

    def test_text_only_cli_prints_diagnostics_without_viewer(self) -> None:
        argv = [
            "camviz",
            "inspect",
            "--matrix",
            "[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]",
            "--text-only",
        ]
        buffer = io.StringIO()
        old_argv = sys.argv
        try:
            sys.argv = argv
            with contextlib.redirect_stdout(buffer):
                main()
        finally:
            sys.argv = old_argv

        output = buffer.getvalue()
        self.assertIn("Pose Diagnostics", output)
        self.assertIn("### Pose Matrix In World", output)


if __name__ == "__main__":
    unittest.main()
