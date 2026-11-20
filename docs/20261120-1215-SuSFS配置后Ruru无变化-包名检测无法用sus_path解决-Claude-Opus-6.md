# SuSFS 配置后 Ruru 结果无变化：它检测的是包名，不是 /data/adb 路径

- 时间：2026-11-20 12:15（GMT+8）
- 设备：v6 内核（`#8`），SuSFS v2.3.0 Inline Hook
- 配置：`sus_paths` 含 `/data/adb/ksu`、`/data/adb/lspd`、`/data/adb/modules` 等 6 条；另加 `/system/bin/su`

---

## 一、配置前后对比

| 检测项 | 配置前 | 配置后 |
| --- | --- | --- |
| 环境检测 | ✅ 未发现 | ✅ 未发现 |
| PM 命令查询 / 常规 / 混合 / 主界面 | ❌ 发现 | ❌ 发现 |
| Libc 文件检查 | ❌ 发现 | ❌ 发现 |
| Syscall 文件检查 | ❌ 发现 | ❌ 发现 |
| Xposed 模块 | ❌ 发现 | ❌ 发现 |
| LSPatch 软件 | ❌ 发现 | ❌ 发现 |
| Magisk 软件 | ✅ 未发现 | ✅ 未发现 |

**完全没变。**

---

## 二、Ruru 到底查什么

展开「Libc 文件检查」，它列的是这些包名：

```
com.topjohnwu.magisk
io.github.vvb2060.magisk
io.github.vvb2060.magisk.lite
de.robv.android.xposed.installer
org.meowcat.edxposed.manager
org.lsposed.manager
top.canyie.dreamland.manager
me.weishu.exp
com.tsng.hidemyapplist
cn.geektang.privacyspace
moe.shizuku.redirectstorage
```

也就是说它查的是 **Magisk / LSPosed / Xposed 等管理器的包名与 APK 文件**，不是 `/data/adb/ksu`。

`PM 命令查询`、`PM 常规/混合/主界面查询` 同理，是通过包管理器查询 `com.sukisu.ultra` 等包是否存在。

`Syscall 文件检查` 大概率查 `/system/bin/su`、`/sbin/su` 一类路径；虽然已经把 `/system/bin/su` 加进 sus_path，结果仍未变化，说明它可能走的是特殊进程/特殊 syscall，不受 `TASK_STRUCT_NON_ROOT_USER_APP_PROC` 约束。

---

## 三、结论

1. **SuSFS 的 `sus_path` 擅长隐藏文件路径与挂载，不擅长隐藏「已安装包名」**；
2. Ruru 的大部分「发现」来自包名/APK 查询，`sus_path` 对此无效；
3. 要骗过这类检测，需要 **HMA（Hide My Applist）** 这类包名隐藏方案；手机上已装 `com.tsng.hidemyapplist`，但需要 LSPosed 模块配合；
4. Shamiko 是 Magisk 专用，SukiSU 上不兼容，不能直接用。

**SuSFS 的价值**在于隐藏 root 的文件与挂载痕迹（Momo 的部分检测项），不是骗过所有安全研究工具。

---

## 四、当前保留的配置

- `sus_paths`：`/data/adb/ksu`、`/data/adb/lspd`、`/data/adb/modules`、`/data/adb/modules_update`、`/data/adb/post-fs-data.d`、`/data/adb/service.d`（持久化，开机自动应用）；
- 额外 `add-sus-path /system/bin/su`（仅内存，重启失效；已验证不影响 `su -c id`）；
- 没有把 ksud 自身路径加进隐藏列表。

---

## 五、下一步建议

1. 如果要继续对抗 Ruru 这类检测，走 HMA 路线（LSPosed 模块 + 隐藏应用列表），不要继续在 sus_path 上堆路径；
2. 如果目标是 Momo 的 root 痕迹检测，SuSFS 的 sus_path/sus_mount 值得继续调；
3. 不建议为了骗检测器而隐藏 `su`/`ksud` 路径——v5 已经证明会把自己的提权入口搞坏。

---

## 关联文档

- [SuSFS 隐藏配置已生效，Ruru 复测被锁屏挡住](./20261120-1205-SuSFS隐藏配置已生效-复测待解锁-Claude-Opus-6.md)
- [SuSFS 隐藏效果初测：能力就绪但未配置](./20261120-1200-SuSFS隐藏效果初测-能力就绪但未配置-Claude-Opus-6.md)
