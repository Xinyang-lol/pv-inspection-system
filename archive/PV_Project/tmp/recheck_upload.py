import json
from pathlib import Path
from backend.config import load_config
from backend.services.pipeline import AnalysisPipeline
cfg = load_config()
p = AnalysisPipeline(cfg)
path = Path(r"D:\大创yolo\backend\runtime\uploads\ABUIABACGAAgipOOuwYo5LTKggcw0AU4lQM.jpg")
result = p.analyze(path)
summary = result['analysis']['result']['summary']
with open(r"D:\大创yolo\tmp\latest_upload_reanalysis.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
