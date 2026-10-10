from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
FRONTEND_ROOT = PROJECT_ROOT / "011 大数据可视化系统数据分析通用模版"


def _path_from_env(name: str, default: Path) -> Path:
    raw_value = os.getenv(name)
    if not raw_value:
        return default
    candidate = Path(raw_value)
    if candidate.is_absolute():
        return candidate
    return (PROJECT_ROOT / candidate).resolve()


@dataclass(slots=True)
class AppConfig:
    project_root: Path = PROJECT_ROOT
    backend_root: Path = BACKEND_ROOT
    frontend_root: Path = FRONTEND_ROOT
    runtime_root: Path = BACKEND_ROOT / "runtime"
    samples_root: Path = BACKEND_ROOT / "samples"
    uploads_root: Path = BACKEND_ROOT / "runtime" / "uploads"
    results_root: Path = BACKEND_ROOT / "runtime" / "results"
    history_path: Path = BACKEND_ROOT / "runtime" / "analysis_history.json"
    panel_model_path: Path = _path_from_env(
        "PV_PANEL_MODEL", BACKEND_ROOT / "models" / "panel_yolov8_seg.pt"
    )
    defect_model_path: Path = _path_from_env(
        "PV_DEFECT_MODEL", BACKEND_ROOT / "models" / "defect_yolo11_seg.pt"
    )
    tile_classifier_model_path: Path = _path_from_env(
        "PV_TILE_CLS_MODEL", BACKEND_ROOT / "models" / "dust_yolov8_cls.pt"
    )
    panel_model_name: str = os.getenv("PV_PANEL_MODEL_NAME", "YOLOv8m-seg")
    defect_model_name: str = os.getenv("PV_DEFECT_MODEL_NAME", "YOLO11m-seg")
    tile_classifier_model_name: str = os.getenv("PV_TILE_CLS_MODEL_NAME", "YOLOv8 tile-cls")
    confidence_threshold: float = float(os.getenv("PV_CONFIDENCE", "0.25"))
    tile_min_mask_ratio: float = float(os.getenv("PV_TILE_MIN_MASK_RATIO", "0.15"))
    device: str = os.getenv("PV_DEVICE", "cpu")
    host: str = os.getenv("PV_HOST", "0.0.0.0")
    port: int = int(os.getenv("PV_PORT", "5000"))
    debug: bool = os.getenv("PV_DEBUG", "false").lower() == "true"
    force_demo_mode: bool = os.getenv("PV_DEMO_MODE", "false").lower() == "true"

    def ensure_runtime_dirs(self) -> None:
        for path in (self.runtime_root, self.samples_root, self.uploads_root, self.results_root):
            path.mkdir(parents=True, exist_ok=True)


def load_config() -> AppConfig:
    config = AppConfig()
    config.ensure_runtime_dirs()
    return config
