from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generic Ultralytics training wrapper")
    parser.add_argument("--task", choices=["segment", "classify", "detect"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", required=True, help="YAML path for detect/segment or dataset root for classify")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--project", default="tmp/training_runs")
    parser.add_argument("--name", required=True)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = YOLO(args.model)
    kwargs = {
        "data": str(Path(args.data)),
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "project": args.project,
        "name": args.name,
        "workers": args.workers,
        "patience": args.patience,
        "seed": args.seed,
    }
    model.train(**kwargs)


if __name__ == "__main__":
    main()
