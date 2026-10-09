"""Import existing project datasets into the standardized local data directories."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".txt", ".yaml", ".yml", ".md", ".json"}


def import_dataset(source: Path, destination: Path, force_copy: bool) -> dict:
    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must be different directories.")
    summary = {"linked": 0, "copied": 0, "existing": 0}
    for file in sorted(source.rglob("*")):
        if not file.is_file() or file.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        target = destination / file.relative_to(source)
        if target.exists():
            if target.stat().st_size != file.stat().st_size:
                raise FileExistsError(f"Different file already exists: {target}")
            summary["existing"] += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if not force_copy:
            try:
                target.hardlink_to(file)
                summary["linked"] += 1
                continue
            except OSError:
                pass
        shutil.copy2(file, target)
        summary["copied"] += 1
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Original PV_Project directory.")
    parser.add_argument("--copy", action="store_true", help="Copy instead of attempting hard links.")
    args = parser.parse_args()
    project = args.source.resolve()
    datasets = {}
    for name, original_name in (("panel-seg", "yolo8 seg training data"), ("tile-cls", "yolo8 cls training data")):
        candidates = [project / "老师给的" / original_name / "Dataset", project / original_name / "Dataset"]
        source = next((path for path in candidates if path.is_dir()), None)
        if source is None:
            raise FileNotFoundError(f"Missing {name} dataset below {project}")
        datasets[name] = source
    for name, source in datasets.items():
        summary = import_dataset(source, ROOT / "data" / "datasets" / name, args.copy)
        print(json.dumps({"dataset": name, "source": str(source), **summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
