#!/usr/bin/env python3
"""Record actual host results without promoting retained phone results to r20."""
import json, subprocess
from pathlib import Path
d=Path(__file__).resolve().parents[1]
rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=d,text=True).strip()
q=lambda x:json.dumps(x,ensure_ascii=False)
areas=[
 ('configuration','host-verified',[],['board.toml','feeds.toml','configs/**','profiles/**','unixnu.lock'],
  'SM8650, retained iOS16.5/Darwin22.5, source pins in unixnu.lock.',
  'Format 2 resolves the custom OS profile; inherited Darwin23 archives are explicitly replaced.',
  'The selected native DarwinBoot source is for review only; stage 1 uses the board protocol adapter.',
  'Replace retained drivers with ABI-audited native component recipes.', 'configure.log'),
 ('firmware','host-verified',[],['firmware/**','scripts/build-bridge.sh','proprietary-files.txt'],
  'Exact r19 DEBUG FD; real UniXNU 04573c5; retained loader SHA0be90c00; physical FB E3940000.',
  'DEBUG menu and production bridge compile; the bridge fits the existing embedded-loader slot.',
  'No r20 hardware boot. Current original firmware sources diverge from the stable binary.',
  'Confirm menu and kernel handoff on Meizu21 after the owner returns.', 'packaging-check.json'),
 ('cpu','implemented',[],['dts/**'],
  'Retained loader uses GICD17100000/GICR17180000, core shift8, and default cpus=1.',
  'CPU/interrupt code is preserved in the independent kernel snapshot; no SMP behavior changed.',
  'No new native ArmCpu integration or SMP verification.',
  'Preserve the working primary-core path while auditing native GIC/timer ABI.', 'kernel-snapshot.json'),
 ('memory','host-verified',[],['firmware/Xnup.h','tests/xnup.c'],
  'FD A4000000+400000, payload F0000000+3800000, retained kernel window B0000000..D8000000.',
  'All firmware file offsets and MemoryMap stay unchanged; bounded parser passes 100000 mutations.',
  'QEMU does not establish DMA or SMMU behavior on SM8650.',
  'Audit native DarwinBoot placement against 16KiB pages and actual free windows.', 'xnup-r20-test.log'),
 ('storage','implemented',[],['board.toml','scripts/package.sh'],
  'Existing UFS/APFS root and cryptex occupy protected super; boot_a must remain intact.',
  'Packaging carries forward the exact small root ramdisk and meizu_ufs/root_apfs arguments.',
  'No root-image transformation, new partition geometry, userdata recipe or storage hardware test.',
  'After menu validation, confirm existing root still mounts; keep super immutable.', 'inputs.json'),
 ('display','host-verified',[],['configs/unixnu.toml','dts/**'],
  'Physical 1080x2340, BGRx32, stride4320, framebuffer E3940000.',
  'Real UniXNU renders a portrait menu at this geometry in QEMU; r16 Dock correction is retained.',
  'QEMU validates menu layout, not phone panel presentation, backlight or acceleration.',
  'Check menu and Dock on the phone without changing memory reservations.', 'qemu-result.log'),
 ('input','implemented',[],['configs/meizu21_transition_defconfig'],
  'Goodix GPIO48/49/50/51, reset161, IRQ162; raw coordinates10800x23400; TCS0 power path.',
  'Existing persistent quiet touch kernel and libhakios/backboardd bridge are preserved.',
  'r20 has not been phone-tested; touch input for the UEFI menu is not implemented.',
  'Verify repeated iOS touches after r20 boot before replacing the HID path.', 'kernel-snapshot.json'),
 ('gpu','planned',[],['README.md'],
  'A750/SM8650; native DT profiles43051400 and43051401; stock Meizu firmware pins preserved locally.',
  'GPU probe remains off. Neither A740 rendering nor Ace5 preparation proves A750 rendering here.',
  'No Meizu GPU power/SMMU/GMU/HFI/CP submission, frontend ABI or Metal verification.',
  'Read real SoC/GPU revision first, then port power and memory ownership before firmware execution.', 'inputs.json'),
 ('network','planned',[],['README.md'],
  'Native WLAN adaptation and firmware transport are not migrated by the boot manager.',
  'No networking driver from another board is enabled in this transition.',
  'No working network claim or new radio operation.',
  'Inventory Meizu WLAN transport/firmware after the boot/GPU migration stage.', None),
 ('audio','planned',[],['README.md'],
  'SM8650 DSP/codec routing requires board-specific firmware and service adaptation.',
  'Existing code is preserved; no Ace5 audio or modem initialization is imported.',
  'No audio playback/capture result.',
  'Audit actual board audio resources and services before enabling a native driver.', None),
 ('power','implemented',[],['README.md'],
  'Approved touch rails: ldob9=2960mV, ldob12=1800mV, HPM7; verified TCS0 response masks.',
  'The working touch voltage/ACK/recovery implementation remains in the retained kernel.',
  'No GPU rail write, new PMIC configuration, battery or suspend migration.',
  'Preserve existing touch power behavior; audit GPU resource ownership separately.', 'kernel-snapshot.json'),
 ('packaging','host-verified',[],['scripts/pack-transition.py','scripts/prepare-assets.py','scripts/package.sh','.gitignore'],
  'Pinned complete r19 image, exact legacy loader, current linked kernel, stock DTB, DEBUG menu.',
  'Repacked image is unpacked and compared; kernel/root/cmdline/shim/DTB remain exact.',
  'r20 unflashed; native UniXNU userdata, generic payload and bootshim recipes are not used.',
  'Device-test r20 boot_b while retaining the complete r16 rollback.', 'packaging-check.json'),
 ('diagnostics','host-verified',['DarwinBoot'],['scripts/configure.py','scripts/preserve-kernel.py','scripts/update-record.py','scripts/audit-handoff.py','evidence/**','AGENTS.md'],
  'Logs include production DEBUG builds, bounded-parser sanitizers and QEMU menu/protocol receiver.',
  'The QEMU receiver exits before any phone kernel or hardware operation. Sources and image pins are recorded.',
  'Host evidence must not be labelled hardware verification; native DarwinBoot ABI is still incompatible.',
  'Record the first phone menu/kernel/desktop checkpoint with image SHA after the owner returns.', 'qemu-result.log'),
]
lines=['schema_version = 1','[device]','name = "meizu21"','soc = "SM8650"',
       'os_profile = "ios-16.5-meizu-darwin22"',
       'summary = "UniXNU transition: host menu/protocol verified; retained Darwin22 hardware path; r20 not device-tested."']
for ident,status,components,paths,inputs,findings,limits,next_action,ref in areas:
    lines += ['', '[[area]]',f'id = {q(ident)}',f'status = {q(status)}',
              f'components = {q(components)}',f'paths = {q(paths)}',f'inputs = {q([inputs])}',
              f'configuration = {q([findings])}',
              f'procedure = {q(["Run scripts/package.sh --check, then scripts/package.sh; inspect the referenced evidence."])}',
              f'findings = {q([findings])}',f'completion = {q([next_action])}',
              f'limits = {q([limits])}',f'next_action = {q([next_action])}']
    if ref:
        evidence={'kind':'host' if status=='host-verified' else 'source','reference':f'evidence/{ref}','result':findings}
        if status=='host-verified':evidence.update(command='bash scripts/package.sh',revision=rev)
        lines += ['evidence = [{ '+', '.join(f'{k} = {q(v)}' for k,v in evidence.items())+' }]']
    else: lines += ['evidence = []']
(d/'porting.toml').write_text('\n'.join(lines)+'\n')
print('Recorded 13 areas; no r20 device-verified status assigned')
