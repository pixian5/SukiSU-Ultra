# SUSFS 可刷 boot 镜像构建与产物

> 时间：2026-11-08 02:45（GMT+8）
> 模型：DeepSeek-V4.1-Flash
> 结论：**已用出厂量产配置 + LTO/CFI 编出可刷入的 `boot` 镜像**，10/10 结构校验通过。
> 本轮只产出文件，**没有刷机、没有碰手机**。

---

## 0. 一句话结论

用你上传的原厂 `boot-stock.img`（MD5 `f8e4f42a4538b03c519bb70921d88bcc`）取出出厂 `ikconfig`，在 `feat/susfs-4.14` 源码上打开 SukiSU + SuSFS，保留量产 LTO/CFI 全量编译，再把新内核装回原厂内存盘/DTB，得到：

| 项 | 值 |
| --- | --- |
| 产物 | `dist/boot-sukisu-susfs-lto-stockdtb.img` |
| 大小 | 67,108,864 字节（64 MiB，与分区一致） |
| MD5 | `322fd6381c8b6d546b0298fbd1b7736f` |
| SHA256 | `c3c2c6d75382ed06ebcbbd3dd9bbbf8dc234410860fa47de99b122ec98a44760` |
| 内核 | `4.14.186-perf-gf4e416aea-dirty #1 SMP PREEMPT Sun Nov 8 02:29:57 CST 2026` |
| 配置 | 出厂配置 + KSU/SUSFS；`LTO_CLANG/THINLTO/CFI_CLANG` 全部开启 |
| 结构校验 | 10/10 PASS |

---

## 1. 输入与来源

| 输入 | 说明 |
| --- | --- |
| 原厂 boot | 用户上传 `boot-stock.img`，67,108,864 字节，MD5 `f8e4f42a4538b03c519bb70921d88bcc`，与同代干净原厂件一致 |
| 出厂配置 | 从原厂内核内嵌 `IKCFG_ST…IKCFG_ED` 解出，5,486 行，`CONFIG_LOCALVERSION="-perf"` |
| 内核源码 | `MiCode/Xiaomi_Kernel_OpenSource` `camellian-t-oss` `f4e416aea` |
| SukiSU 源码 | 分支 `feat/susfs-4.14`（含 SuSFS 4.14 适配与 v2.3.0 ABI 层） |
| 工具链 | AOSP prebuilt clang-r383902（clang 11.0.1）+ LLD 11.0.1 |

原厂镜像结构（解包实测）：

```
header v2 / page 2048
kernel_size   13342418
ramdisk_size  21078370
dtb_size        161191
vbmeta_size       1664
```

## 2. 配置改动（相对出厂）

| 选项 | 出厂 | 现在 | 原因 |
| --- | --- | --- | --- |
| `CONFIG_KSU` | 无 | y | SukiSU 内核集成 |
| `CONFIG_KSU_MANUAL_SU` | — | y | 4.14 手动挂钩 |
| `CONFIG_KSU_FEATURE_ADBROOT` | — | y | 保留原功能 |
| `CONFIG_KSU_SUSFS*` | 无 | 全 y | 本次目标 |
| `CONFIG_KALLSYMS_ALL` | n | **y** | 隐藏 ksu/susfs 符号需要；代价是内核略大 |
| `CONFIG_KSU_DEBUG` | — | n | 安全：避免 `adb shell su` 直通 |
| `CONFIG_KPM` | — | n | 4.14 结构性不可用 |
| `CONFIG_MIHW` | y | **n** | 开源树缺 `vendor/xiaomi/kernel_modules/mihw`，无法编译 |
| `CONFIG_FRAME_WARN` | 3600 | **0** | 厂商触摸屏驱动栈帧 4.2 KB，`-Werror` 下会中断编译；只放宽告警 |
| `CONFIG_LTO/THINLTO/CFI_CLANG*` | y | 保持 y | 与出厂量产一致 |

编译日志无 error，只有厂商代码的既有 warning。

## 3. 产物结构校验（bootimg.py）

```
PASS  size matches factory          (67108864)
PASS  header magic                  (ANDROID!)
PASS  kernel_size patched           (14190984)
PASS  ramdisk_size unchanged        (21078370)
PASS  kernel intact
PASS  ramdisk intact
PASS  dtb intact
PASS  vbmeta intact
PASS  AVB footer magic
PASS  padding zeroed
```

新布局：kernel 在 2048；ramdisk 随内核大小后移；DTB、vbmeta 顺延；AVB footer 的 `original_image_size` 与 `vbmeta_offset` 已重定位。vbmeta 内的哈希描述仍是原厂的，无法在没有厂商私钥时重签——**与当前已运行的 Magisk 方案同条件**，解锁 bootloader 下校验错误不致命。

## 4. 符号与版本验证

- vmlinux 中 `susfs_` 符号 **52 个**
- 关键入口全部存在：`susfs_init`、`susfs_add_sus_path(_loop)`、`susfs_add_sus_kstat`、`susfs_add_open_redirect`、`susfs_set_uname`、`susfs_set_cmdline_or_bootconfig`、`susfs_add_sus_map`、`susfs_set_avc_log_spoofing`、`susfs_set_priority_uid_filter`、`susfs_show_version/variant/features`、`susfs_start_sdcard_monitor_fn`
- SukiSU 钩子：`ksu_handle_sys_reboot`、`ksu_handle_setresuid`、`ksu_handle_execveat`、`ksu_handle_stat`
- vmlinux 字符串：`susfs is initialized! version: v2.3.0`
- 版本串与设备内核同代：`4.14.186-perf-gf4e416aea-dirty`

内核本体：`Image.gz` 14,190,984 字节，MD5 `293f3ceef2caaa6936073ae8bbacb8f0`，SHA256 `47c2809398229d5492ddbf94a5fb70fa815ab1cce8a79e24409d128fd486b8d6`。

## 5. 刷机步骤（需要你明确授权并执行）

> 刷机会写 `boot_b`。请先确认回退件在手：`backup/camellian/boot_b-before.img`（MD5 `531c534bcc8d3172e03b12a2f6dd135d`）。

```bash
# 1. 把产物下载到 Mac，核对校验值
shasum -a 256 boot-sukisu-susfs-lto-stockdtb.img
# 应为 c3c2c6d75382ed06ebcbbd3dd9bbbf8dc234410860fa47de99b122ec98a44760

# 2. 手机进入 fastboot（关机后按住 音量下 + 电源）
fastboot devices
fastboot getvar current-slot        # 应为 b

# 3. 只写当前槽
fastboot flash boot_b boot-sukisu-susfs-lto-stockdtb.img
fastboot reboot
```

**回退**（任选其一）：

```bash
# 恢复到刷机前（含 Magisk）
fastboot flash boot_b backup/camellian/boot_b-before.img
# 或恢复同代干净原厂（无 root）
fastboot flash boot_b backup/camellian/boot-stock.img
```

## 6. 刷后验证判据

1. 能正常开机、无重启循环；
2. 管理器显示「**工作中**」，授权开关可用；
3. 进程列表有 `com.sukisu.ultra:root:0`；
4. 内核日志出现 `susfs is initialized! version: v2.3.0`；
5. `ksud susfs status` 显示 `v2.3.0 / NON-GKI`；
6. 管理器 SuSFS 页能读取特性列表；
7. 用 Momo / 检测类 App 复测之前的「找到 Magisk / Zygisk / 代码注入」报告是否消失。

**不要**用 `adb shell su` 判断成败（调试模式关闭时本来不可用）。

## 7. 风险与边界

- **未真机验证**：本文只保证编译、符号与镜像结构；开机与隐藏效果需刷后验证。
- **KPM 不可用**：4.14 缺 KernelPatch 钩子，已关闭。
- **sus_map / avc_log_spoofing / priority_uid_filter 不生效**：ABI 已注册但无内核钩子，管理器可能显示「支持」，不要据此判断隐蔽性。
- **sus_path_loop 退化为一次性添加**。
- **MIHW 关闭**：小米的 millet 模块不在开源树；若真机某小米专有功能异常，优先怀疑这里。
- **AVB 哈希未重签**：与现有 Magisk 方案同条件；若 bootloader 重新上锁会无法启动。
- **首次开机可能较慢**：新内核 + KALLSYMS_ALL，属正常。

## 8. 复现命令

```bash
# 1. 取出厂配置
python3 tools/camellian-susfs/scripts/bootimg.py unpack boot-stock.img -o factory/
python3 tools/camellian-susfs/scripts/extract-ikconfig.py factory/kernel -o .config

# 2. 打开 KSU/SUSFS、关 debug/KPM/MIHW、放宽 FRAME_WARN
#    见 config/susfs-4.14-config.txt 与本报告第 2 节

# 3. 编译（与本次完全一致的工具链与参数）
make O=out ARCH=arm64 CC=clang CLANG_TRIPLE=aarch64-linux-gnu- \
     CROSS_COMPILE=aarch64-linux-gnu- LD=ld.lld NM=llvm-nm \
     OBJCOPY=llvm-objcopy AR=llvm-ar OBJDUMP=llvm-objdump \
     READELF=llvm-readelf STRIP=llvm-strip -j3 Image.gz

# 4. 重打包
python3 tools/camellian-susfs/scripts/bootimg.py repack \
     boot-stock.img out/arch/arm64/boot/Image.gz -o boot-sukisu-susfs.img
```

---

## 关联文档

- [SUSFS v2.3.0 移植与编译验证](./20261108-0210-SUSFS-v2.3.0移植与编译验证-DeepSeek-V4.1-Flash.md)
- [SukiSU 用户态链路修复与授权验证](./20261107-2230-SukiSU用户态链路修复与授权验证-Claude-Opus-6.md)
- [红米 Note 10 5G 刷机执行方案与回退剧本](./20261107-0029-红米Note10-5G刷机执行方案与回退剧本-Claude-Opus-6.md)
