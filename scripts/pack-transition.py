#!/usr/bin/env python3
"""Insert the small UniXNU bridge into the stable Splash PE's existing slot.
The inner FV keeps exactly the same file layout and length. No phone access.
"""
import argparse, hashlib, json, lzma, struct, subprocess, uuid
from pathlib import Path
from importlib.machinery import SourceFileLoader

sha=lambda b:hashlib.sha256(b).hexdigest()
u24=lambda b,o:int.from_bytes(b[o:o+3],'little')
a8=lambda n:(n+7)&~7
def sections(b,p,end):
    while p+4<=end:
        n=u24(b,p)
        if n<4 or p+n>end: raise ValueError('Section bounds')
        yield p,n,b[p+3]
        p=(p+n+3)&~3
def files(b):
    v=b.find(b'_FVH')-40
    if v<0: raise ValueError('FV header')
    n=struct.unpack_from('<Q',b,v+32)[0]; hlen=struct.unpack_from('<H',b,v+48)[0]
    if v+n>len(b) or sum(struct.unpack_from('<'+'H'*(hlen//2),b,v))%65536: raise ValueError('FV checksum')
    p=a8(v+hlen)
    while p+24<=v+n and b[p:p+24]!=b'\xff'*24:
        h=b[p:p+24]; size=u24(h,20)
        if size<24 or p+size>v+n or (sum(h)-h[17]-h[23])%256: raise ValueError('FFS header')
        if h[19]&0x40:
            if (sum(b[p+24:p+size])+h[17])%256: raise ValueError('FFS data checksum')
        elif h[17]!=0xaa: raise ValueError('FFS fixed checksum')
        yield p,size,str(uuid.UUID(bytes_le=bytes(h[:16]))),h[18]
        p=a8(p+size)
def ffs_header(h,n):
    h=bytearray(h)
    if h[19]&0x40: raise ValueError('Expected fixed data checksum')
    h[20:23]=n.to_bytes(3,'little'); h[16]=0
    h[16]=(-(sum(h)-h[17]-h[23]))&255
    return bytes(h)
def main():
    p=argparse.ArgumentParser();p.add_argument('--bridge',type=Path,required=True)
    p.add_argument('--boot',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mkbootimg',type=Path,required=True); a=p.parse_args()
    device=Path(__file__).resolve().parents[1]
    helper=SourceFileLoader('assets',str(device/'scripts/prepare-assets.py')).load_module()
    a.out.mkdir(parents=True,exist_ok=True); original=a.boot.read_bytes()
    if sha(original)!=helper.PINS['boot']: raise ValueError('Baseline r19 mismatch')
    shim,rd,dtb=helper.boot_parts(original); oldfd=rd[:0x400000]; oldpay=rd[0x400000:]
    inputs=device/'.cache/inputs'; loader=(inputs/'LegacyLoader.efi').read_bytes(); menu=(inputs/'UniXNU.efi').read_bytes()
    bridge=a.bridge.read_bytes(); helper.pe_length(bridge)
    if len(bridge)>len(loader): raise ValueError('Bridge exceeds existing loader slot')
    outer=list(files(oldfd));o,n,g,t=outer[1]
    s,sn,st=list(sections(oldfd,o+24,o+n))[0]
    if st!=2 or struct.unpack_from('<H',oldfd,s+20)[0]!=24: raise ValueError('LZMA GUID section')
    oldstream=oldfd[s+24:s+sn]; plain=lzma.decompress(oldstream,format=lzma.FORMAT_ALONE)
    inner=list(files(plain)); match=[f for f in inner if f[2]=='3b7e7a14-2c3d-4b2e-9a6d-5e1f8c4a7b9d']
    if len(match)!=1:raise ValueError('Splash FFS identity')
    f,fn,fg,ft=match[0]; q,qn,qt=[v for v in sections(plain,f+24,f+fn) if v[2]==0x10][0]
    pe=plain[q+4:q+qn];slot=pe.find(loader)
    if slot<0 or pe.find(loader,slot+1)>=0:raise ValueError('Stable embedded loader slot')
    changed=bytearray(plain);absolute=q+4+slot
    changed[absolute:absolute+len(loader)]=bridge+bytes(len(loader)-len(bridge))
    if list(files(changed))!=inner:raise ValueError('Inner FV file layout changed')
    unchanged=0
    for ff,fs,fg,ft in inner:
        if ff!=f:
            assert changed[ff:ff+fs]==plain[ff:ff+fs];unchanged+=1
    assert len(changed)==len(plain) and changed[:absolute]==plain[:absolute]
    assert changed[absolute+len(loader):]==plain[absolute+len(loader):]
    encoded=lzma.compress(bytes(changed),format=lzma.FORMAT_ALONE,filters=[
        {'id':lzma.FILTER_LZMA1,'dict_size':struct.unpack_from('<I',oldstream,1)[0],'lc':3,'lp':0,'pb':2}])
    encoded=encoded[:5]+struct.pack('<Q',len(changed))+encoded[13:]
    sec=bytearray(oldfd[s:s+24])+encoded;sec[:3]=len(sec).to_bytes(3,'little')
    ffs=ffs_header(oldfd[o:o+24],24+len(sec))+sec
    end=max(a8(o+n),a8(o+len(ffs)))
    if end>=0x3f0000 or oldfd[a8(o+n):end]!=b'\xff'*(end-a8(o+n)):raise ValueError('No outer FV space')
    fd=bytearray(oldfd);fd[o:end]=ffs+b'\xff'*(end-o-len(ffs))
    assert len(fd)==len(oldfd) and fd[:o]==oldfd[:o] and fd[end:]==oldfd[end:]
    list(files(fd))
    assert lzma.decompress(fd[s+24:s+len(sec)],format=lzma.FORMAT_ALONE)==changed
    olditems=helper.entries(oldpay)
    body=oldpay[8:-24]
    for name,data in [('unixnu',menu),('loader',loader)]:
        body+=struct.pack('<16sII',name.encode(),len(data),0)+data+bytes(-len(data)%16)
    body+=bytes(24);pay=struct.pack('<II',0x50554e58,len(body))+body
    newitems=helper.entries(pay)
    for k,v in olditems.items():assert newitems[k]==v
    assert len(pay)<0x3800000
    for name,data in [('fd-r20.bin',fd),('payload.xnup',pay),('ramdisk-r20.bin',fd+pay),
                      ('shim.bin',shim),('firmware.dtb',dtb)]: (a.out/name).write_bytes(data)
    output=a.out/'uefi-r20-unixnu-transition.img'
    subprocess.run(['python3',str(a.mkbootimg),'--header_version','2','--kernel',str(a.out/'shim.bin'),
        '--ramdisk',str(a.out/'ramdisk-r20.bin'),'--dtb',str(a.out/'firmware.dtb'),'--base','0',
        '--kernel_offset','0x8000','--ramdisk_offset','0x1000000','--tags_offset','0x100',
        '--dtb_offset','0x1f00000','--pagesize','4096','--os_version','17.0.0','--os_patch_level','2035-06',
        '--cmdline','console=null','-o',str(output)],check=True)
    result=output.read_bytes();ns,nr,nd=helper.boot_parts(result)
    assert ns==shim and nr==fd+pay and nd==dtb
    # Only ramdisk length and the boot digest may differ in the Android v2 header.
    h1=bytearray(original[:1660]);h2=bytearray(result[:1660])
    for h in (h1,h2):h[16:20]=bytes(4);h[576:608]=bytes(32)
    assert h1==h2
    report={'image':output.name,'image_sha256':sha(result),'bytes':len(result),
        'mode':'UniXNU + Darwin22 compatibility; native DarwinBoot migration pending',
        'baseline_r19_sha256':sha(original),'bridge_sha256':sha(bridge),'bridge_bytes':len(bridge),
        'menu_sha256':sha(menu),'legacy_loader_sha256':sha(loader),'kernel_sha256':sha(newitems['kernel']),
        'fd_sha256':sha(fd),'inner_files':len(inner),'unchanged_inner_files':unchanged,
        'inner_fv_layout_unchanged':True,'kernel_root_cmdline_unchanged':True,
        'shim_dtb_memorymap_unchanged':True,'super_access':'none','flashed':False,'hardware_tested':False}
    (a.out/'packaging-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
