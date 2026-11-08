# SukiSU Ultra（camellia 适配分支）

本仓库是 [SukiSU-Ultra/SukiSU-Ultra](https://github.com/SukiSU-Ultra/SukiSU-Ultra) 的分叉，由 `pixian5` 维护。当前主要工作不是改动项目本体，而是把 SukiSU Ultra 移植到 **红米 Note 10 5G（代号 camellia，联发科 4.14 非 GKI 内核）**，并完整记录设备核对、内核编译、镜像打包、刷机与回退过程。

- `origin`：`https://github.com/pixian5/SukiSU-Ultra`（可写分叉）
- `upstream`：`https://github.com/SukiSU-Ultra/SukiSU-Ultra`（只读上游）
- 项目本体说明：[docs/README.md](docs/README.md)（English） / [docs/zh/README.md](docs/zh/README.md)（简体中文）

## 【当前开发进度】

真机 root **已可用并验证通过**：自编 4.14 内核刷入 `boot_b` 后正常开机，管理器显示「工作中」，授权成功；12 个分区只读备份与精确回退件均已就位。

本轮（2026-11-08）做了六件事：

1. 把两处关键授权修复固化进仓库（厂商内核 `kernel/reboot.c` 钩子、模块侧 `dispatch.c` 默认 profile 回退），并接入 `integrate.py` 第 8、9 步；
2. **把 SuSFS 接入 4.14 内核并完整编译通过**：上游 v1.5.5 的 4.14 原生核心 + 自写 v2.3.0 ABI 翻译层。这在 [tools/camellian-susfs](tools/camellian-susfs/) 里，配套一键接入与校验脚本。
3. **用出厂配置 + LTO/CFI 打出可刷镜像**：`dist/boot-sukisu-susfs-lto-stockdtb.img`，67,108,864 字节，MD5 `322fd6381c8b6d546b0298fbd1b7736f`，10/10 结构校验通过。内核 `4.14.186-perf-gf4e416aea-dirty`，52 个 susfs 符号，版本串 `v2.3.0`。已发布到 [Release camellian-susfs-v0.0.4](https://github.com/pixian5/SukiSU-Ultra/releases/tag/camellian-susfs-v0.0.4)（pre-release，含 SHA256SUMS）。
4. **按交接文档改用 vanilla SuSFS 1.4.2 重编**：执行中发现交接文档的关键判断有误（1.4.2 不含 SukiSU 扩展 UAPI），因此在其核心上自研 4.14 兼容层。新镜像 67,108,864 字节，MD5 `95352fe103f84e1fe07e4d5a2633d461`，12/12 结构校验通过，311 个 `ksu_`/`susfs_` 符号，版本串 `1.4.2` / `NON-GKI`。已发布到 [Release camellian-susfs-v0.0.5](https://github.com/pixian5/SukiSU-Ultra/releases/tag/camellian-susfs-v0.0.5)（pre-release，含 SHA256SUMS），详见 [编译完成记录](docs/20261108-0350-SuSFS隐藏方案编译完成记录-Kimi-K3.md)。
5. **阶段 1：把四条「假支持」命令改成明确不支持**（v2.3.0 路线）：`sus_path_loop`、`sus_map`、`avc_log_spoofing`、`priority_uid_filter` 在 ABI 层直接返回 `-EOPNOTSUPP`，`sus_map` 撤出特性列表。新镜像 67,108,864 字节，MD5 `3248b6a178b2aa91e423d95feab292ad`，10/10 结构校验通过，53 个 susfs 符号，版本串 `v2.3.0`。已发布到 [Release camellian-susfs-v0.0.6](https://github.com/pixian5/SukiSU-Ultra/releases/tag/camellian-susfs-v0.0.6)（pre-release，含 SHA256SUMS）。

6. **修复错误、统一镜像来源并合并并行版本**：另一台并行工作的云电脑先发布了 v0.0.6（在接口层把四条空壳命令改成明确报错，方式比在命令分发处拒绝更贴合用户态协议），本机把它定为主线并补齐 GitCode 资产、刷后判据与来源说明；同时逐份实测更正发布说明里写反的小米模块配置、更正交接文档、补齐真机验证清单、把厂商内核树与 SukiSU 树的全部源码改动导出成补丁入库、归档两份来路不明的镜像。本机另编译了一份「关掉全量符号暴露开关」的实验变体，**仅存档，不作为刷机候选**。详见 [修复与重编译记录](docs/20261108-0428-SuSFS错误修复与v0.0.6重编译-Claude-Opus-6.md)。

> 注意：所有 SuSFS 镜像**尚未在真机上验证**；刷机需你明确授权并执行，回退件 `boot_b-before.img` 仍在。
> **镜像来源**：只认 GitHub Release 资产 + 校验值。对象存储里 `camellian/boot-sukisu-susfs-lto-stockdtb.img` 这个固定名字在 11 月 8 日凌晨被多台并行云电脑覆盖过多次，**不要按这个名字取「最新」**，见 `backup/camellian/SOURCES.txt`。

详细进度：[docs/20261108-0101-当前开发进度-DeepSeek-V4.1-Flash.md](docs/20261108-0101-当前开发进度-DeepSeek-V4.1-Flash.md)、[SUSFS 移植与验证报告](docs/20261108-0210-SUSFS-v2.3.0移植与编译验证-DeepSeek-V4.1-Flash.md)、[可刷镜像构建与产物](docs/20261108-0250-SUSFS可刷镜像构建与产物-DeepSeek-V4.1-Flash.md)

## 【下一步待实现】

1. **刷机并真机验证（需用户明确说「刷机」）**：以 `camellian-susfs-v0.0.6` 发布页资产为准（先核对校验值）→ 确认管理器「工作中」、后台有 root 子进程、内核日志出现 `susfs is initialized! version: v2.3.0`、`ksud susfs status` 显示 `v2.3.0 / NON-GKI`、特性列表不再出现 `CONFIG_KSU_SUSFS_SUS_MAP`、四条不支持的命令明确报错，再用 Momo 复测隐藏效果。**不要用 `adb shell su` 判断成败**。若改刷 v0.0.5 的 1.4.2 路线，判据相应改为 `1.4.2 / NON-GKI`；
2. **复现闭环**：已完成——`tools/camellian-susfs/patches/` 里有厂商内核树补丁、SukiSU 树补丁与编译配置快照，`config/ikconfig-v0.0.6-mainline.txt` 是从主线镜像里提取的出厂配置；实验变体源码单独放在 `patches/experimental-kallsyms-off/`。v0.0.5 那条路线的私有源码确认不可恢复，已结案并从候选除名；公开的等价 4.14 扩展接口实现已固化在 `tools/camellian-susfs/reference/4.14-extension-uapi/`，详见 [结案报告](docs/20261108-0930-v0.0.5源码缺失结案与公开替代实现-Claude-Opus-6.md)；
3. **资产安全**：给回退件与可用镜像做异地备份；
4. **仓库同步**：合并上游 8 个提交（多为管理器界面改动，与内核无关）；
5. **真机收尾**：重启验证 Zygisk Next、逐个启用模块、核对授权列表。

详细清单与验收标准：[docs/20261108-0101-下一步待实现-DeepSeek-V4.1-Flash.md](docs/20261108-0101-下一步待实现-DeepSeek-V4.1-Flash.md)

## 文档导航

- [文档索引.md](文档索引.md)：`docs/` 下每份文档的一句话说明。
- [经验/](经验/)：按类别整理的项目经验与避坑清单，供快速上手。
- [docs/README.md](docs/README.md)：上游项目说明与全部分析报告索引。

## 当前设备状态速查

| 项目 | 值 |
| --- | --- |
| 设备 | `M2103K19C`（camellia），MIUI `V14.0.4.0.TKSEUXM` |
| 槽位 | `b`（虚拟 A/B），只写过 `boot_b` |
| 内核 | `4.14.186-perf-gf4e416aea-dirty` #11，手动挂钩 |
| 当前镜像 | `backup/camellian/boot-sukisu-final3-lto-stockdtb.img`（MD5 `3f687ecbc07f24ac0ecfbea56ebe14f5`） |
| 回退镜像 | `backup/camellian/boot_b-before.img`（MD5 `531c534bcc8d3172e03b12a2f6dd135d`） |
| 管理器 | `v4.3.0-r2`（41150） |
| 调试模式 | 关闭（`adb shell su` 不可用属正常安全设计） |

> `backup/` 已被 `.gitignore` 排除，仅保存在本机。刷机与回退前必须核对校验值。

## 安全与操作边界

- 未经明确授权，不写手机任何分区、不重启、不切槽、不推文件、不装应用。
- 不使用 `flash_all_lock.sh`（会重新锁启动锁，自编内核无法启动）。
- 判断 root 是否成功不要用 `adb shell su`；以管理器「工作中」、`com.sukisu.ultra:root:0` 进程和内核日志 `is_manager: 1` 为准。
- 管理器「隐藏应用」会禁用自身入口，恢复需电脑覆盖重装，建议保持关闭。

## 许可证

沿用上游分层：`kernel/` 为 GPL-2.0-only，带角色的图标有单独许可，其余为 GPL-3.0-or-later。详见 [LICENSE](LICENSE)、[LICENSE_icon_English](LICENSE_icon_English)、[LICENSE_icon_SC](LICENSE_icon_SC)。
