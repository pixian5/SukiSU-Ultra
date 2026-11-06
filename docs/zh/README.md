# SukiSU Ultra
<img align='right' src='SukiSU-mini.svg' width='220px' alt="sukisu logo">

> 当前分支：`main`（活跃开发中）· 基于 KernelSU 分叉，独立演进

**简体中文** [English](../README.md) | 

一个 Android 上基于内核的 root 方案，由 [`tiann/KernelSU`](https://github.com/tiann/KernelSU) 分叉而来，添加了一些有趣的变更。

[![最新发行](https://img.shields.io/github/v/release/SukiSU-Ultra/SukiSU-Ultra?label=Release&logo=github)](https://github.com/SukiSU-Ultra/SukiSU-Ultra/releases/latest)
[![频道](https://img.shields.io/badge/Follow-Telegram-blue.svg?logo=telegram)](https://t.me/Sukiksu)
[![协议: GPL v2](https://img.shields.io/badge/License-GPL%20v2-orange.svg?logo=gnu)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![GitHub 协议](https://img.shields.io/github/license/SukiSU-Ultra/SukiSU-Ultra?logo=gnu)](/LICENSE)

## 特性

1. 基于内核的 `su` 和权限管理。
2. [App Profile](https://sukisu.org/zh/guide/app-profile)：把 Root 权限关进笼子里。
3. 支持 non-GKI 与 GKI 1.0。
4. KPM 支持。
5. 内置 susfs 管理工具，支持一键配置 root 隐藏；管理器主题可自定义。

## 兼容状态

- SukiSU Ultra 支持 GKI 2.0 设备（内核版本 5.10 以上）。
- 旧内核也可兼容（最低 4.14+），但需要自行编译内核。
- 通过更多反向移植，可支持 3.x 内核（3.4–3.18）。
- 目前支持架构：`arm64-v8a`、`armeabi-v7a (bare)`、`X86_64`。
- **注意**：本项目自 `tiann/KernelSU` 分叉后独立演进，兼容性以本仓库实测为准，不再等同于 KernelSU 官方支持范围。

## 安装指导

根据你的设备选择安装方式：

| 场景 | 方式 | 说明 |
|------|------|------|
| GKI 设备（内核 5.10+） | 刷入 boot 镜像 | 详见 [`guide/installation.md`](guide/installation.md) |
| 非 GKI / 旧内核（4.14+） | 手动编译内核 | 详见 [`guide/how-to-integrate.md`](guide/how-to-integrate.md) |
| 需要使用 KPM 功能 | 需开启 `CONFIG_KPM=y` | 见下方「KPM 支持」 |

详细步骤见 [`guide/installation.md`](guide/installation.md)。

## 集成指导

查看 [`guide/how-to-integrate.md`](guide/how-to-integrate.md)

## 项目分析

- [项目全景分析](../20261106-2012-项目全景分析-Claude-Opus-6.md)：仓库分层结构、内核与用户态提权机制、隐藏检测机制、管理器主题商店生态、构建发布链路，以及当前开发重心的完整梳理。
- [分叉与远程配置](../20261106-2025-分叉与远程配置-Claude-Opus-6.md)：本机这份检出的分叉地址、远程布局，以及日常推送与同步上游的常用命令。
- [红米 Note 10 5G 兼容性评估](../20261106-2030-红米Note10-5G兼容性评估-Claude-Opus-6.md)：4.14 非通用内核规范机型为何不能直接刷现成包、自行编译内核需要什么，以及更省事的替代方案。
- [红米 Note 10 5G 实机核对](../20261106-2037-红米Note10-5G实测核对-Claude-Opus-6.md)：通过 USB 调试只读采集真实设备状态，含内核配置、已运行的 root 方案，以及对纸面评估的更正。
- [启动锁状态确认](../20261106-2047-启动锁状态确认-Claude-Opus-6.md)：进刷机模式读到底层变量，证实启动锁已解开，以及这对更换 root 方案意味着什么。
- [内核源码与编译环境摸底](../20261106-2101-内核源码与编译环境摸底-Claude-Opus-6.md)：如何按 MIUI 版本码定位内核源码、实际找到的分支与官方线刷包，以及本机为何编不了这颗内核。
- [官方内核源码静态核对](../20261106-2114-官方内核源码静态核对-Claude-Opus-6.md)：本机浅克隆后的配置差异、大小写冲突问题，以及手动挂钩的具体落点。
- [云电脑编译环境体检与量产配置来源结论](../20261106-2132-云电脑编译环境体检与量产配置来源结论-Claude-Opus-6.md)：云电脑能否承担编译、官方编译器还能不能拿到、量产配置差异的定论，以及原厂固件包的下载可行性。（文中「必须用 clang」的判断已被后续试编更正，见下一条。）
- [原版内核试编成功与工具链适配](../20261106-2201-原版内核试编成功与工具链适配-Claude-Opus-6.md)：在云电脑上成功编出 4.14.186 原版内核镜像；记录为跑通所做的 5 处适配、产物核验结果，以及对上一份文档编译器判断的更正。
- [SukiSU 集成试编成功与 4.14 兼容适配](../20261106-2213-SukiSU集成试编成功与4.14兼容适配-Claude-Opus-6.md)：把 `builtin` 分支接入 4.14 内核并编译成功；记录四处挂钩落点、5 类兼容补丁、主动关闭的可选特性，以及符号级产物核验。
- [原厂线刷包下载与量产内核配置最终核对](../20261106-2234-原厂线刷包下载与量产内核配置最终核对-Claude-Opus-6.md)：为什么该下线刷包、MD5 校验、启动分区镜像结构、用原厂固件交叉验证量产配置、关于 clang/LTO 的最终更正，以及官方刷机脚本里的风险点。
- [双槽 VAB 单槽试刷与回退风险对照](../20261106-2314-双槽VAB单槽试刷与回退风险对照-Claude-Opus-6.md)：这台虚拟 A/B 设备试刷自定义内核为什么只该写当前槽、它与官方全量恢复的区别、三级回退顺序、启动校验与防回滚的影响、绝对不能用的脚本，以及与已装好的 Magisk Alpha 的得失对照。
- [可刷启动镜像打包与结构校验](../20261106-2314-可刷启动镜像打包与结构校验-Claude-Opus-6.md)：用原厂启动镜像作基线换入自编内核；记录启动镜像头版本 2 的精确布局（含联发科设备树私有头与校验尾标）、三个打包决策、12 项结构校验、产物校验值与遗留问题。没有刷入手机。
- [云电脑资产固化与从零复跑手册](../20261106-2314-云电脑资产固化与从零复跑手册-Claude-Opus-6.md)：脚本、补丁、配置摘录与校验值全部收进 `tools/camellian/`，并给出在一台全新 Linux 机器上从零复跑的分阶段步骤。
- [手机只读边界与刷机授权条件](../20261106-2327-手机只读边界与刷机授权条件-Claude-Opus-6.md)：用户确立的长期边界——明确说刷机之前手机只读。列清允许的只读查询、禁止的写分区/重启/切槽/装应用等动作、什么才算授权、以及越界后的处理方式。

## KPM 支持

基于 [KernelPatch](https://github.com/bmax121/KernelPatch) 开发，移除了与 KernelSU 重复的功能，仅保留 KPM 支持。

**当前状态**：
- ✅ 基础 KPM 加载已可用（需开启 `CONFIG_KPM=y`）
- 🚧 APatch 兼容性扩展进行中（部分功能尚未合并）
- ⚠️ Non-GKI 设备需额外开启 `CONFIG_KALLSYMS=y` 和 `CONFIG_KALLSYMS_ALL=y`
- ⚠️ 内核低于 4.19 需从 4.19 的 `set_memory.h` 反向移植

**开源仓库**：[ShirkNeko/SukiSU_KernelPatch_patch](https://github.com/ShirkNeko/SukiSU_KernelPatch_patch)  
**KPM 模板**：[udochina/KPM-Build-Anywhere](https://github.com/udochina/KPM-Build-Anywhere)

## 故障排除

1. **卸载管理器后系统卡住？**  
   卸载 `_com.sony.playmemories.mobile_`。

2. **KPM 加载失败？**  
   确认内核已开启 `CONFIG_KPM=y`；Non-GKI 设备还需 `CONFIG_KALLSYMS=y` 和 `CONFIG_KALLSYMS_ALL=y`。

3. **管理器无法识别 root？**  
   确认刷入的内核与管理器版本匹配，并检查 `su` 是否在 PATH 中。

4. **内核编译报错？**  
   参考 [`guide/how-to-integrate.md`](guide/how-to-integrate.md)，并确认内核版本满足最低要求（4.14+）。

## 参与翻译

要将 SukiSU 翻译成您的语言，或完善现有的翻译，请使用 [Weblate](https://hosted.weblate.org/projects/sukisu-ultra/)。

<a href="https://hosted.weblate.org/engage/sukisu-ultra/"><img src="https://hosted.weblate.org/widget/sukisu-ultra/multi-auto.svg" alt="翻译状态"></a>

## 许可证

- 目录 `kernel` 下所有文件为 [GPL-2.0-only](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)。
- 有动漫人物图片表情包的这些文件 `ic_launcher(?!.*alt.*).*` 图标以特别的形式授权，怡子曰曰绘制，版权明风OuO所有。矢量化图标由本项目提供。详见 [`LICENSE_icon_English`](./LICENSE_icon_English) 与 [`LICENSE_icon_SC`](./LICENSE_icon_SC)。
- 除上述文件及目录的其他部分均为 [GPL-3.0-or-later](https://www.gnu.org/licenses/gpl-3.0.html)。

## 赞助

- [ShirkNeko](https://afdian.com/a/shirkneko)（SukiSU 主要维护者）
- [weishu](https://github.com/sponsors/tiann)（KernelSU 作者）

<details>
<summary>ShirkNeko 的赞助列表</summary>

- [Ktouls](https://github.com/Ktouls) 非常感谢你给我带来的支持
- [zaoqi123](https://github.com/zaoqi123) 请我喝奶茶也不错
- [wswzgdg](https://github.com/wswzgdg) 非常感谢对此项目的支持
- [yspbwx2010](https://github.com/yspbwx2010) 非常感谢
- [DARKWWEE](https://github.com/DARKWWEE) 感谢老哥的 100 USDT
- [Saksham Singla](https://github.com/TypeFlu) 网站的提供以及维护
- [OukaroMF](https://github.com/OukaroMF) 网站域名捐赠

</details>

## 鸣谢

- [KernelSU](https://github.com/tiann/KernelSU)：上游
- [MKSU](https://github.com/5ec1cff/KernelSU)：魔法坐骑支持
- [RKSU](https://github.com/rsuntk/KernelsU)：non-GKI 支持
- [susfs](https://gitlab.com/simonpunk/susfs4ksu)：隐藏内核补丁以及用户空间模组的 KernelSU 附件
- [KernelPatch](https://github.com/bmax121/KernelPatch)：KernelPatch 是内核模块 APatch 实现的关键部分

欢迎提交 PR；翻译请前往 [Weblate](https://hosted.weblate.org/projects/sukisu-ultra/)；问题反馈请开 [Issue](https://github.com/SukiSU-Ultra/SukiSU-Ultra/issues)。

<details>
<summary>KernelSU 的鸣谢</summary>

- [kernel-assisted-superuser](https://git.zx2c4.com/kernel-assisted-superuser/about/)：KernelSU 的灵感。
- [Magisk](https://github.com/topjohnwu/Magisk)：强大的 root 工具箱。
- [genuine](https://github.com/brevent/genuine/)：apk v2 签名验证。
- [Diamorphine](https://github.com/m0nad/Diamorphine)：一些 rootkit 技巧。
</details>
