# Ruru 全部隐藏手段无效：最终结论

- 时间：2026-11-20 12:55（GMT+8）
- 设备：v6 内核（`#8`），SuSFS v2.3.0，Shamiko v1.2.5，Zygisk Next 1.5.2，HMA（Vector 框架）

---

## 一、试过的所有手段与结果

| 手段 | 配置 | Ruru 结果 |
| --- | --- | --- |
| SuSFS `sus_path` | `/data/adb/ksu`、`/data/adb/lspd`、`/data/adb/modules` 等 6 条 | ❌ 无变化 |
| SuSFS `sus_path` + `/system/bin/su` | 额外隐藏 su 路径 | ❌ 无变化（su 仍可用） |
| HMA | 给 Ruru 加隐藏列表，重启后确认加载进 system_server | ❌ PM 四项仍「发现」 |
| Zygisk Next `enforce-denylist just_umount` | 开启 | ❌ 无变化 |
| App Profile `umountModules=true`（Ruru） | `ksud temporary-root apply` 写入 | ❌ 无变化 |
| Shamiko | v1.2.5，报告 working as blacklist mode | ❌ 无变化（依赖 DenyList，SukiSU 无对应配置） |

**十项检测：环境检测与 Magisk 软件「未发现」，其余八项全部「发现」，且在所有配置前后完全一致。**

---

## 二、原因

Ruru 的检测方式绕过了所有可 hook 的层：

1. **PM 查询**：直接读 `/data/system/packages.list` 或 native，不经过 Java PM，HMA 的 system hook 无效；
2. **Libc / Syscall 文件检查**：直接 `open`/`access` `/data/app/*/base.apk`，不经过挂载隐藏，`umount`/`just_umount` 无效；
3. **Xposed / LSPatch**：检测真实安装的模块包名与 APK 文件，这些应用确实存在，不是残留。

**Zygisk Assistant 与 Shamiko 同属 Zygisk 层 root 隐藏，对上述两类检测同样无效；装了不会改变 Ruru 的结果。**

---

## 三、结论

**在 SukiSU 生态内，没有能骗过 Ruru 的方案。** 要让它全部变「未发现」，只有两条路，都不可接受：

1. 卸载所有 Xposed 模块/LSPosed 管理器（破坏日常功能）；
2. 用 `open_redirect` 重定向 `/data/app` 下的真实 APK 路径（内核实现未按 UID 过滤，会连应用自身一起影响，可能导致应用无法启动）。

---

## 四、建议

1. **接受 Ruru 的检测结果**：它是安全研究工具，检测强度远高于实际风控（银行/支付应用通常不会枚举 `/data/app` 下所有 APK）；
2. 保留 **Shamiko + SuSFS**：它们覆盖的是实际风控会用的 su、模块挂载、`/data/adb` 痕迹，这部分已经做好；
3. 想减少检测面，卸载不用的 Xposed 模块即可，没必要为了骗检测器破坏系统。

---

## 五、附：Zygisk Next 1.5.2 的能力

- 已整合 Shamiko 的大部分功能（`enforce-denylist just_umount` 等）；
- 排除列表由 SukiSU 管理器的 App Profile（`umountModules`）提供；
- Shamiko 可以保留，但与 Zygisk Next 功能重叠。

---

## 关联文档

- [Ruru 复测：HMA 已生效，但 PM 查询仍被发现](./20261120-1250-Ruru复测-HMA生效但PM仍被发现-结论-Claude-Opus-6.md)
- [Shamiko 已工作、HMA 作用域固定 system、Ruru 为 native 检测](./20261120-1220-Shamiko已工作-HMA作用域固定system-Ruru为native检测-Claude-Opus-6.md)
