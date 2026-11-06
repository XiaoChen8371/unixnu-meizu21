# 开发指南

## 修改原则

1. 固定 UniXNU 和 DarwinBoot 提交，避免未记录的上游漂移。
2. 优先修改设备 owned profile、桥接或补丁，不直接大范围改写共享源码。
3. 保留 r19 基线 boot image 和 r20 正常回退镜像。
4. 所有 UEFI 诊断构建使用 DEBUG。
5. 修改内存表时必须检查活动地址范围不重叠。
6. 设备日志和提交中移除序列号、账号、路径和专有固件。

## 常见修改位置

- 改菜单参数：`configs/unixnu.toml`
- 改板级能力：`profiles/soc/sm8650/soc.toml`
- 改 iOS/Darwin profile：`profiles/os/ios-16.5-meizu-darwin22/profile.toml`
- 改桥接协议：`firmware/MeizuBootBridge.c`
- 改打包位置：`scripts/pack-transition.py`
- 改输入要求：`scripts/prepare-assets.py`
- 改内核补丁顺序：`patches/xnu/series`
- 改移植记录：`porting.toml`

## 验证

```sh
python3 -m py_compile scripts/*.py
python3 scripts/verify-local-inputs.py
bash scripts/package.sh --check
bash scripts/package.sh
```

提交设备结果时至少记录：

- 代码提交和镜像 SHA256
- 设备型号、SoC、槽位
- 预期行为与实际行为
- 串口、USB 或相机采集的证据位置
- 是否写入了 `boot_b`
- 是否完成回退

## 新增驱动

新增硬件模块应说明：

- MMIO、IRQ、时钟、电源和 IOMMU 所有权
- 固件来源、哈希和认证路径
- DMA 缓冲区生命周期
- 超时、异常和恢复策略
- 主机单元测试
- 设备侧最小可观察结果

在真实硬件结果出现前，状态只能标为“实现”“主机验证”或“实验性”。
