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
- [红米 Note 10 5G 刷机执行方案与回退剧本](../20261107-0029-红米Note10-5G刷机执行方案与回退剧本-Claude-Opus-6.md)：尚未执行的逐步刷机剧本——前置条件、载荷新鲜度核对、云电脑产物回传本机、读回当前槽启动分区做精确复原备份、单槽写入、通过管理器安装包完成用户态接入、验证判据、五级回退顺序、红线、风险与停止条件、以及需要拍板的三个点。明确说「刷机」之前手机保持只读。
- [脱离厂商内核升级主线内核可行性评估](../20261107-0031-脱离厂商内核升级主线内核可行性评估-Claude-Opus-6.md)：回答能否把手机从联发科 4.14 厂商内核换到 7.x 主线内核。核实当前主线版本（7.1 已停止维护）、讲清安卓与厂商驱动/引导链的耦合、记录 MT6833 社区主线化现状与同芯片 Linux 7.2 移植实例，并对照五条可行路线。纯调研，没有动手机。
- [量产编译配置补验证与用户态组件核对](../20261107-0016-量产编译配置补验证与用户态组件核对-Claude-Opus-6.md)：更正此前「开源配置漏抄父开关」的错误说法（真因是第一次误用 gcc 触发构建系统自动删除 clang 专属配置）；补回量产链接时优化与控制流完整性、修掉瘦归档重复符号、全量重编、重新打包启动镜像并通过 12 项校验；核对官方用户态组件、管理器安装包签名白名单与接口版本 6。全程没有刷机、没有往手机装任何东西。
- [可选隐藏特性补齐与再次重编](../20261107-0804-可选隐藏特性补齐与再次重编-Claude-Opus-6.md)：把第一次集成时为能在 4.14 上编译通过而关掉的可选特性逐一试开。开机早期运行器真正补回（15,160 字节运行器二进制已内嵌进内核），CPU 身份伪装补回 4.14 上真实可做的三项；内核补丁模块只补回开关与框架，因缺 KernelPatch 钩子且 4.14 的符号命名对不上而结构性不可用；SuSFS 属外部补丁，明确关闭、不做假实现。保留量产链接时优化与控制流完整性全量重编，零错误，新启动镜像 12 项校验全通过，并写明两份候选镜像的取舍与推荐。全程没有刷机、没有往手机装任何东西。
- [手机分区只读备份与传输污染排查](../20261107-0852-手机分区只读备份与传输污染排查-Claude-Opus-6.md)：在用户单独点名的只读授权下，把 12 个分区（当前槽启动分区、各校验分区、设备树叠加、供应商启动分区及另一槽对应分区）读回本机保存，逐份做精确大小、两次独立读取比对与文本编码交叉验证。记录并修正一个真实坑：本机 USB 调试通道会把二进制里每个换行字节改写成「回车+换行」，直接读回的备份会被撑大损坏（启动分区多出 105,890 字节），旧的「截掉尾部」做法作废，刷机剧本里的备份命令已更正。并证明读回的启动分区确为带 Magisk 的那份（内存盘比原厂大、能搜到面具标记、校验尾位置正确）。全程没有刷写、重启、切槽、推文件或安装应用。
- [启动镜像版本核对与回退件定位](../20261107-0905-启动镜像版本核对与回退件定位-Claude-Opus-6.md)：核对手上四份启动镜像，证明混了两个代际。用户提供的原厂与面具修补版（内核 `ga368196f0bd0`、2023-03-10 编译）属于另一槽那一代，不是当前 b 槽（内核 `gf8d872e9279c`、2023-09-14 编译）。只有 `boot_b-before.img` 是当前槽的精确复原件；同代干净原厂镜像（MD5 `f8e4f42a4538b03c519bb70921d88bcc`）仍在云电脑上。写明回退件取舍并更正刷机剧本。纯只读分析，没有刷任何东西。
- [V14.0.6.0 官方卡刷包下载、boot.img 提取与版本对照](../20261107-0935-V14.0.6.0原厂镜像下载提取与版本对照-Claude-Opus-6.md)：在云电脑下载 3.87 GB 的 MIUI Global V14.0.6.0 整包并校验，用 payload-dumper-go 2.1.0 从 `payload.bin` 解出 boot/dtbo/vbmeta 镜像，与当前 V14.0.4.0 EEA 版本对照。关键发现：内核版本串完全相同（`4.14.186-perf-gf8d872e9279c`），但构建批次不同——构建者标识不同、编译时间晚 5 天、内核小 1,535 字节、内存盘大 12 字节，所以「版本串相同」不等于「同一份镜像」。没有刷任何东西，也没碰手机。
- [首次真机试刷与 SukiSU 接入验证](../20261107-1110-首次真机试刷与SukiSU接入验证-Claude-Opus-6.md)：第一次真机刷入。自编 4.14 内核成功开机，SukiSU 管理器显示「工作中」，后台有以 root 运行的子进程。完整记录时间线（推荐版 → 调试版诊断 → 关闭调试的最终版）、以及用 `adb shell su` 当判据导致的误判（关闭调试模式时它本来就不可用）和正确判据。只写了当前槽启动分区，另一槽、校验分区、用户数据均未动；精确回退件仍在。
- [SukiSU 用户态链路修复与授权验证](../20261107-2230-SukiSU用户态链路修复与授权验证-Claude-Opus-6.md)：修掉阻塞 root 授权的三处接口不匹配——`reboot` 系统调用缺钩子导致后台子进程拿不到通道、读取不存在的应用配置时返回「不存在」导致管理器误判「更新 app profile 失败」、以及管理器界面入口被自身隐藏功能禁用（重装 APK 恢复）。修复后管理器日志 `install result: true`、显示「工作中」、授权成功。含当前镜像校验值与后续建议。
- [SuSFS 隐藏方案编译交接文档](../20261108-0135-SuSFS隐藏方案编译交接文档-Claude-Opus-6.md)：给另一台云电脑上的 AI 使用的自包含交接说明。列出全部公开仓库与版本（内核 camellian-t-oss、SukiSU builtin、SuSFS 1.4.2-kernel-4.14）、补丁应用顺序、配置开关、编译命令、打包脚本、验收标准、七个已知坑（1.3.8 API 不匹配、缺 susfs_def.h、reboot 钩子、app profile fallback、管理器 alias、ADB 换行改写、GitLab TLS），以及产物传输约定。凭证不写入仓库。
- [项目现状复核与复现风险](../20261108-0046-项目现状复核与复现风险-DeepSeek-V4.1-Flash.md)：刷机成功后的只读复核。实测当前镜像与回退件校验值一致；仓库比上游多 28 个文档/工具提交、少 7 个上游提交，项目本体源码零改动。最重要发现：让授权修通的两处修改（内核树 `reboot.c` 钩子、模块侧 `dispatch.c` 默认配置回退）只存在于云电脑构建树，仓库任何补丁或脚本里都没有，按现有资产从零重建无法得到当前可用镜像。文档给出按优先级排列的整改建议。
- [当前开发进度](../20261108-0101-当前开发进度-DeepSeek-V4.1-Flash.md)：里程碑表、当前运行配置与校验值、本轮改动（两处授权补丁入库并接入 `integrate.py` 第 8/9 步）、验证方式与已知限制。
- [下一步待实现](../20261108-0101-下一步待实现-DeepSeek-V4.1-Flash.md)：按 P0–P3 排列的待办与验收标准——重建对比闭环、云电脑修改文件回传、异地备份、合并上游、真机收尾、KPM/SuSFS 可选再评估，以及「不要做」清单。
- [SUSFS v2.3.0 移植与编译验证](../20261108-0210-SUSFS-v2.3.0移植与编译验证-DeepSeek-V4.1-Flash.md)：把 SuSFS 接到 4.14 手动挂钩内核——上游 v1.5.5 的 4.14 核心 + v2.3.0 ABI 翻译层。记录四处 SukiSU 侧修复（5.x 专属 sucompat 分支、缺 setresuid 钩子、缺 `strncpy_from_user_nofault`、adb_root 签名）、三个厂商树编译阻塞、沙箱内完整编译结果（`Image.gz` 11,508,451 字节、51 个 susfs 符号、v2.3.0 字符串）、逐项能力边界，以及为什么这份产物只能算编译验证、不能刷机。

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
