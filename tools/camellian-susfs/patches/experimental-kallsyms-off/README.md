# 实验变体源码快照（**不是主线，不要用来刷机**）

这一目录是 2026-11-08 从本机连上的云电脑原样导出的源码改动，用于回答一个具体问题：**关掉 `CONFIG_KALLSYMS_ALL` 之后这颗 4.14 内核还能不能完整编译**。

期间另一台并行工作的云电脑先发布了正式的 v0.0.6（在 SuSFS 接口层把四条空壳命令写回 `err=-95`），那个做法比本目录里「在命令分发处直接返回错误码」更贴合用户态协议。因此：

- **主线**以发布页 `camellian-susfs-v0.0.6` 与仓库 `tools/camellian-susfs/kernel/fs/susfs_abi.c` 为准；
- **本目录只作存档**，其中 `camellian-tracked.patch`（厂商内核树 28 个文件的改动）与主线通用，其余内容仅对应实验变体；
- 本目录里 `kernel/fs/` 下的两个文件是实验变体版本，**不要复制回 `tools/camellian-susfs/kernel/`**，否则会覆盖主线正确的接口层修复。

## 目录内容

| 文件 | 作用 |
| --- | --- |
| `camellian-tracked.patch` | 厂商内核树里 **28 个已跟踪文件**的改动（挂钩点、`kernel/reboot.c` 的授权通道、`kernel/kallsyms.c` 的符号过滤等） |
| `sukisu.patch` | SukiSU 模块树的改动（4.14 兼容、默认应用配置回退、**四条命令改为返回「不支持」**） |
| `build.config` | 编译时的完整 `.config` 快照（量产 LTO/CFI 保留，`CONFIG_KALLSYMS_ALL=n`，`CONFIG_MIHW=y`，`CONFIG_MILLET=n`） |
| `../../kernel/` | 厂商内核树里 **新增的文件**：`fs/susfs.c`、`fs/susfs_abi.c`、`include/linux/susfs.h`、`include/linux/susfs_def.h`、`arch/arm64/boot/dts/camellian/cust.dtsi` |

> 为什么补丁里没有那几个 SuSFS 文件：它们是新增文件，导出时内核树的索引被编译进程占用，无法生成含新增文件的单一补丁。所以这里用「已跟踪文件补丁 + 新增文件完整快照」的组合，效果等价且更好审读。

## 复现步骤

```sh
# 1. 准备两棵公开源码树（分支要与设备固件一致）
git clone --depth 1 -b camellian-t-oss \
  https://github.com/MiCode/Xiaomi_Kernel_OpenSource.git camellian-kernel
git clone --depth 1 -b builtin \
  https://github.com/SukiSU-Ultra/SukiSU-Ultra.git SukiSU-Ultra

# 2. 内核树：先打已跟踪文件补丁，再复制新增文件
cd camellian-kernel
git apply /path/to/tools/camellian-susfs/patches/v0.0.6/camellian-tracked.patch
cp -R /path/to/tools/camellian-susfs/kernel/. ./

# 3. SukiSU 树：打补丁；内核树通过软链接引用它
cd ../SukiSU-Ultra
git apply /path/to/tools/camellian-susfs/patches/v0.0.6/sukisu.patch
ln -s /abs/path/to/SukiSU-Ultra/kernel ../camellian-kernel/drivers/kernelsu

# 4. 编译（AOSP clang r383902，独立构建目录）
cd ../camellian-kernel
cp /path/to/tools/camellian-susfs/patches/v0.0.6/build.config out/.config
export PATH=/path/to/aosp/clang-r383902/bin:$PATH
make O=out -j4 ARCH=arm64 CC=clang CLANG_TRIPLE=aarch64-linux-gnu- \
  CROSS_COMPILE=aarch64-linux-gnu- LD=ld.lld NM=llvm-nm \
  OBJCOPY=llvm-objcopy AR=llvm-ar olddefconfig
make O=out -j4 ARCH=arm64 CC=clang CLANG_TRIPLE=aarch64-linux-gnu- \
  CROSS_COMPILE=aarch64-linux-gnu- LD=ld.lld NM=llvm-nm \
  OBJCOPY=llvm-objcopy AR=llvm-ar

# 5. 打包：用原厂 V14.0.4.0.TKSEUXM 的 boot.img 作底，只换内核
python3 tools/camellian/scripts/pack_boot.py dist/boot-sukisu-susfs-lto-stockdtb.img
```

原厂底包 MD5 必须是 `f8e4f42a4538b03c519bb70921d88bcc`；打包脚本会保留原厂内存盘、设备树与校验区段，并重定位 AVB 尾部。**vbmeta 内哈希无法用厂商私钥重签**，解锁启动锁下不致命，重新上锁会无法启动。

## 实验变体相对主线 v0.0.6 的实际改动

1. `kernel/supercall/dispatch.c`：`sus_path_loop`、`sus_map`、`priority_uid_filter`、`avc_log_spoofing` 四条命令改为 `return -EOPNOTSUPP`，并各打一次内核警告；管理器不会再看到「成功/支持」。
2. `fs/susfs_abi.c`：`susfs_get_enabled_features` 不再汇报 `CONFIG_KSU_SUSFS_SUS_MAP`。
3. `fs/susfs.c`：开机日志加 `susfs: camellian build 0.0.6, honest feature set`，便于核对刷进去的到底是哪一版。
4. `build.config`：`CONFIG_KALLSYMS_ALL` 由 `y` 改为 `n`。符号隐藏是在 `/proc/kallsyms` 读路径按名字过滤，不依赖这个开关；关掉可减少可被检测的暴露面。**这一项尚未真机验证**，若开机异常优先改回 `=y` 重编。

有真实实现的命令不受影响：`sus_path`、`sus_kstat`、`uname`、`cmdline` 伪装、`open_redirect` 等仍在 v1.5.5 的 4.14 核心里。

## 边界

- 这一版**从未在真机上验证**；编译通过 + 结构校验合格不等于能开机或隐藏有效。
- 刷机需要用户明确说「刷机」；回退件是 `backup/camellian/boot_b-before.img`。
- 另一条技术路线（v0.0.5，vanilla 1.4.2 核心 + 自写兼容层）的源码**仍不在仓库里**，本固化包不包含它，也不要把两路线混用。
