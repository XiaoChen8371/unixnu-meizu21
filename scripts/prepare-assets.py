#!/usr/bin/env python3
"""Pin the transition payload to r19. Read only original inputs; no device access."""
import argparse, hashlib, json, struct, tomllib
from pathlib import Path

sha = lambda b: hashlib.sha256(b).hexdigest()
PINS = {
    'boot': '20a1a8e0fc4374bb559bfb2e8aac070d25ae61ed758f95a7e45f948d13047505',
    'kernel': '94929bfb93911f89b19d81a370553a325ba997e97ebff8ddd2da4b2d1b249c13',
    'loader': '0be90c0061279e2f3c528b6310a1d6091735f8e7fbd410a0fa28b757dc5481fe',
}

def boot_parts(b):
    if b[:8] != b'ANDROID!': raise ValueError('Android header')
    ks, _, rs = struct.unpack_from('<III', b, 8)
    page, version = struct.unpack_from('<II', b, 36)
    if (page,version) != (4096,2): raise ValueError('Expected stable header v2')
    ro = (page+ks+page-1)//page*page
    ds = struct.unpack_from('<I', b, 1648)[0]
    do = (ro+rs+page-1)//page*page
    if do+ds != len(b):
        if do+ds > len(b) or any(b[do+ds:]): raise ValueError('Truncated/trailing data')
    return b[page:page+ks], b[ro:ro+rs], b[do:do+ds]

def entries(b):
    magic, size = struct.unpack_from('<II', b)
    if magic != 0x50554e58 or size+8 != len(b): raise ValueError('XNUP header')
    out = {}; p = 8
    while p+24 <= len(b):
        name, n, flags = struct.unpack_from('<16sII', b, p); p += 24
        if not name[0]:
            if p != len(b): raise ValueError('XNUP end')
            return out
        name = name.rstrip(b'\0').decode()
        if flags or name in out or p+n > len(b): raise ValueError('XNUP entry')
        out[name] = b[p:p+n]; p += (n+15)&~15
    raise ValueError('No XNUP end')

def pe_length(b):
    nt = struct.unpack_from('<I', b, 60)[0]
    if b[:2] != b'MZ' or b[nt:nt+4] != b'PE\0\0': raise ValueError('PE')
    machine, count = struct.unpack_from('<HH', b, nt+4)
    optsize = struct.unpack_from('<H', b, nt+20)[0]
    if machine != 0xaa64: raise ValueError('Expected AArch64 PE')
    sec = nt+24+optsize
    return max(struct.unpack_from('<I', b, sec+i*40+20)[0] +
               struct.unpack_from('<I', b, sec+i*40+16)[0] for i in range(count))

def c_array(name, b):
    lines = [f'CONST UINT8 {name}[] = {{']
    lines += ['  '+','.join(f'0x{x:02x}' for x in b[i:i+24])+',' for i in range(0,len(b),24)]
    return '\n'.join(lines) + f'\n}};\nCONST UINTN {name}Size = sizeof({name});\n'

def fixture(args):
    out = b''
    for name,data in [('kernel',struct.pack('<I',0xfeedfacf)+bytes(60)),('ramdisk',b'test root'),('cmdline',args.encode()+b'\0')]:
        out += struct.pack('<16sII', name.encode(),len(data),0)+data+bytes(-len(data)%16)
    out += bytes(24)
    return struct.pack('<II',0x50554e58,len(out))+out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--boot',type=Path,required=True)
    ap.add_argument('--splash',type=Path,required=True); ap.add_argument('--menu',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); args=ap.parse_args()
    device = Path(__file__).resolve().parents[1]; args.out.mkdir(parents=True,exist_ok=True)
    original=args.boot.read_bytes()
    if sha(original) != PINS['boot']: raise ValueError('r19 baseline mismatch')
    shim, rd, dtb = boot_parts(original); payload=rd[0x400000:]; items=entries(payload)
    if set(items) != {'kernel','ramdisk','cmdline'} or sha(items['kernel']) != PINS['kernel']:
        raise ValueError('Kernel/payload mismatch')
    config=(device/'configs/unixnu.toml').read_bytes()
    line=tomllib.loads(config.decode())['entry'][0]['args']
    if items['cmdline'] != line.encode()+b'\0': raise ValueError('Config differs from retained XNUP')
    splash=args.splash.read_bytes(); matches=[]
    for offset in range(1,len(splash)-128):
        if splash[offset:offset+2] != b'MZ': continue
        try:
            length=pe_length(splash[offset:]); image=splash[offset:offset+length]
            if sha(image) == PINS['loader']: matches.append(image)
        except (ValueError,struct.error): pass
    if len(matches) != 1: raise ValueError('Exact stable embedded loader not found')
    loader=matches[0]; menu=args.menu.read_bytes(); pe_length(menu)
    assets={'gBootConfig':config,'gUniXnuImage':menu,'gTestPayload':fixture(line)}
    header='#include <Uefi.h>\n'
    source='#include "BridgeAssets.h"\n'
    for name,data in assets.items():
        if name != 'gBootConfig':
            header += '#ifdef MEIZU_QEMU_TEST\n'
            source += '#ifdef MEIZU_QEMU_TEST\n'
        header += f'extern CONST UINT8 {name}[];\nextern CONST UINTN {name}Size;\n'
        source += c_array(name,data)
        if name != 'gBootConfig':
            header += '#endif\n'; source += '#endif\n'
    header += 'extern CONST CHAR16 gExpectedArgs[];\nextern CONST CHAR8 gExpectedAsciiArgs[];\nextern CONST UINTN gExpectedKernelSize, gExpectedMenuSize, gExpectedLoaderSize;\n'
    source += f'CONST CHAR16 gExpectedArgs[] = L"{line}";\nCONST CHAR8 gExpectedAsciiArgs[] = "{line}";\n'
    source += f'CONST UINTN gExpectedKernelSize = {len(items["kernel"])};\n'
    source += f'CONST UINTN gExpectedMenuSize = {len(menu)};\nCONST UINTN gExpectedLoaderSize = {len(loader)};\n'
    (device/'firmware/BridgeAssets.h').write_text(header)
    (device/'firmware/BridgeAssets.c').write_text(source)
    for name,data in [('shim.bin',shim),('fd-r19.bin',rd[:0x400000]),('payload.xnup',payload),
                      ('firmware.dtb',dtb),('LegacyLoader.efi',loader),('kernel.macho',items['kernel']),
                      ('UniXNU.efi',menu),('test-payload.xnup',assets['gTestPayload'])]:
        (args.out/name).write_bytes(data)
    manifest={'baseline_r19_sha256':sha(original),'kernel_sha256':sha(items['kernel']),
              'loader_sha256':sha(loader),'menu_sha256':sha(menu),'cmdline':line,
              'mode':'UniXNU boot manager + UNIXNU_LOADER_PROTOCOL + Darwin22 compatibility',
              'native_darwinboot':False,'hardware_tested':False,'flashed':False,
              'super_write_allowed':False,'boot_a_write_allowed':False}
    (args.out/'inputs.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
if __name__ == '__main__': main()
