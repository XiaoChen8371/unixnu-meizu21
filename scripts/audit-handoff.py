#!/usr/bin/env python3
"""Audit actual ABI declarations and unchanged memory-map source, without a phone."""
import ctypes as C
import hashlib, json, os, re, lzma, uuid
from importlib.machinery import SourceFileLoader
from pathlib import Path
d=Path(__file__).resolve().parents[1];w=d.parent
source=Path(os.environ.get('KERNEL_SOURCE_DIR',w/'kernel-ios16')).resolve()
unixnu=Path(os.environ.get('UNIXNU_DIR',w/'UniXNU')).resolve()
edk2=Path(os.environ.get('UNIXNU_EDK2',w/'Mu-Silicium/Mu_Basecore')).resolve()
kernel_header=(source/'pexpert/pexpert/arm64/boot.h').read_text()
native_header=(unixnu/'drivers/DarwinBoot/DarwinBootPkg/Driver/BootArgs.h').read_text()
kernel_line=int(re.search(r'#define\s+BOOT_LINE_LENGTH\s+(\d+)',kernel_header)[1])
native_line=int(re.search(r'CommandLine\[(\d+)\]',native_header)[1])
def layout(n):
    class Args(C.LittleEndianStructure):
        _fields_=[('Revision',C.c_uint16),('Version',C.c_uint16),
                  ('VirtualBase',C.c_uint64),('PhysicalBase',C.c_uint64),
                  ('MemorySize',C.c_uint64),('TopOfKernelData',C.c_uint64),
                  ('Video',C.c_uint64*6),('MachineType',C.c_uint32),
                  ('DeviceTree',C.c_uint64),('DeviceTreeLength',C.c_uint32),
                  ('CommandLine',C.c_char*n),('BootFlags',C.c_uint64),('MemorySizeActual',C.c_uint64)]
    return {'bytes':C.sizeof(Args),'command_line_bytes':n,'device_tree_offset':Args.DeviceTree.offset,
            'command_line_offset':Args.CommandLine.offset,'memory_size_actual_offset':Args.MemorySizeActual.offset}
k=layout(kernel_line);u=layout(native_line)
assert k['bytes']==736 and k['memory_size_actual_offset']==0x2d8
assert u['bytes']==1152 and u['memory_size_actual_offset']==0x478
assert k['device_tree_offset']==u['device_tree_offset']==0x60
record={'retained_kernel':k,'native_darwinboot':u,'compatible_without_porting':False,
        'remaining':['608-byte command line and 736-byte boot_args',
        '32 MiB/16 KiB placement and retained virtual-base mapping',
        'actual contiguous allocation versus 6 GiB reported memory and ADT dram policy',
        'watchdog, ADT, root and HID/userland services; kernel return context ownership'],
        'native_darwinboot_enabled':False}
(d/'evidence/native-abi-audit.json').write_text(json.dumps(record,indent=2)+'\n')
p=edk2/'Platforms/Meizu/meizu21Pkg/Library/MemoryMapLib/MemoryMapLib.c'
raw=p.read_bytes();text=raw.decode()
text=re.sub(r'/\*.*?\*/','',text,flags=re.S);text=re.sub(r'//[^\n]*','',text)
ranges=[]
for name,start,length in re.findall(r'\{\s*"([^"]+)"\s*,\s*(0x[\da-fA-F]+)\s*,\s*(0x[\da-fA-F]+)',text):
    a=int(start,16);n=int(length,16);assert n>0
    ranges.append({'name':name,'start':a,'bytes':n,'end':a+n})
ranges.sort(key=lambda r:r['start'])
for left,right in zip(ranges,ranges[1:]):
    assert left['end']<=right['start'],f"Memory overlap: {left['name']} / {right['name']}"
assert any(r['start']==0xf0000000 and r['bytes']==0x3800000 for r in ranges)
(d/'evidence/memorymap-check.json').write_text(json.dumps({'source':str(p),
    'source_sha256':hashlib.sha256(raw).hexdigest(),'source_modified':False,'regions':ranges,
    'overlaps':[],'firmware_memorymap_file_changed':False},indent=2)+'\n')
helper=SourceFileLoader('transition_pack',str(d/'scripts/pack-transition.py')).load_module()
fd=(d/'.cache/inputs/fd-r19.bin').read_bytes()
o,n,_,_=list(helper.files(fd))[1]
s,sn,_=list(helper.sections(fd,o+24,o+n))[0]
inner=lzma.decompress(fd[s+24:s+sn],format=lzma.FORMAT_ALONE)
apriori=[f for f in helper.files(inner) if f[2]=='fc510ee7-ffdc-11d4-bd41-0080c73c8881']
assert len(apriori)==1
f,fn,_,_=apriori[0]
q,qn,_=[x for x in helper.sections(inner,f+24,f+fn) if x[2]==0x19][0]
raw=inner[q+4:q+qn];assert len(raw)%16==0
order=[str(uuid.UUID(bytes_le=raw[i:i+16])) for i in range(0,len(raw),16)]
timer='49ea041e-6752-42ca-b0b1-7344fe2546b7'
splash='3b7e7a14-2c3d-4b2e-9a6d-5e1f8c4a7b9d'
assert timer in order and (splash not in order or order.index(timer)<order.index(splash))
(d/'evidence/boot-order-check.json').write_text(json.dumps({'source':'exact stable DEBUG FD APRIORI',
    'timer_guid':timer,'timer_apriori_index':order.index(timer),'splash_in_apriori':splash in order,
    'timer_precedes_splash_dispatch':True,'timer_runtime_verified_on_phone':False,
    'order':order},indent=2)+'\n')
print(f'ABI mismatch documented; {len(ranges)} nonoverlapping active memory regions; stable timer dispatch precedes Splash; no source mutation')
