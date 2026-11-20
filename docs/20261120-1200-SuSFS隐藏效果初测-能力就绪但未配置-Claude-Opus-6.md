# SuSFS 隐藏效果初测：内核能力就绪，但没有任何隐藏配置

- 时间：2026-11-20 12:00（GMT+8）
- 设备：v6 内核（`#8`，SuSFS v2.3.0 Inline Hook）
- 工具：Ruru V1.1.0（`com.byxiaorun.detector`，手机上已安装）

---

## 一、Ruru 检测结果

| 检测项 | 状态 |
| --- | --- |
| 环境检测 | ✅ 未发现 |
| PM 命令查询 | ❌ 发现 |
| PM 常规 Api 查询 | ❌ 发现 |
| PM 混合 API 查询 | ❌ 发现 |
| PM 主界面查询 | ❌ 发现 |
| Libc 文件检查 | ❌ 发现 |
| Syscall 文件检查 | ❌ 发现 |
| Xposed 模块 | ❌ 发现 |
| LSPatch 软件 | ❌ 发现 |
| Magisk 软件 | ✅ 未发现 |

---

## 二、关键发现：SuSFS 没有配置

检查 `/data/adb/ksu/`：

```
.allowlist  .allowlist.bak-20261119  .dynamic_managers  .feature_config
bin  lib  log  module_configs  preinit_status  profile  sulogd.lock  temporary-root
```

**没有任何 susfs 配置文件**（`find /data/adb -iname '*susfs*'` 无结果）。

也就是说：

- SuSFS 的内核能力（sus_path / sus_mount / sus_kstat / uname 伪装等）**都编进去了**；
- 但**没有配置任何要隐藏的路径或规则**，等于「引擎装好了，没挂挡」。

---

## 三、Ruru 结果的正确解读

- **Magisk 软件「未发现」不是 SuSFS 的功劳**：这台手机本来就没有 Magisk（刷 SukiSU 时已卸载），自然检测不到；
- **环境检测「未发现」**同理，没有 Magisk 环境；
- **PM 查询、Libc/Syscall 文件检查「发现」**：检测到的是 SukiSU 自己的痕迹（包名 `com.sukisu.ultra`、`/data/adb/ksu` 相关路径）；
- **Xposed / LSPatch「发现」**：手机上确实装了 LSPosed（`/data/adb/lspd`）和 Xposed 模块，这些痕迹没有被隐藏。

**结论：SuSFS 当前处于「能力就绪、零配置」状态，隐藏效果等于没有。**

---

## 四、要真正隐藏，需要做什么

SuSFS 的隐藏规则需要显式配置，常见项：

| 目标 | 配置项 |
| --- | --- |
| 隐藏 SukiSU 管理器包名 | `sus_path` 或包名伪装（PM 查询） |
| 隐藏 `/data/adb/ksu`、`/data/adb/lspd` | `sus_path` |
| 隐藏模块挂载 | `sus_mount` |
| 隐藏 `/system/bin/su` 等文件 | `sus_path`（但注意别把提权入口也藏了，v5 的坑） |
| 伪装内核版本/cmdline | `SPOOF_UNAME` / `SPOOF_CMDLINE_OR_BOOTCONFIG` |
| 隐藏 ksu 符号 | 已默认开启（`HIDE_KSU_SUSFS_SYMBOLS`） |

配置属于**写操作**，需要用户授权后才能执行；配置方式可以是 `ksud` 的 susfs 子命令，或管理器里的 SuSFS 设置页。

---

## 五、下一步建议

1. 先用 Momo 或 Ruru 记录一份「配置前」基线（本次已记录）；
2. 按需配置 `sus_path` / `sus_mount` / `uname` 伪装，再复测；
3. 注意 v5 的教训：**不要隐藏 `/system/bin/su` 和 ksud 自己的路径**，否则提权入口会被藏掉。

---

## 关联文档

- [v6 刷入成功：su 恢复、WiFi 正常、授权保留](./20261120-1145-v6刷入成功-su恢复与授权保留-Claude-Opus-6.md)
- [v3 的 su 被 SuSFS 隐藏](./20261120-0105-v3的su被SuSFS隐藏-Claude-Opus-6.md)
