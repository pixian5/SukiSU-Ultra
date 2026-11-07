# SuSFS 4.14 移植包（camellian / 红米 Note 10 5G）

把 **SUSFS** 接入 SukiSU Ultra 的 4.14 手动挂钩内核。目标设备是红米 Note 10 5G（camellia，MT6833，内核 4.14.186，非 GKI）。

## 为什么需要这个移植包

- 上游 `susfs4ksu` 给 4.14 的补丁停在 **v1.5.5**（2025-02），命令 ABI 是旧的。
- SukiSU Ultra `builtin` 分支（当前设备在用的分支）要求 **SUSFS v2.3.0** 的命令 ABI：函数签名是 `void fn(void __user **)`，结构体带 `err` 字段，另有 `sus_map`、`avc_log_spoofing`、`priority_uid_filter`、`sus_path_loop` 等新命令。
- 直接把 v2.3.0 的 5.10 补丁往 4.14 上套不可行（mm/selinux/fs 大量接口不同）。

因此采用**混合实现**：

| 层 | 来源 | 作用 |
| --- | --- | --- |
| 内核钩子 | `susfs4ksu` `kernel-4.14` 分支 v1.5.5 | 提供 4.14 原生的 fs 钩子、inode 标记、mnt_id 伪造 |
| 核心实现 | v1.5.5 4.14 代码 + 少量改造（`fs/susfs.c`） | 实际的 sus_path / sus_mount / sus_kstat / uname / cmdline / open_redirect |
| ABI 层 | 参考 `yao140514/oppoa2m-sukisu-susfs` 的 v2.3.0 适配层，按 4.14 调整（`fs/susfs_abi.c`） | 把 v2.3.0 的 16 条命令翻译成 v1.5.5 核心调用 |
| 头文件 | v2.3.0 结构体布局（`include/linux/susfs.h`、`susfs_def.h`） | 让管理器看到它期望的 v2.3.0 |

SukiSU 侧另有三处 4.14 适配（见 `patches/` 与仓库 `kernel/` 的提交）：

1. `feature/sucompat.c`、`sucompat.h`：SUSFS 版钩子限定 `LINUX_VERSION_CODE >= 5.0`。4.14 的 `vfs_statx`/`faccessat` 传的是用户路径字符串，按 5.x 的 `struct filename *` 解释会在开机 1 秒内 data abort（社区已有实际崩溃记录）。
2. `kernel/sys.c`：SUSFS 模式下 LSM `task_fix_setuid` 钩子不注册，必须在 `SYSCALL_DEFINE3(setresuid)` 里调用 `ksu_handle_setresuid()`，否则应用进程不会被标记 umounted、拿不到驱动 fd。
3. `kernel_compat.h`：补 `strncpy_from_user_nofault()`（5.8 才引入）。

## 目录

```
tools/camellian-susfs/
├── README.md
├── VERSION
├── config/susfs-4.14-config.txt     需要开启的 CONFIG
├── kernel/                          要覆盖进内核树的文件
│   ├── fs/susfs.c                   v1.5.5 4.14 核心（改造版）
│   ├── fs/susfs_abi.c               v2.3.0 ABI 翻译层
│   └── include/linux/susfs.h
│       include/linux/susfs_def.h
├── patches/
│   ├── 50_add_susfs_in_kernel-4.14.patch   上游 v1.5.5 补丁（原样）
│   ├── 10_sukisu-4.14-susfs.patch          SukiSU 侧 4.14 适配（本次，含 SUSFS 修复）
│   ├── camellian-integration.patch         早期交接骨架：仅 KSU 接入，不含 SUSFS 本体
│   └── sukisu-integration.patch            早期交接骨架：SukiSU 4.14 兼容（被 10_ 覆盖）
└── scripts/
    ├── integrate-susfs.py           一键接入（幂等）
    ├── build-verify.sh              编译验证命令
    └── verify-symbols.sh            产物符号校验
```

> 两处 `*-integration.patch` 是并行会话产出的交接骨架，只解决「KSU 能在 4.14 编译」；
> **真正让 SUSFS 可用的是 `50_` + `10_` + `kernel/` 文件**。两组不要叠加应用，避免重复。

## 使用

```sh
# 1. 准备内核源码（与设备固件同源）
git clone --depth 1 -b camellian-t-oss \
  https://github.com/MiCode/Xiaomi_Kernel_OpenSource.git camellian-kernel

# 2. 接入（会应用补丁、装 ABI 层、接 SukiSU 手动挂钩、补 setresuid）
python3 tools/camellian-susfs/scripts/integrate-susfs.py /path/to/camellian-kernel

# 3. 打开配置
cat tools/camellian-susfs/config/susfs-4.14-config.txt >> <defconfig 或 .config>
```

## 能力边界（必须如实告知用户）

| 功能 | 状态 | 说明 |
| --- | --- | --- |
| sus_path（隐藏路径） | 可用 | 依赖应用进程标记；由 setresuid 钩子触发 |
| sus_mount（隐藏挂载） | 可用 | v1.5.5 的 mnt_id 伪造 + 隐藏 sus 挂载 |
| sus_kstat（伪造 stat） | 可用 | |
| uname / cmdline 伪装 | 可用 | |
| open_redirect | 可用 | |
| enable_log | 可用 | |
| hide ksu/susfs symbols | 可用 | 需要 CONFIG_KALLSYMS_ALL |
| sus_path_loop | **不支持** | ABI 明确返回 `-EOPNOTSUPP`，管理器会显示命令失败；不再静默退化成一次性添加 |
| sus_map | **不支持** | 无过滤 `/proc/pid/maps` 的钩子；ABI 返回 `-EOPNOTSUPP`，且不再出现在启用特性列表 |
| avc_log_spoofing | **不支持** | 无 security/selinux 侧钩子；ABI 返回 `-EOPNOTSUPP` |
| priority_uid_filter | **不支持** | 没有实现 getpriority 过滤；ABI 返回 `-EOPNOTSUPP` |
| try_umount | 未启用 | v1.5.5 的可选特性，需要额外 KSU 支撑 |
| KPM | 不可用 | 与 SUSFS 无关，4.14 缺 KernelPatch 钩子 |

> **关于「不支持」的语义**：这四条命令仍保留入口（内核 ABI 需要符号存在），但一进来就写入
> `-EOPNOTSUPP`，不做任何实际动作。用户态 `ksud` 会把非 0 / 非 126 的 `err` 当成失败上报，
> 所以管理器里这些操作会明确报错，而不是显示成功。
> `sus_map` 同时从 `susfs_get_enabled_features()` 的返回里移除，特性页不会再把它标为启用。
> 这是刻意的取舍：宁可功能少，也不让用户误以为隐藏已经生效。

## 验证状态

- 编译验证（2026-11-08）：x86_64 Linux 沙箱，AOSP clang-r383902 完整编译通过。
- 可刷镜像（2026-11-08）：用**出厂 ikconfig + LTO/CFI** 编译，装回原厂内存盘/DTB，10/10 结构校验通过。
  - `dist/boot-sukisu-susfs-lto-stockdtb.img` 67,108,864 字节
  - MD5 `322fd6381c8b6d546b0298fbd1b7736f`
  - SHA256 `c3c2c6d75382ed06ebcbbd3dd9bbbf8dc234410860fa47de99b122ec98a44760`
  - 内核 `4.14.186-perf-gf4e416aea-dirty`，52 个 `susfs_` 符号
- 真机验证：**未刷入**。刷机需要用户明确授权，且会写 `boot_b`。
- 本包不改变启动镜像打包流程；`bootimg.py` 与既有 `pack_boot.py` 的布局假设一致。

## 来源与许可

- `susfs4ksu`（`kernel-4.14` 分支，v1.5.5）：GPL-2.0，作者 simonpunk。
- v2.3.0 ABI 适配思路参考 `yao140514/oppoa2m-sukisu-susfs`（GPL-2.0 内核代码）。
- 本目录中的改动同样按 GPL-2.0 发布。
