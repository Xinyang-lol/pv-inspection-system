"""Check packaged files without installing app dependencies or changing runtime data."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source_files(extension: str):
    for directory, folders, filenames in os.walk(ROOT):
        folders[:] = [name for name in folders if name not in {".git", ".venv", "__pycache__", "private", "datasets", "runtime", "runs", "archive"}]
        for filename in sorted(filenames):
            if filename.endswith(extension):
                yield Path(directory) / filename


def check_project(require_runtime: bool = False) -> dict:
    checks: list[str] = []
    errors: list[str] = []
    for source in source_files(".py"):
        try:
            ast.parse(source.read_text(encoding="utf-8-sig"), filename=str(source))
        except (SyntaxError, UnicodeError) as exc:
            errors.append(f"Python syntax: {source.relative_to(ROOT)}: {exc}")
    checks.append("Python syntax parsed")

    # Load the dependency-free configuration without creating runtime directories.
    namespace: dict = {"__file__": str(ROOT / "backend" / "config.py"), "__name__": "__main__"}
    exec(compile((ROOT / "backend" / "config.py").read_text(encoding="utf-8"), "config.py", "exec"), namespace)
    config = namespace["AppConfig"]()
    for key in ("frontend_root", "panel_model_path", "tile_classifier_model_path"):
        path = getattr(config, key)
        if not path.exists():
            errors.append(f"Missing configured path: {key}")
    checks.append("Frontend and required model paths checked")

    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    refs = re.findall(r'(?:src|href)="([^"?#]+)(?:\?[^\"]*)?"', html)
    for ref in refs:
        if not ref.startswith(("http:", "https:", "data:", "/")) and not (ROOT / "frontend" / ref).is_file():
            errors.append(f"Missing HTML asset: {ref}")
    css = (ROOT / "frontend" / "css" / "comon0.css").read_text(encoding="utf-8")
    for ref in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", css):
        if not ref.startswith(("http:", "https:", "data:")) and not (ROOT / "frontend" / "css" / ref.split("?")[0]).is_file():
            errors.append(f"Missing CSS asset: {ref}")
    checks.append("HTML and CSS asset references checked")

    for document in source_files(".md"):
        if "reference" in document.parts or "private" in document.parts:
            continue
        for link in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if "://" in link or link.startswith("#"):
                continue
            target = link.split("#")[0]
            if target and not (document.parent / target).exists():
                errors.append(f"Broken documentation link: {document.relative_to(ROOT)} -> {target}")
    checks.append("Current documentation links checked")

    weights = []
    for weight in sorted((ROOT / "models").rglob("*.pt")):
        weights.append({"path": weight.relative_to(ROOT).as_posix(), "bytes": weight.stat().st_size,
                        "sha256": hashlib.sha256(weight.read_bytes()).hexdigest()})
    if len(weights) != 4:
        errors.append(f"Expected four supplied weight files, found {len(weights)}")
    checks.append("Supplied weight files hashed; model execution not tested")

    runtime_missing = [path.as_posix() for path in (Path("backend/services/__init__.py"), Path("backend/services/pipeline.py"))
                       if not (ROOT / path).is_file()]
    if require_runtime and runtime_missing:
        errors.append("Missing original runtime source: " + ", ".join(runtime_missing))
    return {"static_ok": not errors, "checks": checks, "errors": errors, "weights": weights,
            "runtime_source_missing": runtime_missing, "runtime_verified": False,
            "note": "Static checks do not verify app imports, APIs, inference, training or GPU support."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-runtime", action="store_true")
    parser.add_argument("--report", type=Path, help="Optional JSON report destination.")
    args = parser.parse_args()
    report = check_project(args.require_runtime)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    print(payload)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")
    raise SystemExit(0 if report["static_ok"] else 1)


if __name__ == "__main__":
    main()
