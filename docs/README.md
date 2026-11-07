# SukiSU Ultra
<img align='right' src='SukiSU-mini.svg' width='220px' alt="sukisu logo">

> Current branch: `main` (active development) · Forked from KernelSU, independently maintained

**English** | [简体中文](./zh/README.md)

A kernel-based root solution for Android devices, forked from [`tiann/KernelSU`](https://github.com/tiann/KernelSU), with some interesting changes added.

[![Latest release](https://img.shields.io/github/v/release/SukiSU-Ultra/SukiSU-Ultra?label=Release&logo=github)](https://github.com/SukiSU-Ultra/SukiSU-Ultra/releases/latest)
[![Channel](https://img.shields.io/badge/Follow-Telegram-blue.svg?logo=telegram)](https://t.me/Sukiksu)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-orange.svg?logo=gnu)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![GitHub License](https://img.shields.io/github/license/SukiSU-Ultra/SukiSU-Ultra?logo=gnu)](/LICENSE)

## Features

1. Kernel-based `su` and root access management
2. [App Profile](https://sukisu.org/guide/app-profile): Lock up the root power in a cage
3. Support non-GKI and GKI 1.0
4. KPM Support
5. Built-in susfs management tool for one-click root hiding configuration; customizable manager theme.

## Compatibility Status

- SukiSU Ultra supports Android GKI 2.0 devices (kernel 5.10+).
- Older kernels (4.14+) are also compatible, but the kernel will have to be built manually.
- With more backports, kernels 3.x (3.4–3.18) can be supported.
- Currently, only `arm64-v8a`, `armeabi-v7a (bare)` and `X86_64` (some) are supported.
- **Note**: Since forking from `tiann/KernelSU`, this project has evolved independently. Compatibility is based on actual testing in this repository and no longer equals KernelSU's official support scope.

## Installation

Choose the installation method based on your device:

| Scenario | Method | Notes |
|----------|--------|-------|
| GKI device (kernel 5.10+) | Flash boot image | See [`guide/installation.md`](guide/installation.md) |
| Non-GKI / older kernel (4.14+) | Build kernel manually | See [`guide/how-to-integrate.md`](guide/how-to-integrate.md) |
| Need KPM features | Enable `CONFIG_KPM=y` | See "KPM Support" below |

Detailed steps: [`guide/installation.md`](guide/installation.md)

## Integration

See [`guide/how-to-integrate.md`](guide/how-to-integrate.md)

## Project Analysis

- [项目全景分析（中文）](./20261106-2012-项目全景分析-Claude-Opus-6.md): A full walkthrough of the repository layout, kernel and userspace mechanisms, manager ecosystem, build/release pipeline, and current development focus.
- [分叉与远程配置（中文）](./20261106-2025-分叉与远程配置-Claude-Opus-6.md): How this checkout is wired to its fork and upstream, plus the daily push and sync commands.
- [红米 Note 10 5G 兼容性评估（中文）](./20261106-2030-红米Note10-5G兼容性评估-Claude-Opus-6.md): Why a 4.14 non-GKI device cannot use the standard install path, what building a kernel requires, and the lower-effort alternatives.
- [红米 Note 10 5G 实机核对（中文）](./20261106-2037-红米Note10-5G实测核对-Claude-Opus-6.md): Read-only inspection of the actual device over USB, including kernel config, the running root solution, and corrections to the paper assessment.
- [启动锁状态确认（中文）](./20261106-2047-启动锁状态确认-Claude-Opus-6.md): Bootloader-level readback confirming the device is already unlocked, and what that changes for switching root solutions.
- [内核源码与编译环境摸底（中文）](./20261106-2101-内核源码与编译环境摸底-Claude-Opus-6.md): How to locate the kernel source for a specific MIUI build, the exact branch and firmware package found, and why this Mac cannot build it.
- [官方内核源码静态核对（中文）](./20261106-2114-官方内核源码静态核对-Claude-Opus-6.md): Findings from a local shallow clone, including config differences, case-sensitivity issues, and the exact manual-hook call sites.
- [云电脑编译环境体检与量产配置来源结论（中文）](./20261106-2132-云电脑编译环境体检与量产配置来源结论-Claude-Opus-6.md): Remote Linux box readiness, toolchain availability, why the production kernel config is already authoritative, and firmware download feasibility. (Section 3's compiler claim was later corrected — see the next report.)
- [原版内核试编成功与工具链适配（中文）](./20261106-2201-原版内核试编成功与工具链适配-Claude-Opus-6.md): A clean 4.14.186 kernel image was built on the cloud box; records the five necessary adaptations, artifact verification, and a correction to the earlier LTO/clang assumption.
- [SukiSU 集成试编成功与 4.14 兼容适配（中文）](./20261106-2213-SukiSU集成试编成功与4.14兼容适配-Claude-Opus-6.md): The `builtin` branch was integrated into the 4.14 kernel and compiled successfully; documents the hook sites, five compatibility fixes, disabled optional features, and symbol-level artifact verification.
- [原厂线刷包下载与量产内核配置最终核对（中文）](./20261106-2234-原厂线刷包下载与量产内核配置最终核对-Claude-Opus-6.md): Why the Fastboot ROM is the right download, MD5 verification, boot image layout, cross-validation of the production kernel config from the factory image, the final correction on clang/LTO, and flashing-script risks.
- [双槽 VAB 单槽试刷与回退风险对照（中文）](./20261106-2314-双槽VAB单槽试刷与回退风险对照-Claude-Opus-6.md): Why trial-flashing a custom kernel should write only the current slot on this Virtual A/B device, how that differs from a full factory restore, the three-stage rollback order, AVB verification and anti-rollback risks, scripts that must never be used, and a gain/loss comparison against the already installed Magisk Alpha.
- [可刷启动镜像打包与结构校验（中文）](./20261106-2314-可刷启动镜像打包与结构校验-Claude-Opus-6.md): Rebuilds the factory boot image with the self-built SukiSU kernel; records the exact header-v2 layout (including the MediaTek DTB header and AVB footer), three packaging decisions, 12 structural checks, artifact checksums, and known gaps. Nothing was flashed.
- [云电脑资产固化与从零复跑手册（中文）](./20261106-2314-云电脑资产固化与从零复跑手册-Claude-Opus-6.md): All scripts, patches, config excerpts and checksums moved into `tools/camellian/`, plus a stage-by-stage from-scratch rebuild guide for a fresh Linux box.
- [手机只读边界与刷机授权条件（中文）](./20261106-2327-手机只读边界与刷机授权条件-Claude-Opus-6.md): The user's standing rule — the phone stays read-only until flashing is explicitly authorized. Whitelist of allowed read-only checks, blacklist of forbidden write/reboot/slot-switch actions, what counts as authorization, and what to do if the boundary is crossed.
- [红米 Note 10 5G 刷机执行方案与回退剧本（中文）](./20261107-0029-红米Note10-5G刷机执行方案与回退剧本-Claude-Opus-6.md): A step-by-step, not-yet-executed flashing playbook — preconditions, payload freshness checks, moving artifacts from the cloud box to the local Mac, reading back the current slot's boot partition for exact rollback, single-slot flashing, userspace installation via the manager APK, verification criteria, a five-level rollback ladder, red lines, risks, stop conditions and decision points. The phone stays read-only until explicitly authorized.
- [脱离厂商内核升级主线内核可行性评估（中文）](./20261107-0031-脱离厂商内核升级主线内核可行性评估-Claude-Opus-6.md): Answers whether the phone can be moved to mainline Linux 7.x instead of the MediaTek 4.14 vendor kernel. Verifies current kernel.org releases (7.1 is already EOL), explains why Android, HALs, out-of-tree drivers and the bootloader are coupled to the vendor kernel, documents the MT6833 community mainlining status and a Linux 7.2 port on the same chipset, and compares five possible routes. Pure research, no device changes.
- [量产编译配置补验证与用户态组件核对（中文）](./20261107-0016-量产编译配置补验证与用户态组件核对-Claude-Opus-6.md): Corrects the earlier "defconfig omitted the parent switches" claim — the real cause was a first gcc build triggering the kernel Makefile's clang-only option removal. Restores production LTO/CFI, fixes a thin-archive duplicate symbol, fully rebuilds, repacks the boot image with 12 passing checks, and verifies the official userspace binaries, manager APK v2 signature whitelist and UAPI version 6. Nothing was flashed or installed on the phone.
- [可选隐藏特性补齐与再次重编（中文）](./20261107-0804-可选隐藏特性补齐与再次重编-Claude-Opus-6.md): Re-enables the optional features that were disabled during the first 4.14 integration build. The early-boot preinit runner is genuinely back (its 15160-byte blob is embedded in vmlinux) and CPU identity spoof is partially but really implemented for the three 4.14 variables that exist. KPM's switch and framework are compiled in but structurally unusable here — no KernelPatch hook, and the probing symbol names do not exist in Linux 4.14. SuSFS needs out-of-tree kernel patches and was deliberately left off rather than faked. Full rebuild with production LTO/CFI, zero errors, new boot image with 12/12 structural checks, and a documented choice between the two candidate images. Nothing was flashed or installed on the phone.
- [手机分区只读备份与传输污染排查（中文）](./20261107-0852-手机分区只读备份与传输污染排查-Claude-Opus-6.md): Completes the separately authorized read-only partition backup — 12 partitions (the current slot's boot and verification partitions, device-tree overlay, vendor boot, and the other slot) saved to the local Mac with exact kernel-reported sizes, dual-read comparison and a base64 cross-check. Documents and fixes a real pitfall: the adb exec-out channel on this device rewrites every 0x0A byte as 0x0D 0x0A, so a plain dd redirect yields an inflated, corrupted backup (boot_b gained 105890 bytes); the earlier "trim the tail" approach and the flashing playbook's backup command are corrected. Proves the saved boot_b really is the Magisk-patched image (ramdisk grew versus factory, magisk marker present, AVB footer at the right offset). No flashing, reboot, slot switch, file push or app install was performed.
- [启动镜像版本核对与回退件定位（中文）](./20261107-0905-启动镜像版本核对与回退件定位-Claude-Opus-6.md): Checks the four boot images now on hand and proves that two generations are mixed. The user-provided factory and Magisk-patched images (kernel 4.14.186-perf-ga368196f0bd0, built 2023-03-10) belong to the OTHER slot generation, not the current b slot (kernel gf8d872e9279c, built 2023-09-14). Only boot_b-before.img is the exact restore image for the current slot; the same-generation clean factory image (md5 f8e4f42a4538b03c519bb70921d88bcc) is still on the cloud box. Explains the rollback choice and corrects the flashing playbook. Read-only analysis; nothing was flashed.

## KPM Support

Based on [KernelPatch](https://github.com/bmax121/KernelPatch), we removed features redundant with KSU and retained only KPM support.

**Current status**:
- ✅ Basic KPM loading is available (requires `CONFIG_KPM=y`)
- 🚧 APatch compatibility expansion is in progress (some features not yet merged)
- ⚠️ Non-GKI devices additionally require `CONFIG_KALLSYMS=y` and `CONFIG_KALLSYMS_ALL=y`
- ⚠️ Kernels below 4.19 require backporting `set_memory.h` from 4.19

**Open-source repository**: [ShirkNeko/SukiSU_KernelPatch_patch](https://github.com/ShirkNeko/SukiSU_KernelPatch_patch)  
**KPM template**: [udochina/KPM-Build-Anywhere](https://github.com/udochina/KPM-Build-Anywhere)

## Troubleshooting

1. **Device stuck after uninstalling the manager app?**  
   Uninstall `_com.sony.playmemories.mobile_`.

2. **KPM fails to load?**  
   Confirm the kernel has `CONFIG_KPM=y` enabled; Non-GKI devices also need `CONFIG_KALLSYMS=y` and `CONFIG_KALLSYMS_ALL=y`.

3. **Manager cannot detect root?**  
   Confirm the flashed kernel matches the manager version, and check that `su` is in PATH.

4. **Kernel build errors?**  
   Refer to [`guide/how-to-integrate.md`](guide/how-to-integrate.md), and confirm the kernel version meets the minimum requirement (4.14+).

## Translation

If you need to contribute to the translation of the manager, please go to [Weblate](https://hosted.weblate.org/projects/sukisu-ultra/).

<a href="https://hosted.weblate.org/engage/sukisu-ultra/"><img src="https://hosted.weblate.org/widget/sukisu-ultra/multi-auto.svg" alt="Translation status"></a>

## Sponsor

- [ShirkNeko](https://afdian.com/a/shirkneko) (maintainer of SukiSU)
- [weishu](https://github.com/sponsors/tiann) (author of KernelSU)

<details>
<summary>ShirkNeko's sponsorship list</summary>

- [Ktouls](https://github.com/Ktouls) Thanks so much for bringing me support.
- [zaoqi123](https://github.com/zaoqi123) Thanks for the milk tea.
- [wswzgdg](https://github.com/wswzgdg) Many thanks for supporting this project.
- [yspbwx2010](https://github.com/yspbwx2010) Many thanks.
- [DARKWWEE](https://github.com/DARKWWEE) 100 USDT
- [Saksham Singla](https://github.com/TypeFlu) Provide and maintain the website
- [OukaroMF](https://github.com/OukaroMF) Donation of website domain name

</details>

## License

- The files in the `kernel` directory are under [GPL-2.0-only](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html) license.
- The images of the files `ic_launcher(?!.*alt.*).*` with anime character artwork are licensed under a special arrangement: drawn by [怡子曰曰](https://space.bilibili.com/10545509), the copyright is held by [明风 OuO](https://space.bilibili.com/274939213), and the vectorized icons are provided by this project. See [`LICENSE_icon_English`](./LICENSE_icon_English) and [`LICENSE_icon_SC`](./LICENSE_icon_SC) for details.
- Except for the files or directories mentioned above, all other parts are under [GPL-3.0 or later](https://www.gnu.org/licenses/gpl-3.0.html) license.

## Credit

- [KernelSU](https://github.com/tiann/KernelSU): upstream
- [MKSU](https://github.com/5ec1cff/KernelSU): Magic Mount
- [RKSU](https://github.com/rsuntk/KernelsU): support non-GKI
- [susfs](https://gitlab.com/simonpunk/susfs4ksu): An addon root hiding kernel patches and userspace module for KernelSU.
- [KernelPatch](https://github.com/bmax121/KernelPatch): KernelPatch is a key part of the APatch implementation of the kernel module

Contributions welcome via PR; translations via [Weblate](https://hosted.weblate.org/projects/sukisu-ultra/); issues via [GitHub Issues](https://github.com/SukiSU-Ultra/SukiSU-Ultra/issues).

<details>
<summary>KernelSU's credit</summary>

- [Kernel-Assisted Superuser](https://git.zx2c4.com/kernel-assisted-superuser/about/): The KernelSU idea.
- [Magisk](https://github.com/topjohnwu/Magisk): The powerful root tool.
- [genuine](https://github.com/brevent/genuine/): APK v2 signature validation.
- [Diamorphine](https://github.com/m0nad/Diamorphine): Some rootkit skills.
</details>
