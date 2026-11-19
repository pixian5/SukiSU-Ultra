# v2 内核 WiFi 打不开：vendor 模块加载失败，已回退 final3

- 时间：2026-11-20 00:15（GMT+8）
- 设备：Redmi Note 10 5G（M2103K19C / camellia），Android 13，槽 b
- 现象：刷入 v2（`boot-sukisu-susfs-allowlist-fix-v2.img`）后 **WiFi 开关打不开**；用户补充「之前有的版本的面具刷入后也无法打开 WiFi」
- 处置：已回退 final3，WiFi 恢复正常并自动连上 f5

---

## 一、现象与证据

刷 v2 后：

- `cmd wifi status` → `Wifi is disabled`，但 `settings get global wifi_on` = 1（系统认为该开）；
- `/proc/net/dev` 里**没有 `wlan0`**；
- `/sys/module` 里有 `cfg80211`（内核内置），**没有 `wlan_drv_gen4m`**（MTK 的 WiFi 驱动，vendor 预编译模块）。

结论：**WiFi 驱动模块没有加载**，不是开关/服务问题。

---

## 二、排除的项

| 项 | final3 | v2 | 结论 |
| --- | --- | --- | --- |
| `CONFIG_CFG80211` | y | y | 相同 |
| `CONFIG_MTK_COMBO` 及芯片选项 | 相同 | 相同 | 相同 |
| `CONFIG_MAC80211` | 未设 | 未设 | 相同 |
| `CONFIG_MODVERSIONS` | y | y | 相同 |
| 内核 vermagic | `4.14.186-perf-gf4e416aea-dirty SMP preempt mod_unload modversions aarch64` | 完全相同 | 相同 |

**配置项和 vermagic 都一样，所以不是「漏开 WiFi 驱动」那么简单。**

---

## 三、根因判断：SuSFS 改了结构体，vendor 模块符号 CRC 不匹配

`CONFIG_MODVERSIONS=y` 时，内核会用 `genksyms` 给每个导出符号算一个 CRC，模块加载时逐个比对。这个 CRC 由**结构体布局和函数签名**决定。

SuSFS 的 4.14 补丁会修改 `struct inode`、`struct task_struct`、`struct mount`、`struct super_block` 等核心结构（加字段/标志位）。这些改动会**改变大量导出符号的 CRC**，而 `/vendor/lib/modules/wlan_drv_gen4m.ko` 是厂商预编译的，CRC 对应原厂内核——于是模块加载时校验失败，内核拒绝加载，`wlan0` 就不存在。

这解释了为什么：

- `cfg80211`（编进内核的）在，`wlan_drv_gen4m`（vendor 的 .ko）不在；
- **final3 没有 SuSFS**（`CONFIG_KSU_SUSFS is not set`），结构体未改，vendor 模块正常；
- 用户以前刷某些 Magisk 版本也遇到 WiFi 打不开——同样是内核改动触发了 vendor 模块校验。

---

## 四、已执行的恢复

回退到 final3：

```
fastboot flash boot_b boot-sukisu-final3-lto-stockdtb.img   # MD5 3f687ecbc07f24ac0ecfbea56ebe14f5
fastboot reboot
```

结果：

- 内核 `#11`（11-07 03:45:39）；
- `cmd wifi status` → **`Wifi is enabled`**，已连接 `f5`；
- `/sys/module` 里 `wlan_drv_gen4m`、`cfg80211` 都在；
- `wlan0` 正常有收发。

**WiFi 已恢复。**

---

## 五、后续要刷带 SuSFS 的版本，怎么解决

按可行性排序：

1. **重编时关闭 `CONFIG_MODVERSIONS`**（`# CONFIG_MODVERSIONS is not set`）。
   - 内核不再校验符号 CRC，vendor 预编译模块可以加载；
   - 风险：ABI 不完全一致的模块可能不稳定，但同版本内核通常可用；
   - 这是社区自定义内核解决 vendor 模块加载失败的常用办法。
2. **把 vendor 模块对应的驱动源码一起编进内核**：MTK 的 `vendor/mediatek/proprietary` 不开源，做不到。
3. **放弃 SuSFS**，只保留 SukiSU（即 final3 路线），WiFi 与相机等 vendor 功能不受影响。

**建议**：让对方按第 1 条重编 v3（在 v2 基础上只改 `CONFIG_MODVERSIONS=n`），刷后先验 WiFi、相机、指纹，再验授权。

---

## 六、教训

- 在 4.14 这种非 GKI 内核上，任何改动核心结构体的补丁（SuSFS、部分 Magisk 变体）都可能让 vendor 预编译模块（WiFi、相机、指纹、传感器）加载失败；
- 判断方法很简单：`/sys/module` 里缺了对应模块、`/proc/net/dev` 里缺 `wlan0`；
- 以后刷任何自定义内核，第一轮验证必须包含 WiFi 和相机，不能只看开机和 root。

---

## 关联文档

- [刷入 v2 镜像与验证结果](./20261120-0005-刷入v2镜像与验证结果-Claude-Opus-6.md)
- [v2 镜像独立验证：两处修复齐全，可刷](./20261119-2355-v2镜像独立验证与可刷结论-Claude-Opus-6.md)
- [首次真机试刷与 SukiSU 接入验证](./20261107-1110-首次真机试刷与SukiSU接入验证-Claude-Opus-6.md)
