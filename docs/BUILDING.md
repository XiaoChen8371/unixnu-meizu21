# 构建

## 工作区

```text
workspace/
├── UniXNU/
├── Mu-Silicium/
│   └── Mu_Basecore/
├── meizu-baseline/
│   ├── uefi-r19-clean-boot.img
│   └── SplashFbDxe-r19.efi
├── unixnu-meizu21/
└── build/
```

## 配置

```sh
cp configs/local-inputs.example.env local-inputs.env
. ./local-inputs.env
python3 scripts/verify-local-inputs.py
bash scripts/package.sh --check
```

`verify-local-inputs.py` 检查：

- r19 基线镜像 SHA256
- splash、`mkbootimg.py` 和 EDK2
- UniXNU 固定提交
- Python、Git、DTC、GCC、QEMU 和 Clang

## 完整构建

```sh
bash scripts/package.sh
```

输出：

```text
../build/r20-transition/uefi-r20-unixnu-transition.img
../build/r20-transition/packaging-check.json
```

已知正常镜像哈希：

```text
d4b3d5f61bd2570470c7b67bd61222f23ee05c18adb69dd2bafa92ccc600699b
```

哈希不一致时不要刷机，先检查 `evidence/` 中的 `inputs.json`、
`packaging-check.json`、`menu-build.log`、`bridge-build.log` 和
`qemu-result.log`。

## 构建阶段

1. `configure.py` 把设备 profile 接入固定 UniXNU 树。
2. DEBUG 模式编译真实 UniXNU 菜单。
3. 从稳定 r19 boot image 提取 shim、内核、ramdisk、DTB 和命令参数。
4. 编译 `MeizuBootBridge.efi`。
5. 在 FFS 现有的 embedded-loader 槽位中放入桥接模块。
6. 把 UniXNU 和原加载器作为额外 XNUP 记录加入保留 payload。
7. 运行 XNUP 解析器、内存表审计和 QEMU 菜单测试。

## 本地输入

仓库不包含 iOS 镜像、Apple SDK、原厂固件或完整 boot image。输入要求见
`proprietary-files.txt` 和 `STARTUP.md`。
