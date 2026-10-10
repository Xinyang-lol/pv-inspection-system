from __future__ import annotations

import json
import random
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLS_SOURCE = ROOT / "yolo8 cls training data" / "Dataset"
SEG_SOURCE = ROOT / "yolo8 seg training data" / "Dataset"
OUTPUT_ROOT = ROOT / "tmp" / "prepared_training_data"
CLS_OUTPUT = OUTPUT_ROOT / "cls_severity"
SEG_CONFIG = OUTPUT_ROOT / "panel_seg_dataset.yaml"
SUMMARY_PATH = OUTPUT_ROOT / "dataset_summary.json"
SEED = 42
VAL_RATIO = 0.1


def ensure_link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        dst.hardlink_to(src)
    except OSError:
        shutil.copy2(src, dst)


def collect_images(directory: Path) -> list[Path]:
    return sorted(
        [path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}]
    )


def prepare_cls_dataset() -> dict[str, object]:
    class_dirs = sorted([path for path in (CLS_SOURCE / "train").iterdir() if path.is_dir()])
    rng = random.Random(SEED)
    summary: dict[str, dict[str, int]] = {}

    for split in ("train", "val", "test"):
        (CLS_OUTPUT / split).mkdir(parents=True, exist_ok=True)

    for class_dir in class_dirs:
        class_name = class_dir.name
        train_images = collect_images(CLS_SOURCE / "train" / class_name)
        test_images = collect_images(CLS_SOURCE / "test" / class_name)

        indices = list(range(len(train_images)))
        rng.shuffle(indices)
        val_count = max(1, int(len(train_images) * VAL_RATIO))
        val_indices = set(indices[:val_count])

        counts = {"train": 0, "val": 0, "test": 0}

        for index, image_path in enumerate(train_images):
            split = "val" if index in val_indices else "train"
            ensure_link_or_copy(image_path, CLS_OUTPUT / split / class_name / image_path.name)
            counts[split] += 1

        for image_path in test_images:
            ensure_link_or_copy(image_path, CLS_OUTPUT / "test" / class_name / image_path.name)
            counts["test"] += 1

        summary[class_name] = counts

    return {
        "source": str(CLS_SOURCE),
        "prepared_root": str(CLS_OUTPUT),
        "class_names": [path.name for path in class_dirs],
        "splits": summary,
        "seed": SEED,
        "val_ratio": VAL_RATIO,
    }


def prepare_seg_dataset() -> dict[str, object]:
    yaml_text = "\n".join(
        [
            f"path: {SEG_SOURCE.as_posix()}",
            "train: train/images",
            "val: valid/images",
            "test: test/images",
            "",
            "names:",
            "  0: panel",
            "",
        ]
    )
    SEG_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    SEG_CONFIG.write_text(yaml_text, encoding="utf-8")

    summary = {}
    for split in ("train", "valid", "test"):
        image_dir = SEG_SOURCE / split / "images"
        label_dir = SEG_SOURCE / split / "labels"
        summary[split] = {
            "images": len([path for path in image_dir.iterdir() if path.is_file()]) if image_dir.exists() else 0,
            "labels": len([path for path in label_dir.iterdir() if path.is_file()]) if label_dir.exists() else 0,
        }

    return {
        "source": str(SEG_SOURCE),
        "yaml": str(SEG_CONFIG),
        "splits": summary,
        "class_names": ["panel"],
    }


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "classification": prepare_cls_dataset(),
        "segmentation": prepare_seg_dataset(),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
