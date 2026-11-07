# 首次真机试刷：自编内核成功开机，SukiSU 接入完成

> 状态：**已执行刷机并验证成功**。用户于 2026-11-07 10:22 明确说出「刷机」，授权范围是本次试刷流程。
> 写入的分区只有当前槽的启动分区（`boot_b`）一个；没有动 `boot_a`、没有动校验分区、没有切槽、没有清数据。
> 撰写时间：2026-11-07 11:10（本机时间）。

---

## 0. 一句话结论

自编的 4.14 内核在真机上**成功开机**，SukiSU 管理器显示「工作中」，后台有以 root 运行的子进程。中途我一度误判为失败，原因是把「adb shell 里没有 `su`」当成了故障——实际上那是关闭调试模式后的**正常安全设计**。真正的判据应该是管理器界面状态和它的 root 子进程。

---

## 1. 执行时间线

| 时间 | 动作 | 结果 |
| --- | --- | --- |
| 10:22 | 只读复核：型号、系统版本、槽位、电量、分区大小、产物校验值 | 全部通过；电量 100%；`boot_b` 分区 67,108,864 字节与镜像一致 |
| 10:23 | `adb reboot bootloader`，复核槽位与启动锁 | `current-slot: b`、`unlocked: yes`、`secure: no`、`anti: 1` |
| 10:24 | 写入 `boot_b`：推荐版 `boot-sukisu-lto-stockdtb.img`（MD5 `4bc14c88…`） | `Sending OKAY`、`Writing OKAY`，返回 0 |
| 10:24 | 重启 | 约 2 分钟完成开机，内核变为自编的 `gf4e416aea-dirty` |
| 10:26 | 安装管理器 APK（`Success`），启动 | 管理器能开，但日志报 `could not retrieve kernelsu driver fd`、`kernel=0` |
| 10:33 | 重启一次 | 仍无 shell `su`，误判为仍然失败 |
| 10:36–10:44 | 排查源码：确认 `CONFIG_KSU=y`、四处挂钩调用点、`device_initcall`、LSM 钩子都在 | 集成代码没有明显缺失 |
| 10:44 | 打开 `CONFIG_KSU_DEBUG` 重编（调试模式允许 shell 提权，便于读内核日志） | 零错误 |
| 10:47 | 刷入调试版 `boot-sukisu-debug-lto-stockdtb.img`（MD5 `3fef2c8c…`） | 开机成功 |
| 10:48 | 调试版下检查 | **`su -c id` 返回 `uid=0`、上下文 `u:r:ksu:s0`**；`/data/adb/ksud` 已在；内核日志 `is_manager: 1` |
| 10:52 | 打开管理器 | 首页显示「**工作中**」，版本 41156-6，模块 17，钩子类型 Manual Hook |
| 10:56–11:06 | 关闭调试模式重编最终版 | 零错误，量产优化配置保持 |
| 11:07 | 刷入最终版 `boot-sukisu-final-lto-stockdtb.img`（MD5 `fbe24534…`） | 开机成功，内核 `#9` |
| 11:09 | 最终验证 | 管理器主进程 + **root 子进程 `com.sukisu.ultra:root:0`**；无通道错误；`adb shell su` 按预期不可用 |

---

## 2. 中途误判的原因（值得记住）

第一次刷入后，我用 `adb shell su -c id` 判断是否成功，看到「su 不存在」就认为失败了。这是**错的判据**：

- 调试模式关闭时，内核里 `allow_shell = false`，shell 本来就不允许直接提权——这是防止「只要能连 adb 就能 root」的安全设计。
- 管理器的 root 走的是另一条路：内核识别管理器签名后，在进程切换用户时把一个内核通道注入给它（日志里的 `install fd for manager`）。所以管理器可以有 root，而 shell 没有。
- 日志里那条 `could not retrieve kernelsu driver fd` 出现在管理器**刚启动**的瞬间，之后 `ksud` 在 10:32 就被装上了——说明链路后来是通的。这条早期错误具有很强的误导性。

**正确判据**（已写入刷机剧本）：

1. 管理器首页是否显示「工作中」；
2. 进程列表里是否存在 `com.sukisu.ultra:root:0` 这个以 root 运行的子进程；
3. 管理器版本页里的内核版本、钩子类型是否正确；
4. 内核日志里是否有 `is_manager: 1` 与 `manager uid unchanged`。

`adb shell su` 是否可用**不能**作为判据。

---

## 3. 三个版本的镜像与最终状态

| 镜像 | MD5 | 用途 | 结果 |
| --- | --- | --- | --- |
| `boot-sukisu-lto-stockdtb.img` | `4bc14c88fb8b76c370619f3b36c76437` | 第一次试刷（推荐版） | 开机成功；当时误判为 SukiSU 未生效 |
| `boot-sukisu-debug-lto-stockdtb.img` | `3fef2c8ce4d79aba1920d65e6949b404` | 诊断用，开调试模式 | 开机成功，`su` 可用，确认链路正常 |
| `boot-sukisu-final-lto-stockdtb.img` | `fbe245348a7879993865a76f9b48dd83` | **当前运行**，调试模式关闭 | 开机成功，管理器「工作中」，root 子进程存在 |

最终版 SHA256：`64281a9d5a9e5d84381aebae361799fd50950441a58b993f27048b0127770651`，12 项结构校验全部通过。运行中的内核：

```text
Linux version 4.14.186-perf-gf4e416aea-dirty (user@main)
(Android (6443078 based on r383902) clang version 11.0.1 ..., LLD 11.0.1 ...)
#9 SMP PREEMPT Sat Nov 7 02:56:24 UTC 2026
```

管理器里显示的信息：

- 管理器版本 `v4.3.0-r2（41150-6）`
- 内核完整版本 `v4.3.0-r2-1cfa5734@builtin`
- 钩子类型 `Manual Hook`
- 系统指纹 `Redmi/camellia/camellia:13/TP1A.220624.014/V14.0.4.0.TKSEUXM:user/release-keys`
- SELinux 状态：强制执行
- Zygisk 实现：Zygisk Next（提示需要重启）

---

## 4. 手机当前状态

- 内核：自编 4.14，`#9`，调试模式关闭
- root 方案：SukiSU（管理器已识别，root 子进程在运行）；原来的 Magisk 启动层补丁随刷机消失，Magisk 的 `su` 不再存在
- 当前槽：仍是 b；`boot_a` 一个字节没动
- 系统：`V14.0.4.0.TKSEUXM`，用户数据未动
- 校验分区：未动
- 超级用户：0 个（还没有授权任何应用）
- 模块：管理器显示 17 个，但内核日志显示多个模块 `is disabled, skip`

**可直接恢复原状的回退件**：`backup/camellian/boot_b-before.img`（MD5 `531c534bcc8d3172e03b12a2f6dd135d`）。刷回它即可回到刷机前的 Magisk 状态。这条回退是写分区，需要另行授权。

---

## 5. 还需要用户处理的事项

1. **重启一次**：管理器提示 Zygisk Next 需要重启才能生效。
2. **检查模块**：原来 Magisk 的模块目录还在 `/data/adb/modules`，但内核日志显示多个模块被跳过（disabled）。需要在管理器里按需启用，不要一次性全开，以免冲突。
3. **授权应用**：超级用户目前为 0，需要哪个应用用 root 就在管理器里授权。
4. **确认 shell root 策略**：如果需要 adb shell 也能提权，要在管理器里配置；默认不再允许，这是安全设计。

---

## 6. 已知遗留问题

- Zygisk Next 需要重启后才生效，尚未验证。
- 模块启用状态需要人工确认，尚未逐个验证功能。
- 管理器仍存在 `KsuCli: Failed to get feature adb_root` / `shell_su_adb_only` 的提示，属于功能配置默认值未写入，不影响基本 root。
- 官方用户态与内置内核之间仍有一个接口常量差异（`KSU_IOCTL_SET_SPOOF_VERSION`），管理器里个别伪装设置可能不生效，尚未验证。
- KPM 开关虽然在配置里，但在这颗内核上结构性不可用（缺 KernelPatch 钩子）；SuSFS 未集成。

---

## 7. 本轮写入记录（如实）

| 分区 | 是否写入 | 说明 |
| --- | --- | --- |
| `boot_b` | 写入 3 次 | 推荐版 → 调试版 → 最终版，每次都用 fastboot 明确点名 `boot_b` |
| `boot_a` | 未写入 | 一个字节没动 |
| `vbmeta_b` / 其它校验分区 | 未写入 | 按方案 A 不动 |
| 用户数据分区 | 未写入 | 未清数据、未恢复出厂 |
| 其它分区 | 未写入 | 未刷 `super`、未刷 `metadata`、未执行任何官方刷机脚本 |

应用安装：安装了 SukiSU 管理器 APK（写入数据分区，属于刷机流程的一部分）。除此之外没有安装或卸载其它应用。

---

## 关联文档

- [红米 Note 10 5G 刷机执行方案与回退剧本](./20261107-0029-红米Note10-5G刷机执行方案与回退剧本-Claude-Opus-6.md)
- [手机分区只读备份与传输污染排查](./20261107-0852-手机分区只读备份与传输污染排查-Claude-Opus-6.md)
- [启动镜像版本核对与回退件定位](./20261107-0905-启动镜像版本核对与回退件定位-Claude-Opus-6.md)
- [可选隐藏特性补齐与再次重编](./20261107-0804-可选隐藏特性补齐与再次重编-Claude-Opus-6.md)
- [手机只读边界与刷机授权条件](./20261106-2327-手机只读边界与刷机授权条件-Claude-Opus-6.md)
