# 启动和修改指南

本仓库保存的是魅族 21（SM8650）的 **r20 UniXNU + Darwin 22 过渡版**。
它能启动 UniXNU 菜单并进入已经验证过的 iOS 16.5 桌面，但还没有完成原生
DarwinBoot 迁移和 GPU 硬件加速。

## 需要自备的本地文件

仓库不包含 Apple 镜像、iOS 系统分区、Apple SDK、原厂固件或完整启动镜像。
构建者必须自行准备有权使用的输入文件。

至少需要：

1. `uefi-r19-clean-boot.img`，SHA256 必须是
   `20a1a8e0fc4374bb559bfb2e8aac070d25ae61ed758f95a7e45f948d13047505`。
2. 与该基线配套的 `SplashFbDxe-r19.efi`。
3. UniXNU，固定提交
   `04573c510c5fd4892ca6948739389141cc9e05f5`。
4. Mu-Silicium / EDK2 的 `Mu_Basecore` 源码。
5. `mkbootimg.py`。
6. 有权使用的 iOS 16.5 内核、ramdisk、加载器和设备树；r20 使用固定
   boot image 中已经验证的组合，不要自行替换其中任意一项。

`configs/local-inputs.example.env` 列出了所有可配置路径。

## 对应项目链接

| 项目或文件 | 公开来源 | 版本 |
| --- | --- | --- |
| UniXNU | [UniXNU/UniXNU](https://github.com/UniXNU/UniXNU) | `04573c510c5fd4892ca6948739389141cc9e05f5` |
| DarwinBoot | [UniXNU/DarwinBoot](https://github.com/UniXNU/DarwinBoot) | `3c75734014cdab0acd9541e88057b7606ee7ae08` |
| Mu-Silicium / EDK2 | [Project-Silicium/Mu-Silicium](https://github.com/Project-Silicium/Mu-Silicium) | 本地 `Mu_Basecore` 源码 |
| `mkbootimg.py` | [Mu-Silicium](https://github.com/Project-Silicium/Mu-Silicium) 的 `Resources/Scripts/` | 与所用基线配套 |
| OnePlus Ace 5 | [tycykp/UniXNU-OnePlus-Ace5](https://github.com/tycykp/UniXNU-OnePlus-Ace5) | `aaa100d19f6fb14e5897a7e496edf7838d4d4e9f` |
| 魅族 20 Classic | [RiverKawa271828/UniXNU-m2381](https://github.com/RiverKawa271828/UniXNU-m2381) | 参考实现 |
| 小米 14 | [lonzzi/UniXNU-houji](https://github.com/lonzzi/UniXNU-houji) | SM8650/A750 参考实现 |
| HackiOS | [oosexgang/hakios-xnu-kernel](https://github.com/oosexgang/hakios-xnu-kernel) | compatibility-chain 参考 |
| iOS Sweet | [dipa-studio/ios-sweet](https://github.com/dipa-studio/ios-sweet) | compatibility-chain 参考 |
| Apple XNU | [apple-oss-distributions/xnu](https://github.com/apple-oss-distributions/xnu) | ABI 参考 |
| SM8650 原厂图形源码 | [OnePlusOSS SM8650](https://github.com/OnePlusOSS/android_kernel_modules_and_devicetree_oneplus_sm8650) | `453d8875f815bf9dfad9035982861226a4823a6c` |

`uefi-r19-clean-boot.img`、`SplashFbDxe-r19.efi`、iOS 内核、ramdisk、
加载器、Apple SDK 和原厂固件没有可随本项目公开分发的统一下载源，必须按
`proprietary-files.txt` 的哈希和本地设备状态自行准备。

机器可读版本表见仓库根目录的 `sources.json`。

## 推荐目录

```text
workspace/
├── UniXNU/                  # 固定提交的 UniXNU
├── Mu-Silicium/
│   └── Mu_Basecore/         # EDK2 基础源码
├── meizu-baseline/
│   ├── uefi-r19-clean-boot.img
│   └── SplashFbDxe-r19.efi
├── unixnu-meizu21/          # 本仓库
└── build/
```

## 主机依赖

建议使用 Ubuntu 24.04。需要：

- Python 3.11+
- Git
- Clang/LLVM 18
- GCC、GNU Make、Flex、Bison、M4
- Device Tree Compiler（`dtc`）
- QEMU AArch64 和 AAVMF
- EDK2 BaseTools

## 配置和校验

```sh
cp configs/local-inputs.example.env local-inputs.env
. ./local-inputs.env
python3 scripts/verify-local-inputs.py
bash scripts/package.sh --check
```

校验会拒绝基线镜像哈希不符、splash 缺失、UniXNU 提交不符、EDK2 或
`mkbootimg.py` 缺失，以及关键主机工具缺失。

## 构建

```sh
bash scripts/package.sh
```

输出：

```text
../build/r20-transition/uefi-r20-unixnu-transition.img
../build/r20-transition/packaging-check.json
```

已验证的镜像 SHA256：

```text
d4b3d5f61bd2570470c7b67bd61222f23ee05c18adb69dd2bafa92ccc600699b
```

哈希不一致时不要刷机。先检查 `evidence/` 下的构建和 QEMU 日志。

## 刷机测试

以下命令只写入 `boot_b`，不会写 `super`：

```sh
fastboot devices
fastboot getvar current-slot
fastboot flash boot_b ../build/r20-transition/uefi-r20-unixnu-transition.img
fastboot reboot
```

刷机前必须备份原有 `boot_b`，保留已知正常镜像，并确认 fastboot 输出包含
`Writing 'boot_b' ... OKAY` 和 `Finished`。

**绝不能写入 `super`。** 它保存 iOS 根卷和 cryptex。不要修改分区表或
随意切换槽位。

## 修改代码

- `firmware/`：UniXNU 菜单与保留加载器之间的桥接。
- `configs/`：菜单配置和板级 defconfig。
- `profiles/`：iOS 16.5、Darwin 22 和 SM8650 配置。
- `scripts/`：输入准备、桥接构建、打包和证据检查。
- `patches/`：保留内核的补丁序列。
- `tests/`：XNUP 载荷解析测试。

每次修改后至少执行：

```sh
bash scripts/package.sh --check
bash scripts/package.sh
```

## 当前限制

- UniXNU 菜单在两秒后自动启动，菜单触摸尚未实现。
- 当前使用保留的 Darwin 22 加载器、内核和硬件路径。
- 原生 DarwinBoot 的 608/736 字节 ABI 尚未完成。
- A750 GPU、GMU、HFI 和 Metal 启动链尚未完成。
- 本仓库不是 iOS、Apple SDK 或原厂固件的分发渠道。

更详细的来源、哈希和验证边界见 `README.md`、`proprietary-files.txt` 和
`evidence/`。
