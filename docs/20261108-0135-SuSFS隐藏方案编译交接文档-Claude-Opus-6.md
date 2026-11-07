# SuSFS 隐藏方案：编译交接文档（给另一台云电脑上的 AI）

> **目的**：把「SukiSU 内核 + SuSFS 隐藏」的编译任务交接出去，让另一台云电脑上的 AI 能独立完成，产物传回本机刷入。
> **本机（Mac）只负责最后刷机**，不参与编译。
> 撰写时间：2026-11-08 01:35。

---

## 1. 任务目标

在小米 4.14 内核（机型 camellian）上，为 SukiSU-Ultra 启用 **SuSFS** 隐藏补丁，编出可刷入的启动镜像。

**产物要求**：
- 文件名 `boot-sukisu-susfs-lto-stockdtb.img`
- 67,108,864 字节（分区大小）
- 启动头版本 2、页大小 2048、内核版本串含 `gf4e416aea-dirty`
- 结构校验 12 项全过（用本项目的 `tools/camellian/pack_boot.py`）
- 刷入后能开机，SukiSU 管理器显示「工作中」，授权正常

---

## 2. 背景与现状（为什么做这个）

- 手机：Redmi Note 10 5G（`M2103K19C`），Android 13，`V14.0.4.0.TKSEUXM`，当前槽 **b**
- root：SukiSU-Ultra（builtin 内核集成），已能正常授权
- 已装：Zygisk Next 1.5.2、Shamiko 1.2.5（**黑名单模式**）、Vector
- **问题**：Momo 仍报「找到 Magisk / 找到 Zygisk / 代码注入 / 调试模式」
- **结论**：文件、属性、挂载层面已经清干净，剩下的是内核层特征，需要 SuSFS 隐藏

**当前手机运行的内核**（已验证可用，作为基线）：

```text
Linux version 4.14.186-perf-gf4e416aea-dirty (user@main)
#11 SMP PREEMPT Sat Nov 7 03:45:39 UTC 2026
```

对应镜像 MD5 `3f687ecbc07f24ac0ecfbea56ebe14f5`。

---

## 3. 环境要求

- Ubuntu 24.04 x86_64，**至少 8 GB 内存、20 GB 磁盘**
- clang 11.0.1（AOSP r383902）+ LLD 11.0.1
- 参考路径：`/workspace/aosp/clang-r383902`
- 依赖：`git`、`make`、`python3`、`unzip`、`curl`、`rclone`

---

## 4. 源码清单（全部公开，不需要任何 GitHub 凭证）

| 用途 | 仓库地址 | 分支 / tag |
|---|---|---|
| 内核源码 | `https://github.com/MiCode/Xiaomi_Kernel_OpenSource` | `camellian-t-oss` |
| SukiSU | `https://github.com/SukiSU-Ultra/SukiSU-Ultra` | `builtin` |
| SuSFS | `https://gitlab.com/simonpunk/susfs4ksu` | **`1.4.2-kernel-4.14`**（不要用 master 1.3.8） |
| 解包工具 | `https://github.com/ssut/payload-dumper-go` | 2.1.0 |
| 同步工具 | `https://downloads.rclone.org/rclone-current-linux-amd64.zip` | 最新 |

> **GitHub 凭证不需要**：以上仓库都是公开的，`git clone https://...` 直接可用。如果 clone 慢或被 TLS 中断，可以在能访问的机器上 clone 后打包，通过对象存储中转（见第 8 节）。

---

## 5. 操作步骤

### 5.1 获取源码

```bash
cd /workspace
git clone --depth 1 -b camellian-t-oss \
  https://github.com/MiCode/Xiaomi_Kernel_OpenSource.git camellian-kernel
git clone --depth 1 -b builtin \
  https://github.com/SukiSU-Ultra/SukiSU-Ultra.git SukiSU-Ultra
# SuSFS 必须用 4.14 的 tag，不能用 master
git clone --depth 1 --branch 1.4.2-kernel-4.14 \
  https://gitlab.com/simonpunk/susfs4ksu.git susfs4ksu
```

如果 GitLab 的 TLS 不稳定（本机云电脑经常 `gnutls_handshake() failed`），就在别的机器上 clone 后打包成 `tar.gz`，通过对象存储传过来。

### 5.2 应用 SukiSU 集成补丁

本仓库已导出两个补丁（在 `tools/camellian-susfs/patches/`）：

| 文件 | 作用 | MD5 |
| --- | --- | --- |
| `camellian-integration.patch` | 内核侧：挂钩点、Makefile/Kconfig、SuSFS 1.3.8 改动 | `865b32a04a055c971223cc3c94d0a1f6` |
| `sukisu-integration.patch` | SukiSU 侧：app profile fallback、preinit、CPU 伪装等 | `366b5d1983c2496e17991446db0d35bc` |

```bash
cd /workspace/camellian-kernel
git apply /path/to/camellian-integration.patch
cd /workspace/SukiSU-Ultra
git apply /path/to/sukisu-integration.patch
```

**重要**：`camellian-integration.patch` 是在「**已经打了 SuSFS 1.3.8**」的状态下导出的，所以它里面**混有 1.3.8 的改动**。下一步必须把 1.3.8 回滚掉，再换 1.4.2。

### 5.3 回滚 1.3.8 的 SuSFS 改动

```bash
cd /workspace/camellian-kernel
# 只反向应用 SuSFS 1.3.8 的 hunk，不会动 SukiSU 的集成挂钩
patch -p1 -R < /workspace/susfs4ksu-master/kernel_patches/50_add_susfs_in_kernel-4.14.patch
rm -f include/linux/susfs.h fs/susfs.c include/linux/susfs_def.h
```

> 如果 `patch -R` 有失败，说明补丁状态不一致，请逐个文件核对：`fs/Makefile`、`fs/internal.h`、`fs/namei.c`、`fs/namespace.c`、`fs/open.c`、`fs/proc/*`、`fs/readdir.c`、`fs/stat.c`、`kernel/sys.c`、`mm/shmem.c`。

### 5.4 应用 SuSFS 1.4.2（4.14）

按上游 README 的方式：

```bash
cp /workspace/susfs4ksu/kernel_patches/include/linux/susfs.h \
   /workspace/camellian-kernel/include/linux/
cp /workspace/susfs4ksu/kernel_patches/fs/susfs.c \
   /workspace/camellian-kernel/fs/
cd /workspace/camellian-kernel
patch -p1 < /workspace/susfs4ksu/kernel_patches/50_add_susfs_in_kernel-4.14.patch
```

如果 1.4.2 里有 `susfs_def.h`，一并复制到 `include/linux/`；如果没有而这个头文件被引用，就创建一个最小版本：

```c
#ifndef KSU_SUSFS_DEF_H
#define KSU_SUSFS_DEF_H
#define SUSFS_VERSION "1.4.2"
#endif
```

同时确认 `include/linux/susfs.h` 里定义了 `SUSFS_VERSION`（`kernel/Makefile` 会读它打印版本）。

### 5.5 配置

```bash
cd /workspace/camellian-kernel
./scripts/config --file /workspace/out/.config -e KSU
./scripts/config --file /workspace/out/.config -e KSU_SUSFS
make O=/workspace/out ARCH=arm64 ... olddefconfig
```

必须确认以下开关（缺一不可）：

```
CONFIG_KSU=y
CONFIG_KSU_SUSFS=y
CONFIG_LTO_CLANG=y
CONFIG_CFI_CLANG=y
```

**不要**开 `CONFIG_KSU_DEBUG`（调试模式会让任何能连 adb 的人拿到 root）。

### 5.6 编译

```bash
export PATH=/workspace/aosp/clang-r383902/bin:$PATH
export LD_LIBRARY_PATH=/workspace/aosp/clang-r383902/lib64:$LD_LIBRARY_PATH
cd /workspace/camellian-kernel
make O=/workspace/out -j4 ARCH=arm64 \
  CC=clang CLANG_TRIPLE=aarch64-linux-gnu- \
  CROSS_COMPILE=aarch64-linux-gnu- \
  LD=ld.lld NM=llvm-nm OBJCOPY=llvm-objcopy AR=llvm-ar
```

LTO 链接很慢，一次可能超过 9 分钟。如果命令被超时中断，**直接重跑同一条命令**即可，增量编译会接着做。

### 5.7 打包

用本项目的打包脚本（会做 12 项结构校验）：

```bash
python3 /path/to/pack_boot.py /workspace/dist/boot-sukisu-susfs-lto-stockdtb.img
```

脚本需要的原厂镜像：`/workspace/rom/camellian_eea_global_images_V14.0.4.0.TKSEUXM_13.0/images/boot.img`
（MD5 `f8e4f42a4538b03c519bb70921d88bcc`）

---

## 6. 已知坑（都已经踩过，不要重复）

1. **SuSFS 1.3.8 与 SukiSU 不匹配**：缺 `SUSFS_MAGIC`、`susfs_add_sus_path_loop`、`susfs_start_sdcard_monitor_fn`、`susfs_parse_priority_app_strings`、`CMD_SUSFS_ADD_SUS_PATH_LOOP`、`CMD_SUSFS_SET_CMDLINE_OR_BOOTCONFIG`、`CMD_SUSFS_ADD_OPEN_REDIRECT`、`CMD_SUSFS_ADD_SUS_MAP` 等。**必须用 1.4.2**。
2. **`susfs_def.h` 在 1.3.8 里不存在**，但 SukiSU 的 `kernel/kernel_includes.h` 会 include 它，导致 `fatal error: 'linux/susfs_def.h' file not found`。
3. **`reboot` 系统调用必须挂钩子**：`ksud` 子进程通过带魔数的 `reboot` 申请内核通道，缺钩子会报 `could not retrieve kernelsu driver fd`。位置在 `kernel/reboot.c` 的 `SYSCALL_DEFINE4(reboot)` 开头。
4. **`do_get_app_profile` 对不存在的 uid 必须返回默认 profile**，返回 `-ENOENT` 会让管理器报「更新 app profile 失败」、授权开关打不开。位置在 `kernel/supercall/dispatch.c`。
5. **管理器「隐藏应用」会禁用 launcher alias**，导致管理器打不开，只能 `adb install -r` 覆盖重装恢复。不要开这个功能。
6. **ADB 通道会把 `0x0A` 改写成 `0x0D 0x0A`**：从手机读分区必须还原并校验长度，不能直接 `dd` 重定向。
7. **云电脑到 GitLab 的 TLS 不稳定**：本机云电脑多次 `gnutls_handshake() failed`，建议本机 clone 后打包走对象存储。

---

## 7. 验收标准

- 镜像 67,108,864 字节，MD5/SHA256 记录在案
- 打包脚本 12 项校验全 PASS
- 刷入后开机正常、槽位仍是 b
- SukiSU 管理器显示「工作中」，进程里有 `com.sukisu.ultra:root:0`
- `ksu_susfs` 命令可用（`/data/adb/ksu/bin/` 下）
- 关机再开机后仍然正常

---

## 8. 产物与传输

**传输方式**：S3 兼容对象存储，必须用 **rclone**（服务端校验 User-Agent）。

- endpoint：`https://s3.cstcloud.cn`
- bucket：`xbz`
- 前缀：`camellian/`
- 凭证：见随附的 `HANDOFF-CREDENTIALS.txt`（**不在 Git 仓库内**，请单独获取）

```bash
rclone --config /path/to/rclone.conf copyto \
  /workspace/dist/boot-sukisu-susfs-lto-stockdtb.img \
  cst:xbz/camellian/boot-sukisu-susfs-lto-stockdtb.img -v
```

**注意**：列目录时路径**必须带结尾斜杠**（`rclone ls cst:xbz/camellian/`），否则这个服务返回空列表。

上传完成后，本机（Mac）会下载并校验，然后刷入手机。**不要直接操作手机**，刷机由本机负责。

---

## 9. 与本项目的对接

- 产物命名：`boot-sukisu-susfs-lto-stockdtb.img`
- 上传到 `cst:xbz/camellian/`
- 把 MD5/SHA256 写回来（可以用 `rclone md5sum` 读取）
- 本机下载后校验、刷入、验证，并更新 `docs/` 与索引

---

## 关联文档

- [SukiSU 用户态链路修复与授权验证](./20261107-2230-SukiSU用户态链路修复与授权验证-Claude-Opus-6.md)
- [首次真机试刷与 SukiSU 接入验证](./20261107-1110-首次真机试刷与SukiSU接入验证-Claude-Opus-6.md)
- [红米 Note 10 5G 刷机执行方案与回退剧本](./20261107-0029-红米Note10-5G刷机执行方案与回退剧本-Claude-Opus-6.md)
- [启动镜像版本核对与回退件定位](./20261107-0905-启动镜像版本核对与回退件定位-Claude-Opus-6.md)
