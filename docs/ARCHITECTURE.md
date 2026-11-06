# 架构

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

## 当前实现

`MeizuBootBridge` 是一个小型 EDK2 模块，负责向 UniXNU 发布只读内存文件系统，
并实现 `UNIXNU_LOADER_PROTOCOL` revision 2。保留加载器继续负责 Apple 设备树
和内核内存交接。

这不是完整的原生 UniXNU 平台迁移。当前阶段保留已经验证的 Darwin 22 加载器、
内核、UFS 路径、显示和触摸实现。

## 内存和固件映像

- 19 KiB 桥接模块替换原 FFS embedded-loader 槽位。
- UniXNU 和原加载器作为额外 XNUP 记录存在。
- 内层 FV 的 54 个文件中，53 个保持逐字节不变。
- kernel、ramdisk、cmdline、shim、Android DTB 和 MemoryMap 保持固定。
- `super` 不参与构建，也不会被脚本访问。

## 目录职责

| 路径 | 内容 |
| --- | --- |
| `board.toml`、`feeds.toml`、`porting.toml` | 板级、来源和移植记录 |
| `configs/` | UniXNU 配置和本地输入示例 |
| `dts/` | 板级 inventory DTS |
| `profiles/` | SM8650、iOS 16.5 和 Darwin 22 profile |
| `firmware/` | UniXNU 与 retained loader 之间的桥接 |
| `patches/xnu/` | 保留内核补丁顺序 |
| `scripts/` | 配置、构建、打包和校验 |
| `tests/` | XNUP 与主机侧检查 |
| `evidence/` | 固定输入和验证结果 |
| `archive/` | 历史源码快照 |

## 尚未完成

- 原生 DarwinBoot 的 608-byte cmdline 和 736-byte boot_args ABI
- 32 MiB 放置策略与本内核物理/虚拟地址窗口
- 原生 ADT、平台、HID 和 runtime services
- A750 GPU/GMU/HFI/命令提交
- Metal 与 iOS 图形前端
