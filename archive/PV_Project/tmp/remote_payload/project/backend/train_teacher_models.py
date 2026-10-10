from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
TEACHER_ROOT = PROJECT_ROOT / "老师给的"


DEFAULT_SEG_DATA = BACKEND_ROOT / "data" / "pv_surface_seg.yaml"
DEFAULT_CLS_DATA = TEACHER_ROOT / "yolo8 cls training data" / "Dataset"
DEFAULT_SEG_MODEL = PROJECT_ROOT / "yolov8n-seg.pt"
DEFAULT_CLS_MODEL = "yolov8n-cls.pt"
DEFAULT_PROJECT = BACKEND_ROOT / "runs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train teacher YOLOv8 PV models.")
    parser.add_argument(
        "--stage",
        choices=("panel-seg", "tile-cls", "all"),
        default="all",
        help="Model stage to train.",
    )
    parser.add_argument("--seg-data", default=str(DEFAULT_SEG_DATA), help="YOLO seg data yaml.")
    parser.add_argument("--cls-data", default=str(DEFAULT_CLS_DATA), help="YOLO cls data directory.")
    parser.add_argument("--seg-model", default=str(DEFAULT_SEG_MODEL), help="Initial YOLOv8 seg weight.")
    parser.add_argument("--cls-model", default=DEFAULT_CLS_MODEL, help="Initial YOLOv8 cls weight.")
    parser.add_argument("--epochs", type=int, default=100, help="Epochs for both stages.")
    parser.add_argument("--seg-epochs", type=int, help="Epochs for panel segmentation.")
    parser.add_argument("--cls-epochs", type=int, help="Epochs for tile classification.")
    parser.add_argument("--seg-imgsz", type=int, default=640, help="Segmentation image size.")
    parser.add_argument("--cls-imgsz", type=int, default=64, help="Classification image size.")
    parser.add_argument("--seg-batch", type=int, default=8, help="Segmentation batch size.")
    parser.add_argument("--cls-batch", type=int, default=16, help="Classification batch size.")
    parser.add_argument("--device", default="0", help="Training device, such as 0 or cpu.")
    parser.add_argument("--workers", type=int, default=4, help="Data loader workers.")
    parser.add_argument("--project", default=str(DEFAULT_PROJECT), help="Run output directory.")
    parser.add_argument("--copy-best", action="store_true", help="Copy best.pt into backend/models.")
    return parser.parse_args()


def train_panel_seg(args: argparse.Namespace) -> Path:
    model = YOLO(args.seg_model)
    result = model.train(
        data=args.seg_data,
        epochs=args.seg_epochs or args.epochs,
        imgsz=args.seg_imgsz,
        batch=args.seg_batch,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name="pv_surface_yolov8_seg",
        patience=25,
    )
    return Path(result.save_dir) / "weights" / "best.pt"


def train_tile_cls(args: argparse.Namespace) -> Path:
    model = YOLO(args.cls_model)
    result = model.train(
        data=args.cls_data,
        epochs=args.cls_epochs or args.epochs,
        imgsz=args.cls_imgsz,
        batch=args.cls_batch,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name="pv_tile_yolov8_cls",
        patience=20,
        pretrained=True,
    )
    return Path(result.save_dir) / "weights" / "best.pt"


def copy_best(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    print(f"copied {source} -> {target}")


def main() -> None:
    args = parse_args()
    trained: list[tuple[Path, Path]] = []

    if args.stage in ("panel-seg", "all"):
        best = train_panel_seg(args)
        trained.append((best, BACKEND_ROOT / "models" / "panel_yolov8_seg.pt"))
        print(f"panel segmentation best: {best}")

    if args.stage in ("tile-cls", "all"):
        best = train_tile_cls(args)
        trained.append((best, BACKEND_ROOT / "models" / "dust_yolov8_cls.pt"))
        print(f"tile classification best: {best}")

    if args.copy_best:
        for source, target in trained:
            copy_best(source, target)


if __name__ == "__main__":
    main()
