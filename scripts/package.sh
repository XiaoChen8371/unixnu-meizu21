#!/usr/bin/env bash
# Meizu's transition packaging recipe. Offline; no flashing or partition writes.
set -euo pipefail
device=$(cd "$(dirname "$0")/.." && pwd)
work=$(cd "$device/.." && pwd)
unixnu=${UNIXNU_DIR:-$work/UniXNU}
baseline=${MEIZU_BASELINE_DIR:-$work/meizu-baseline}
baseline_boot=${MEIZU_BASELINE_BOOT:-$baseline/uefi-r19-clean-boot.img}
baseline_splash=${MEIZU_BASELINE_SPLASH:-$baseline/SplashFbDxe-r19.efi}
mkbootimg=${MKB00TIMG:-$work/Mu-Silicium/Resources/Scripts/mkbootimg.py}
export UNIXNU_DIR="$unixnu"
export UNIXNU_EDK2=${UNIXNU_EDK2:-$work/Mu-Silicium/Mu_Basecore}
mkdir -p "$device/evidence" "$device/.cache/inputs" "$work/build/menu-debug"
python3 "$device/scripts/configure.py" > "$device/evidence/configure.log" 2>&1
if [ "${1:-}" = --check ]; then
  python3 - "$device" "$baseline_boot" <<'PY'
import hashlib,json,sys,tomllib
from pathlib import Path
d,b=map(Path,sys.argv[1:]);pins=json.loads((d/'evidence/inputs.json').read_text())
assert hashlib.sha256(b.read_bytes()).hexdigest()==pins['baseline_r19_sha256']
assert tomllib.loads((d/'board.toml').read_text())['meizu_transition']['super_access']=='never-write'
print('Pinned baseline and protected storage policy PASS; no device access')
PY
  exit 0
fi
export UNIXNU_BUILD_DIR="$work/build/menu-debug"
export CLANG_BIN=${CLANG_BIN:-/usr/lib/llvm-18/bin/}
export JOBS=${MEIZU_JOBS:-4}
bash "$unixnu/package/build.sh" -b DEBUG -t CLANGPDB > "$device/evidence/menu-build.log" 2>&1
python3 "$device/scripts/prepare-assets.py" --boot "$baseline_boot" \
  --splash "$baseline_splash" \
  --menu "$UNIXNU_BUILD_DIR/Build/Out/AARCH64-DEBUG/UniXNU.efi" \
  --out "$device/.cache/inputs" > "$device/evidence/inputs.json"
bash "$device/scripts/build-bridge.sh" > "$device/evidence/bridge-build.log" 2>&1
cp "$work/build/bridge-debug/Build/MeizuBridge/DEBUG_CLANGPDB/AARCH64/MeizuBootBridge.efi" "$device/.cache/inputs/MeizuBootBridge.efi"
bash "$device/scripts/build-bridge.sh" -D MEIZU_QEMU_TEST=1 > "$device/evidence/bridge-qemu-build.log" 2>&1
mkdir -p "$device/.cache/qemu-esp/EFI/BOOT"
cp "$work/build/bridge-debug/Build/MeizuBridgeQemu/DEBUG_CLANGPDB/AARCH64/MeizuBootBridge.efi" "$device/.cache/qemu-esp/EFI/BOOT/BOOTAA64.EFI"
gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-sanitize-recover=all \
  "$device/tests/xnup.c" -o "$device/.cache/test-xnup"
python3 "$device/scripts/pack-transition.py" --bridge "$device/.cache/inputs/MeizuBootBridge.efi" \
  --boot "$baseline_boot" --out "$work/build/r20-transition" \
  --mkbootimg "$mkbootimg" > "$device/evidence/packaging-check.json"
"$device/.cache/test-xnup" "$work/build/r20-transition/payload.xnup" "$device/.cache/inputs/test-payload.xnup" > "$device/evidence/xnup-r20-test.log"
dtc -I dts -O dtb "$device/dts/meizu21-inventory.dts" -o "$device/.cache/meizu21-inventory.dtb" 2> "$device/evidence/dts-check.log"
python3 "$device/scripts/audit-handoff.py" > "$device/evidence/handoff-audit.log"
python3 "$unixnu/package/Scripts/qemu-run.py" "$device/.cache/qemu-esp" \
  --log "$device/evidence/qemu-menu.log" --screenshot "$device/evidence/qemu-menu.png" \
  --display-size 1080x2340 --expect 'MEIZU-BRIDGE: protocol handoff PASS' \
  --expect 'UNIXNU: config: 1 entries' --expect 'UNIXNU: ui: graphics 1080x2340' \
  --reject 'config error' --finish-on-expect \
  --timeout "${MEIZU_QEMU_TIMEOUT:-45}" > "$device/evidence/qemu-result.log" 2>&1
python3 "$unixnu/scripts/porting-record.py" check --device "$device"
cat "$device/evidence/packaging-check.json"
