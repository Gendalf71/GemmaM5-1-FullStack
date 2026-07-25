#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import stat
import zipfile

FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def add_file(archive: zipfile.ZipFile, source: Path, arcname: str) -> None:
    mode = stat.S_IMODE(source.stat().st_mode)
    info = zipfile.ZipInfo(arcname, date_time=FIXED_ZIP_TIME)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.flag_bits |= 0x800
    archive.writestr(
        info,
        source.read_bytes(),
        compress_type=zipfile.ZIP_STORED,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a deterministic release ZIP")
    parser.add_argument("stage", type=Path, help="Directory containing one package root")
    parser.add_argument("archive", type=Path, help="Output ZIP path")
    args = parser.parse_args()

    stage = args.stage.resolve()
    archive_path = args.archive.resolve()
    package_roots = sorted(path for path in stage.iterdir() if path.is_dir())
    if len(package_roots) != 1:
        parser.error("stage must contain exactly one package directory")

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w") as archive:
        for source in sorted(package_roots[0].rglob("*"), key=lambda path: path.as_posix()):
            if source.is_symlink():
                parser.error(f"symlink is not permitted: {source}")
            if source.is_file():
                add_file(archive, source, source.relative_to(stage).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
