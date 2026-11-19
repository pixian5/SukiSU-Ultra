# v3 刷入成功：WiFi 恢复、SuSFS 生效

- 时间：2026-11-20 01:00（GMT+8）
- 镜像：`boot-sukisu-susfs-allowlist-fix-v3.img`
  - 67,108,864 字节，MD5 `5085cea8e4592996ff9d35a559e1c82b`
  - SHA256 `a5eff0b63ac5e982e6935667c9f6a5a1e284cc41f28e79d6004fc4eb3692bf8d`（与对方一致）
- 内核：`#3 SMP PREEMPT Fri Nov 20 00:42:40 CST 2026`

---

## 一、v3 的修复内容与验证

v2 的 WiFi 失败原因是 `CONFIG_MODVERSIONS=y` 下符号 CRC 与厂商预编译模块不匹配；v3 在 `kernel/module.c` 的 `check_version()` 里放行 CRC 不匹配（保留符号存在性检查），`CONFIG_MODVERSIONS` 保持开启，vermagic 不变。

四项标志在产物里逐一确认：

| 标志 | 位置/结果 |
| --- | --- |
| allowlist 空包名跳过 | 指令序列在 Image 偏移 16,716,096 |
| CRC 放行字符串 | `ignoring crc mismatch for symbol ... (SUSFS custom kernel)` |
| 默认配置回退 | `get_app_profile: copy_to_user default failed` |
| vermagic 含 modversions | `4.14.186-perf-gf4e416aea-dirty SMP preempt mod_unload modversions aarch64` |

配置：`CONFIG_MODVERSIONS=y`、`CONFIG_KSU_SUSFS=y`、`CONFIG_KALLSYMS_ALL=y`、`CONFIG_LTO_CLANG=y`、`CONFIG_CFI_CLANG=y`。

---

## 二、刷入与开机

只写 `boot_b`，fastboot 全部 OKAY；`sys.boot_completed=1`，开机过程无崩溃。

---

## 三、WiFi：完全恢复

- `cmd wifi status` → **`Wifi is connected to "f5"`**；
- IP `192.168.1.9`，WiFi 5，390 Mbps，WPA3-SAE，RSSI -43；
- `/sys/module` 里 `wlan_drv_gen4m`、`cfg80211` 都在；
- `wlan0` 正常收发（接收 28,422 字节、发送 12,434 字节）。

**CRC 放行生效，WiFi 驱动正常加载。**

---

## 四、相机与指纹

- `cameraserver`、`camerahalserver` 正常运行；
- `android.hardware.biometrics.fingerprint@2.1-service` 正常运行。

服务层面无异常；实际拍照与解锁体验需要日常使用观察。

---

## 五、SukiSU 与 SuSFS 状态

管理器设置页显示：

- 管理器版本 `v4.3.0-r2 (41150-6)`；
- 内核完整版本 **`v3.0.0-4bec532d@builtin`**；
- **SuSFS 版本 `v2.3.0 (SUSFS Inline Hook)`**；
- Zygisk Next 1.5.2；
- `com.sukisu.ultra:root:0` 以 root 运行，SukiSU 工作中。

注意：内核 SukiSU 版本是 `v3.0.0`，管理器是 `v4.3.0-r2`，两者版本串不一致但 UAPI 兼容，当前可正常使用；以后若出现授权/模块异常，优先怀疑这个版本差。

---

## 六、授权记录

管理器显示「已授权 10 / 551 个应用」，比 v2 时的 12 条少 2 条：

- 一条是 Shell（uid 2000）——临时授权，重启按设计失效，正常；
- 另一条应是 final3 回退期间被清掉的空包名记录（final3 没有「跳过空包名」修复）。

v3 开机已经跑过一次清理（`on_boot_completed` → prune），保留的 10 条全部是 ROOT，说明 v3 的空包名跳过逻辑生效。

---

## 七、已知风险

1. SuSFS 确实修改了两个核心结构：`vfsmount` 末尾加 8 字节、`task_struct` 在 `thread` 之前加 16 字节；
2. `CONFIG_GCC_PLUGINS` 未开启，字段顺序固定，**前置字段偏移没有变**，因此厂商模块访问常用字段是安全的；
3. 但如果 WiFi 出现「能开但异常断连/崩溃」，优先怀疑结构体偏移（而非 CRC），此时应回退 final3。

---

## 八、回退

`boot-sukisu-final3-lto-stockdtb.img`（MD5 `3f687ecbc07f24ac0ecfbea56ebe14f5`）：

```
fastboot flash boot_b boot-sukisu-final3-lto-stockdtb.img
fastboot reboot
```

---

## 关联文档

- [v2 内核 WiFi 失效根因与回退](./20261120-0015-v2内核WiFi失效根因与回退-Claude-Opus-6.md)
- [要求对方关 MODVERSIONS 重编 v3 的提示词](./20261120-0020-要求对方关MODVERSIONS重编v3的提示词-Claude-Opus-6.md)
- [刷入 v2 镜像与验证结果](./20261120-0005-刷入v2镜像与验证结果-Claude-Opus-6.md)
