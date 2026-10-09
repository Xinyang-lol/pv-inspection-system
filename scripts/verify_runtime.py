"""Verify relocated app assets, APIs and CPU inference with an existing panel image."""
from __future__ import annotations

import argparse
import io
import json
import platform
import sys
import tempfile
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True, help="Existing real image with visible PV panels.")
    parser.add_argument("--report", type=Path, default=ROOT / "docs/checks/runtime-validation.json")
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error("--image must be an existing image file")

    from backend import app as application
    from backend.services.pipeline import AnalysisPipeline

    checks = []
    with tempfile.TemporaryDirectory(prefix="pv-inspection-check-") as temporary:
        root = Path(temporary)
        config = replace(application.config, runtime_root=root, uploads_root=root / "uploads",
                         results_root=root / "results", history_path=root / "analysis_history.json",
                         force_demo_mode=False, device="cpu")
        config.ensure_runtime_dirs()
        application.config = config
        application.pipeline = AnalysisPipeline(config)
        client = application.app.test_client()
        for route in ("/", "/js/jquery.js", "/js/echarts.min.js", "/js/js.js", "/css/comon0.css",
                      "/api/health", "/api/dashboard", "/api/samples", "/api/sample-files/dust-heavy.png"):
            response = client.get(route)
            assert response.status_code == 200, f"GET {route}: {response.status_code}"
        checks.append("Homepage, static resources, health, dashboard, samples and sample image: 200")
        assert client.post("/api/analyze").status_code == 400
        assert client.post("/api/analyze-sample/not-a-sample").status_code == 404
        assert client.get("/api/results/missing.png").status_code == 404
        checks.append("Missing upload, unknown sample and missing result: expected 400/404")
        with args.image.open("rb") as image:
            response = client.post("/api/analyze", data={"image": (io.BytesIO(image.read()), args.image.name)},
                                   content_type="multipart/form-data")
        assert response.status_code == 200, f"Real inference failed: {response.status_code}"
        payload = response.get_json()
        entry = payload["analysis"]["history_entry"]
        assert entry["mode"] == "yolo-tile", entry["mode"]
        assert entry["panel_count"] > 0, "No panel found in supplied verification image"
        assert application.pipeline._tile_classifier_model is not None, "Classifier was not used"
        result_url = entry["result_image_url"]
        assert client.get(result_url).status_code == 200
        checks.append("Real image upload, panel segmentation, tile classification and result image: 200")
        real_summary = payload["analysis"]["result"]["summary"]
        real_timing = payload["analysis"]["result"]["runtime_ms"]
        assert client.get("/api/dashboard").get_json()["overview"]["analysis_count"] == 1
        application.pipeline = AnalysisPipeline(replace(config, force_demo_mode=True))
        for sample_id in ("dust-heavy", "crack-critical", "bio-stain"):
            response = client.post("/api/analyze-sample/" + sample_id)
            assert response.status_code == 200, sample_id
            sample_entry = response.get_json()["analysis"]["history_entry"]
            assert sample_entry["mode"] == "demo"
            assert client.get(sample_entry["result_image_url"]).status_code == 200
        checks.append("All three synthetic samples and result images in explicit demo mode: 200")
        reset = client.post("/api/reset")
        assert reset.status_code == 200
        assert reset.get_json()["overview"]["analysis_count"] == 0
        assert (config.results_root / result_url.rsplit("/", 1)[-1]).is_file()
        checks.append("Reset clears dashboard history and preserves generated image files")
        classifier_names = AnalysisPipeline(config)._load_tile_classifier_model().names
    report = {
        "ok": True, "python": platform.python_version(), "device": "cpu",
        "environment": {name: version(name) for name in ("flask", "numpy", "pillow", "ultralytics", "torch", "torchvision", "PyYAML")},
        "checks": checks, "real_inference_mode": "yolo-tile", "real_image_filename": args.image.name,
        "real_summary": real_summary, "real_runtime_ms": real_timing,
        "classifier_classes": classifier_names,
        "limitations": "One-image functional verification only; no dataset accuracy, retraining or GPU benchmark.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
