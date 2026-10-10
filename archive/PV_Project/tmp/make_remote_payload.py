from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


workspace = Path(r"D:\大创yolo")
project_root = workspace / "tmp" / "remote_payload" / "project"
archive_path = workspace / "tmp" / "remote_train_payload_posix.zip"

if archive_path.exists():
    archive_path.unlink()

with ZipFile(archive_path, "w", ZIP_DEFLATED) as zf:
    for path in project_root.rglob("*"):
        if path.is_file():
            zf.write(path, path.relative_to(project_root).as_posix())

print(archive_path)
print(round(archive_path.stat().st_size / 1024 / 1024, 2))
