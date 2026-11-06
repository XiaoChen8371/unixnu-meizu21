#!/usr/bin/env python3
"""Record the independently copied kernel sources without changing the old tree."""
import hashlib, json, os, subprocess, tarfile
from pathlib import Path
device=Path(__file__).resolve().parents[1]
source=Path(os.environ.get('KERNEL_SOURCE_DIR',device.parent/'kernel-ios16')).resolve()
original=Path(os.environ.get(
    'KERNEL_ORIGINAL_DIR',
    device.parent/'hackios-upstream/xnu-src/xnu-8796.121.2',
)).resolve()
if source==original or not (source/'.git').is_dir():
    raise SystemExit('Requires an independent source copy')
out=device/'.cache/kernel-snapshot';out.mkdir(parents=True,exist_ok=True)
files=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=source).split(b'\0')
manifest={}; missing=[]
for name in sorted(set(os.fsdecode(n) for n in files if n)):
    if name.startswith('BUILD/') or '..' in Path(name).parts: raise SystemExit('Unexpected source path')
    p=source/name
    if p.is_symlink(): manifest[name]={'symlink':os.readlink(p)}
    elif p.is_file(): manifest[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
    else:missing.append(name)
report={'source':str(source),'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),
        'files':manifest,'deleted':missing,'kernel_rebuilt':False}
encoded=(json.dumps(report,sort_keys=True,indent=2)+'\n').encode()
digest=hashlib.sha256(encoded).hexdigest()
manifest_path=out/f'source-manifest-{digest[:16]}.json'
archive=out/f'source-{digest[:16]}.tar.gz'
manifest_path.write_bytes(encoded)
(device/'evidence/kernel-snapshot.json').write_text(json.dumps({
    'source':str(source),'base_commit':report['base_commit'],'source_files':len(manifest),
    'manifest_sha256':digest,'archive':str(archive),
    'independent_copy':True,'kernel_rebuilt':False,
    'retained_kernel_sha256':'94929bfb93911f89b19d81a370553a325ba997e97ebff8ddd2da4b2d1b249c13'},indent=2)+'\n')
(out/f'tracked-{digest[:16]}.patch').write_bytes(subprocess.check_output(['git','diff','--binary','HEAD'],cwd=source))
if not archive.exists():
    with tarfile.open(archive,'w:gz',dereference=False) as tar:
        for name in manifest: tar.add(source/name,arcname=name,recursive=False)
        tar.add(manifest_path,arcname='source-manifest.json')
with tarfile.open(archive,'r:gz') as tar:
    assert tar.extractfile('source-manifest.json').read()==encoded, 'Archive manifest mismatch'
print(f'Preserved {len(manifest)} kernel source files: {digest}')
