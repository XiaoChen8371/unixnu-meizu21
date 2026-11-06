#!/usr/bin/env python3
"""Install this device-owned OS profile into the isolated UniXNU checkout."""
import json, os, subprocess, sys
from pathlib import Path
device=Path(__file__).resolve().parents[1]
root=Path(os.environ.get('UNIXNU_DIR', device.parent/'UniXNU')).resolve()
name='ios-16.5-meizu-darwin22'
target=device/'profiles/os'/name
link=root/'profiles/os'/name
if link.is_symlink():
    if link.resolve()!=target: raise SystemExit('OS profile symlink belongs to another tree')
elif link.exists(): raise SystemExit('Refusing to replace an existing OS profile')
else: link.symlink_to(target, target_is_directory=True)
subprocess.run([sys.executable,str(root/'unixnu'),'defconfig','meizu21_transition_defconfig','-D',str(device)],check=True,cwd=root)
status=subprocess.check_output([sys.executable,str(root/'unixnu'),'status','--json','-D',str(device)],cwd=root,text=True)
(device/'evidence/resolved-status.json').write_text(status)
# Resolve/assemble only the selected components. Unlike upstream's general
# prepare(), this stage does not initialize unrelated driver submodules.
sys.path.insert(0,str(root/'scripts'))
from unixnu.cli import parser
from unixnu.config import Context
from unixnu import feeds, tree
ctx=Context(parser().parse_args(['tree','-D',str(device)]))
modules=feeds.resolve(ctx)
for m in modules.values():
    if m.kind!='refer' and m.path is None: raise SystemExit(f'Pinned component missing: {m.name}')
tree.assemble(ctx,modules)
print('Meizu Darwin22 profile resolved; selected tree assembled; native kernel step is not run')
