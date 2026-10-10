from __future__ import annotations

import re

from flask import Flask, jsonify, request, send_file

from backend.config import load_config
from backend.services.pipeline import AnalysisPipeline


config = load_config()
app = Flask(__name__, static_folder=str(config.frontend_root), static_url_path="")
pipeline = AnalysisPipeline(config)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def _safe_filename(original_name: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z.\-_一-龥]+", "_", original_name.strip())
    return cleaned or "uploaded_image.png"


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, **pipeline.get_status()})


@app.get("/api/dashboard")
def dashboard():
    return jsonify(pipeline.build_dashboard())


@app.get("/api/samples")
def samples():
    return jsonify({"samples": pipeline.list_samples()})


@app.post("/api/reset")
def reset_dashboard():
    return jsonify(pipeline.reset_dashboard())


@app.post("/api/analyze")
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "请上传图像文件，字段名为 image。"}), 400

    uploaded = request.files["image"]
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "未收到有效图像文件。"}), 400

    filename = _safe_filename(uploaded.filename)
    upload_path = config.uploads_root / filename
    uploaded.save(upload_path)
    payload = pipeline.analyze(upload_path)
    return jsonify(payload)


@app.post("/api/analyze-sample/<sample_id>")
def analyze_sample(sample_id: str):
    sample_path = pipeline.resolve_sample(sample_id)
    if sample_path is None:
        return jsonify({"error": "示例样本不存在，请先生成本地示例图。"}), 404
    payload = pipeline.analyze(sample_path)
    return jsonify(payload)


@app.get("/api/sample-files/<path:filename>")
def sample_file(filename: str):
    target = (config.samples_root / filename).resolve()
    if target.parent != config.samples_root.resolve() or not target.exists():
        return jsonify({"error": "示例图不存在。"}), 404
    return send_file(target)


@app.get("/api/results/<path:filename>")
def result_image(filename: str):
    target = (config.results_root / filename).resolve()
    if target.parent != config.results_root.resolve() or not target.exists():
        return jsonify({"error": "结果图不存在。"}), 404
    return send_file(target)


if __name__ == "__main__":
    app.run(host=config.host, port=config.port, debug=config.debug)
