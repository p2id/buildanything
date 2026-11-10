#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_OUTPUTS = {"MANIFEST.json", "SHA256SUMS.txt"}


def generate_manifest(root: Path = ROOT) -> list[dict[str, object]]:
    root = Path(root).resolve()

    for name in EXCLUDED_OUTPUTS:
        if (root / name).is_symlink():
            raise ValueError(f"refusing to write through symbolic link: {name}")

    files: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        if path.is_symlink():
            raise ValueError(f"refusing to include symbolic link: {relative.as_posix()}")
        if not path.is_file() or path.name in EXCLUDED_OUTPUTS:
            continue

        content = path.read_bytes()
        files.append(
            {
                "path": relative.as_posix(),
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )

    manifest = {"name": "universal-build-workflow-v1.0.0", "files": files}
    (root / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (root / "SHA256SUMS.txt").write_text(
        "".join(f"{item['sha256']}  {item['path']}\n" for item in files),
        encoding="utf-8",
    )
    return files


def main() -> int:
    try:
        generate_manifest()
    except (OSError, ValueError) as error:
        print(f"manifest generation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
