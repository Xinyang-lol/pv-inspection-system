"""Archive every project file except delivery output, and verify content hashes."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'delivery'
OUTPUT.mkdir(exist_ok=True)
archive = OUTPUT / 'PV_Project_Complete.zip'
files = sorted(p for p in ROOT.rglob('*') if p.is_file() and OUTPUT not in p.parents)
manifest = []
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as target:
    for index, path in enumerate(files, 1):
        relative = path.relative_to(ROOT).as_posix()
        digest = hashlib.sha256()
        size = 0
        with path.open('rb') as source, target.open('PV_Project/' + relative, 'w', force_zip64=True) as dest:
            while chunk := source.read(1024 * 1024):
                dest.write(chunk)
                digest.update(chunk)
                size += len(chunk)
        manifest.append({'path': relative, 'size': size, 'sha256': digest.hexdigest()})
        if index % 5000 == 0:
            print(f'Packed {index}/{len(files)}', flush=True)
    target.writestr('PV_Project/PACKAGE_MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2))
print('Verifying every archived file...', flush=True)
with zipfile.ZipFile(archive) as packaged:
    assert len(packaged.infolist()) == len(manifest) + 1
    for item in manifest:
        digest = hashlib.sha256()
        with packaged.open('PV_Project/' + item['path']) as source:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
        assert digest.hexdigest() == item['sha256'], item['path']
with archive.open('rb') as source:
    checksum = hashlib.file_digest(source, 'sha256').hexdigest()
(OUTPUT / (archive.name + '.sha256')).write_text(checksum + '  ' + archive.name + '\n', encoding='ascii')
summary = {'archive': str(archive), 'files': len(manifest), 'source_bytes': sum(x['size'] for x in manifest), 'archive_bytes': archive.stat().st_size, 'sha256': checksum, 'verification': 'All file SHA-256 hashes and ZIP CRC verified', 'excluded': ['delivery/ (archive output only)']}
(OUTPUT/'package_report.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
