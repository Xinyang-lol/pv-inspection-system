from pathlib import Path
import ast, io, json, sys, tempfile
from dataclasses import replace
from importlib.metadata import version
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend import app as server
from backend.services.pipeline import AnalysisPipeline
report = {"python": sys.version, "checks": []}
for base in ('backend', 'tools'):
    for path in (ROOT/base).rglob('*.py'):
        ast.parse(path.read_text(encoding='utf-8-sig'))
report['checks'].append('Python syntax OK')
with tempfile.TemporaryDirectory(prefix='pv-delivery-') as temp:
    runtime = Path(temp)
    cfg = replace(server.config, runtime_root=runtime, uploads_root=runtime/'uploads', results_root=runtime/'results', history_path=runtime/'history.json')
    cfg.ensure_runtime_dirs()
    server.config = cfg
    server.pipeline = AnalysisPipeline(cfg)
    server.app.testing = True
    client = server.app.test_client()
    for route in ['/', '/js/jquery.js', '/js/echarts.min.js', '/js/js.js', '/css/comon0.css', '/api/health', '/api/dashboard', '/api/samples']:
        response = client.get(route)
        assert response.status_code == 200, route
        response.close()
        report['checks'].append(route + ' OK')
    report['model_status'] = client.get('/api/health').get_json()
    assert report['model_status']['runtime_mode'] == 'yolo-tile'
    sample = next((ROOT/'老师给的'/'yolo8 seg training data'/'Dataset'/'test'/'images').glob('*.jpg'))
    response = client.post('/api/analyze', data={'image': (io.BytesIO(sample.read_bytes()), sample.name)}, content_type='multipart/form-data')
    assert response.status_code == 200, response.data[:1000]
    payload = response.get_json()
    report['analysis'] = payload['analysis']
    results = list(cfg.results_root.glob('*.png'))
    assert results, 'No result image'
    result_response = client.get('/api/results/' + results[0].name)
    assert result_response.status_code == 200
    result_response.close()
    report['checks'].append('Real trained models: upload, inference and result image OK')
    server.pipeline = AnalysisPipeline(replace(cfg, force_demo_mode=True))
    response = client.post('/api/analyze-sample/dust-heavy')
    assert response.status_code == 200
    report['checks'].append('Demo sample inference OK')
(ROOT/'validation_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
packages = ['flask', 'numpy', 'pillow', 'ultralytics', 'torch', 'torchvision', 'PyYAML']
(ROOT/'delivery_environment.txt').write_text('Python '+sys.version+'\n'+'\n'.join(p+'=='+version(p) for p in packages)+'\n', encoding='utf-8')
print(json.dumps({'checks': report['checks'], 'mode': report['model_status']['runtime_mode']}, ensure_ascii=False))
