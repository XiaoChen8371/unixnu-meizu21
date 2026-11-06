# UniXNU · meizu21

魅族 21（SM8650 / Snapdragon 8 Gen 3）的 UniXNU 非官方设备适配。

项目保留 iOS 16.5 / Darwin 22 的已经验证启动链，目标是逐步替换为原生
DarwinBoot、板级驱动和 GPU 图形栈。

[启动指南](docs/STARTUP.md) ·
[构建](docs/BUILDING.md) ·
[刷机与恢复](docs/FLASHING.md) ·
[功能状态](docs/STATUS.md) ·
[架构](docs/ARCHITECTURE.md) ·
[开发指南](docs/DEVELOPMENT.md) ·
[问题反馈](https://github.com/XiaoChen8371/unixnu-meizu21/issues)

> 开发阶段项目，不适合作为日常系统。刷机和替换分区可能导致数据丢失。
> 构建成功或主机测试通过不代表硬件功能已经可用。

## 目标设备

| 项目 | 配置 |
| --- | --- |
| 机型 | 魅族 21（meizu21） |
| SoC | Qualcomm SM8650，Snapdragon 8 Gen 3 |
| CPU | ARM64 |
| 存储 | UFS |
| 显示与触控 | 1080×2340，Goodix |
| iOS | 16.5 |
| Darwin | 22 |
| 启动 | Mu-Silicium DEBUG UEFI → bridge → UniXNU → retained loader → XNU |

## 功能状态

| 功能 | 状态 | 说明 |
| --- | --- | --- |
| UniXNU 菜单 | 已验证 | 真实 UniXNU 构建，1080×2340 |
| iOS 桌面 | 已验证 | r20 正常版，无调试覆盖 |
| 显示 | 已验证 | 面板高度、Dock 和触控坐标已校正 |
| 触控 | 已验证 | 点击和滑动正常 |
| UFS / APFS | 已验证 | 保留 native UFS 与根卷路径 |
| GPU | 未完成 | 实验代码只保留在本地，不含在正常版 |
| Wi-Fi / 音频 / 蜂窝 | 未实现 | 见 [功能状态](docs/STATUS.md) |

## 启动链

```text
ABL
  -> clean shim
  -> exact DEBUG UEFI firmware
  -> MeizuBootBridge
  -> UniXNU menu
  -> UNIXNU_LOADER_PROTOCOL
  -> retained Darwin 22 loader
  -> retained XNU
  -> iOS 16.5
```

当前阶段由 UniXNU 提供菜单和加载协议；已经验证的 Darwin 22 加载器、内核、
UFS、显示和触摸路径继续保留。这不是已经完成的原生 UniXNU 平台迁移。

## 快速开始

```sh
git clone https://github.com/XiaoChen8371/unixnu-meizu21.git
cd unixnu-meizu21
cp configs/local-inputs.example.env local-inputs.env
. ./local-inputs.env
python3 scripts/verify-local-inputs.py
bash scripts/package.sh --check
bash scripts/package.sh
```

完整目录和输入要求见 [启动指南](docs/STARTUP.md)。镜像、Apple SDK、原厂
固件和分区备份需要自行准备，不能从本仓库下载。

## 代码导航

| 路径 | 内容 |
| --- | --- |
| `board.toml`、`feeds.toml`、`porting.toml` | 板级、来源和移植记录 |
| `configs/` | UniXNU 配置与本地输入模板 |
| `dts/` | meizu21 inventory DTS |
| `profiles/` | SM8650、iOS 16.5 和 Darwin 22 profile |
| `firmware/` | UniXNU / retained loader 桥接 |
| `patches/xnu/` | 保留内核补丁和顺序 |
| `scripts/` | 配置、准备、构建、打包和校验 |
| `tests/` | XNUP 与主机测试 |
| `evidence/` | 输入哈希、打包检查和验证记录 |
| `docs/` | 启动、构建、刷机、架构和开发文档 |
| `archive/` | r20 历史源码快照 |
| `unixnu.lock` | 上游固定版本 |

## 验证

```sh
python3 -m py_compile scripts/*.py
bash -n scripts/*.sh
python3 scripts/verify-local-inputs.py
bash scripts/package.sh --check
```

在实际设备上必须单独验证菜单、内核交接、桌面、重复触控和回退。主机测试、
QEMU 和构建检查不能替代真机结果。

## 刷机边界

- 只测试 `boot_b`。
- 不写 `super`：其中包含 iOS 根卷和 cryptex。
- 不写 `boot_a`。
- 不修改分区表。
- 不切换槽位。
- 刷机前完整备份已知正常镜像。
- 刷机输出必须同时出现 `Writing 'boot_b' ... OKAY` 和 `Finished`。

详细步骤见 [刷机与恢复](docs/FLASHING.md)。

## 来源与依赖

- [UniXNU](https://github.com/UniXNU/UniXNU)：`04573c510c5fd4892ca6948739389141cc9e05f5`
- [DarwinBoot](https://github.com/UniXNU/DarwinBoot)：`3c75734014cdab0acd9541e88057b7606ee7ae08`
- [Mu-Silicium](https://github.com/Project-Silicium/Mu-Silicium)：UEFI/EDK2 和打包工具
- [OnePlus Ace 5](https://github.com/tycykp/UniXNU-OnePlus-Ace5)：`aaa100d19f6fb14e5897a7e496edf7838d4d4e9f`
- [魅族 20 Classic](https://github.com/RiverKawa271828/UniXNU-m2381)
- [小米 14](https://github.com/lonzzi/UniXNU-houji)
- [HackiOS](https://github.com/oosexgang/hakios-xnu-kernel)
- [SM8650 原厂图形源码](https://github.com/OnePlusOSS/android_kernel_modules_and_devicetree_oneplus_sm8650)

感谢 UniXNU、Mu-Silicium、DarwinBoot、HackiOS、OnePlus Ace 5、
Meizu m2381、Xiaomi houji 等公开移植项目提供的源码和调查记录。

完整的机器可读来源表见 [sources.json](sources.json)，逐项输入说明见
[启动指南](docs/STARTUP.md)。

仓库混合了多种上游许可证，详见 [COPYING.md](COPYING.md) 和
[docs/THIRD_PARTY.md](docs/THIRD_PARTY.md)。
