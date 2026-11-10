import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from automation.update_manifest import generate_manifest


class UpdateManifestTests(unittest.TestCase):
    def test_generates_sorted_hashes_and_excludes_output_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "b.txt").write_bytes(b"beta")
            (root / "a.txt").write_bytes(b"alpha")
            (root / "MANIFEST.json").write_text("stale", encoding="utf-8")
            (root / "SHA256SUMS.txt").write_text("stale", encoding="utf-8")

            files = generate_manifest(root)

            expected = [
                {
                    "path": "a.txt",
                    "bytes": 5,
                    "sha256": hashlib.sha256(b"alpha").hexdigest(),
                },
                {
                    "path": "b.txt",
                    "bytes": 4,
                    "sha256": hashlib.sha256(b"beta").hexdigest(),
                },
            ]
            self.assertEqual(files, expected)
            self.assertEqual(
                json.loads((root / "MANIFEST.json").read_text(encoding="utf-8")),
                {"name": "universal-build-workflow-v1.0.0", "files": expected},
            )
            self.assertEqual(
                (root / "SHA256SUMS.txt").read_text(encoding="utf-8"),
                "".join(f"{item['sha256']}  {item['path']}\n" for item in expected),
            )

    def test_rejects_file_symlink(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "repo"
            root.mkdir()
            outside = Path(temporary_directory) / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            (root / "linked.txt").symlink_to(outside)

            with self.assertRaisesRegex(ValueError, "symbolic link"):
                generate_manifest(root)

            self.assertFalse((root / "MANIFEST.json").exists())
            self.assertEqual(outside.read_text(encoding="utf-8"), "outside")

    def test_rejects_directory_symlink(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "repo"
            root.mkdir()
            outside = Path(temporary_directory) / "outside"
            outside.mkdir()
            (outside / "secret.txt").write_text("outside", encoding="utf-8")
            (root / "linked-dir").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "symbolic link"):
                generate_manifest(root)

            self.assertFalse((root / "MANIFEST.json").exists())

    def test_rejects_symlinked_output_without_overwriting_target(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "repo"
            root.mkdir()
            outside = Path(temporary_directory) / "outside-manifest.json"
            outside.write_text("keep", encoding="utf-8")
            (root / "MANIFEST.json").symlink_to(outside)

            with self.assertRaisesRegex(ValueError, "write through symbolic link"):
                generate_manifest(root)

            self.assertEqual(outside.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
