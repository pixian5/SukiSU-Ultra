# SukiSU Ultra（camellia 适配分支）

本仓库是 [SukiSU-Ultra/SukiSU-Ultra](https://github.com/SukiSU-Ultra/SukiSU-Ultra) 的分叉，由 `pixian5` 维护。当前主要工作不是改动项目本体，而是把 SukiSU Ultra 移植到 **红米 Note 10 5G（代号 camellia，联发科 4.14 非 GKI 内核）**，并完整记录设备核对、内核编译、镜像打包、刷机与回退过程。

- `origin`：`https://github.com/pixian5/SukiSU-Ultra`（可写分叉）
- `upstream`：`https://github.com/SukiSU-Ultra/SukiSU-Ultra`（只读上游）
- 项目本体说明：[docs/README.md](docs/README.md)（English） / [docs/zh/README.md](docs/zh/README.md)（简体中文）

## 【当前开发进度】

真机 root **已可用并验证通过**：自编 4.14 内核刷入 `boot_b` 后正常开机，管理器显示「工作中」，授权成功；12 个分区只读备份与精确回退件均已就位。

本轮（2026-11-08）做了两件事：

1. 把两处关键授权修复固化进仓库（厂商内核 `kernel/reboot.c` 钩子、模块侧 `dispatch.c` 默认 profile 回退），并接入 `integrate.py` 第 8、9 步；
2. **把 SuSFS 接入 4.14 内核并完整编译通过**：上游 v1.5.5 的 4.14 原生核心 + 自写 v2.3.0 ABI 翻译层，产出 `Image.gz`（51 个 `susfs_` 符号、版本串 `v2.3.0`）。这在 [tools/camellian-susfs](tools/camellian-susfs/) 里，配套一键接入与校验脚本。

> 注意：SuSFS 产物目前只是**编译验证镜像**，用了通用 defconfig、关闭了 LTO/CFI，不能直接刷机。

详细进度：[docs/20261108-0101-当前开发进度-DeepSeek-V4.1-Flash.md](docs/20261108-0101-当前开发进度-DeepSeek-V4.1-Flash.md)、[SUSFS 移植与验证报告](docs/20261108-0210-SUSFS-v2.3.0移植与编译验证-DeepSeek-V4.1-Flash.md)

## 【下一步待实现】

1. **SuSFS 真机可用**：用出厂量产配置 + LTO/CFI 重建 → `pack_boot.py` 打包 → 用户明确授权后刷 `boot_b` → 真机验证 sus_path / sus_mount / sus_kstat；
2. **复现闭环**：按新补丁重建内核，与当前 `final3` 镜像对比校验值或给出功能等价证据；
3. **资产安全**：回传云电脑实际修改文件，给回退件与可用镜像做异地备份；
4. **仓库同步**：合并上游 7 个提交；
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
