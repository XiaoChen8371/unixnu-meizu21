#!/usr/bin/env bash
# Offline only. Neither this script nor its children invoke fastboot/adb.
set -euo pipefail
device=$(cd "$(dirname "$0")/.." && pwd)
work=$(cd "$device/.." && pwd)
unixnu="$work/UniXNU"
edk2=${UNIXNU_EDK2:-$work/Mu-Silicium/Mu_Basecore}
out="$work/build/bridge-debug"
mkdir -p "$out/Conf"
export WORKSPACE="$out" PACKAGES_PATH="$device:$unixnu/package:$edk2"
export EDK_TOOLS_PATH="$edk2/BaseTools" CONF_PATH="$out/Conf"
export PATH="$EDK_TOOLS_PATH/BinWrappers/PosixLike:$EDK_TOOLS_PATH/Source/C/bin:$PATH"
export CLANG_BIN=/usr/lib/llvm-18/bin/ PYTHON_COMMAND=python3
for f in target tools_def build_rule; do
  if [ ! -f "$CONF_PATH/$f.txt" ]; then cp "$EDK_TOOLS_PATH/Conf/$f.template" "$CONF_PATH/$f.txt"; fi
done
build -p "$device/firmware/MeizuBridge.dsc" -a AARCH64 -b DEBUG -t CLANGPDB -n 4 "$@"
