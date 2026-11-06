# 刷机与恢复

## 前置条件

- 手机处于 fastboot。
- 当前活动槽位为 `b`。
- 原 `boot_b` 已完整备份。
- `super` 的内容已经验证并禁止写入。
- 已知正常的完整启动镜像仍然保留。
- 构建镜像 SHA256 与 `packaging-check.json` 一致。

## 写入

```sh
fastboot devices
fastboot getvar current-slot
fastboot flash boot_b ../build/r20-transition/uefi-r20-unixnu-transition.img
fastboot reboot
```

写入输出必须包含：

```text
Sending 'boot_b' ... OKAY
Writing 'boot_b' ... OKAY
Finished
```

## 禁止操作

- 不写 `super`。
- 不写 `boot_a`。
- 不修改分区表。
- 不在输入哈希不一致时刷机。
- 不把旧 RTC 限时诊断镜像当作正常系统镜像复用。
- 不在未备份时测试新镜像。

## 回退

```sh
fastboot flash boot_b /path/to/verified-working-boot_b.img
fastboot reboot
```

回退镜像也应先校验 SHA256。当前项目已验证的正常 r20 回退 SHA256 为
`d4b3d5f61bd2570470c7b67bd61222f23ee05c18adb69dd2bafa92ccc600699b`。

若设备未自动返回 fastboot，长按硬件按键进入 fastboot 后恢复已知镜像。
