#!/usr/bin/env python3
"""Verify local, non-redistributable inputs before attempting an r20 build."""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

BOOT_SHA256 = "20a1a8e0fc4374bb559bfb2e8aac070d25ae61ed758f95a7e45f948d13047505"
UNIXNU_COMMIT = "04573c510c5fd4892ca6948739389141cc9e05f5"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(name, path):
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"missing file: {name}: {path}")


def main():
    root = Path(__file__).resolve().parents[1]
    unixnu = Path(os.environ.get("UNIXNU_DIR", root.parent / "UniXNU")).resolve()
    edk2 = Path(
        os.environ.get("UNIXNU_EDK2", root.parent / "Mu-Silicium/Mu_Basecore")
    ).resolve()
    baseline = Path(
        os.environ.get("MEIZU_BASELINE_DIR", root.parent / "meizu-baseline")
    ).resolve()
    boot = Path(
        os.environ.get("MEIZU_BASELINE_BOOT", baseline / "uefi-r19-clean-boot.img")
    ).resolve()
    splash = Path(
        os.environ.get("MEIZU_BASELINE_SPLASH", baseline / "SplashFbDxe-r19.efi")
    ).resolve()
    mkbootimg = Path(
        os.environ.get(
            "MKB00TIMG",
            root.parent / "Mu-Silicium/Resources/Scripts/mkbootimg.py",
        )
    ).resolve()

    require_file("clean r19 boot image", boot)
    actual = sha256(boot)
    if actual != BOOT_SHA256:
        raise SystemExit(
            f"r19 boot image SHA256 mismatch: expected {BOOT_SHA256}, got {actual}"
        )
    require_file("SplashFbDxe", splash)
    require_file("mkbootimg.py", mkbootimg)

    if not (unixnu / ".git").is_dir() or not (unixnu / "package/build.sh").is_file():
        raise SystemExit(f"invalid UniXNU checkout: {unixnu}")
    commit = subprocess.check_output(
        ["git", "-C", str(unixnu), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != UNIXNU_COMMIT:
        raise SystemExit(
            f"UniXNU commit mismatch: expected {UNIXNU_COMMIT}, got {commit}"
        )
    if not (edk2 / "BaseTools").is_dir():
        raise SystemExit(f"invalid EDK2/Mu_Basecore checkout: {edk2}")

    missing = [
        tool
        for tool in ("python3", "git", "dtc", "gcc", "qemu-system-aarch64")
        if not shutil.which(tool)
    ]
    clang_bin = Path(os.environ.get("CLANG_BIN", "/usr/lib/llvm-18/bin/"))
    if not (clang_bin / "clang").is_file():
        missing.append(str(clang_bin / "clang"))
    if missing:
        raise SystemExit("missing host tools: " + ", ".join(missing))

    print("Local input verification PASS")
    print(f"baseline: {boot}")
    print(f"splash:   {splash}")
    print(f"UniXNU:   {unixnu} @ {commit}")
    print(f"EDK2:     {edk2}")
    print(f"bootimg:  {mkbootimg}")


if __name__ == "__main__":
    main()
