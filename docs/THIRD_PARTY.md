# 第三方来源和许可

本仓库是多项目适配工作，不重新授权第三方文件。发布或再分发前，应保留每个
文件原有的版权头和许可证。

## 固定上游

| 项目 | 用途 | 固定版本 |
| --- | --- | --- |
| [UniXNU](https://github.com/UniXNU/UniXNU) | 菜单、配置和加载协议 | `04573c510c5fd4892ca6948739389141cc9e05f5` |
| [DarwinBoot](https://github.com/UniXNU/DarwinBoot) | Darwin 原生启动参考 | `3c75734014cdab0acd9541e88057b7606ee7ae08` |
| [Mu-Silicium](https://github.com/Project-Silicium/Mu-Silicium) | UEFI、EDK2 和 boot image 打包 | 本地 `Mu_Basecore` checkout |
| [UniXNU-OnePlus-Ace5](https://github.com/tycykp/UniXNU-OnePlus-Ace5) | SM8650 和 Gen7 GPU 研究参考 | `aaa100d19f6fb14e5897a7e496edf7838d4d4e9f` |
| [UniXNU-m2381](https://github.com/RiverKawa271828/UniXNU-m2381) | 魅族 SM8550 设备仓库参考 | 当前公开版本 |
| [UniXNU-houji](https://github.com/lonzzi/UniXNU-houji) | SM8650 UFS、XNU 和 A750 参考 | 当前公开版本 |
| [HackiOS](https://github.com/oosexgang/hakios-xnu-kernel) | retained Darwin compatibility chain | 区域/归档参考 |
| [iOS Sweet](https://github.com/dipa-studio/ios-sweet) | iOS compatibility-chain reference | 当前公开版本 |
| [Apple XNU](https://github.com/apple-oss-distributions/xnu) | 内核 ABI 和接口参考 | 对应源码版本 |

## 其他参考资料

- OnePlusOSS SM8650 graphics kernel：
  <https://github.com/OnePlusOSS/android_kernel_modules_and_devicetree_oneplus_sm8650>
- Linux Qualcomm SMMU、GPUCC 和 RPMH 实现
- U-Boot Qualcomm RPMH RSC 实现
- 项目 `evidence/` 目录中记录的其他固定提交

这些项目各自使用自己的许可证。引用某份文档或接口不等于将对应代码重新授权。

## 不随仓库分发的输入

以下内容必须由构建者自行获得并确认有权使用：

- iOS 内核、ramdisk、设备树和系统根卷
- Apple SDK、`identity.h` 和相关签名材料
- 原厂 GPU、GMU、ZAP 或其他固件 blob
- 完整的 r19、r20 boot image
- 手机分区备份和 `super` 内容

`../proprietary-files.txt` 只记录哈希，不表示仓库有权重新分发对应文件。

## 本仓库新增代码

本仓库新增的桥接、打包辅助和文档目前没有单独选定仓库级许可证。由于文件
混合了不同上游许可证，不能简单套用单一许可证。后续发布新版本时应：

1. 逐项确认新增文件和上游文件的来源。
2. 保留所有原始版权和许可证。
3. 为可独立授权的新增部分选择合适的许可证。
4. 不删除 `vendor/`、源快照或补丁中的许可证文本。
