# SuSFS 可刷镜像的修改建议（给下一个 AI）

> 时间：2026-11-08 03:35（GMT+8）
> 对象：`camellian-susfs-v0.0.4` 镜像（`boot-sukisu-susfs-lto-stockdtb.img`，MD5 `322fd6381c8b6d546b0298fbd1b7736f`）
> 结论：**结构合格，可以试刷**；但有 3 个「假支持」特性和 2 个配置取舍需要处理，否则隐藏效果会被高估。

---

## 0. 先说做得对的地方

- 用原厂 `ikconfig` 而不是开源 defconfig，方向正确
- LTO/THINLTO/CFI 保持量产配置
- 结构 10/10 校验、52 个 `susfs_` 符号、版本串 `v2.3.0`
- 已经修掉两个会直接导致开机崩溃的问题：
  - `sucompat.c` 的 5.x 钩子限定 `>= 5.0`（4.14 把用户路径当 `struct filename *` 解引用会 data abort）
  - `kernel/sys.c` 的 `setresuid` 补上 `ksu_handle_setresuid()`
- 有 Release 和 `SHA256SUMS.txt`

---

## 1. 必须修：三个特性是「假支持」

### 1.1 `sus_map`、`avc_log_spoofing`、`priority_uid_filter`

**现状**：ABI 层注册了这三条命令，但底层 v1.5.5 核心没有对应实现。管理器会显示「支持」，用户会以为它们生效。

**为什么是问题**：这是**误导性最强的一类缺陷**——用户看到「支持」就去测 Momo，结果没变化，会误判成「SuSFS 没用」，而不是「这三个功能没实现」。

**建议（二选一，优先 A）**：

**A. 诚实标注（工作量小，先做）**
在 ABI 层对这三条命令返回 `-EOPNOTSUPP`（或对应错误码），让管理器显示「不支持」。同时在 `tools/camellian-susfs/README.md` 的「已知限制」里写清楚。

**B. 真正补钩子（工作量中等）**
- `sus_map`：在 `mm/mmap.c` 的 `mmap_region()` 或 `do_mmap()` 里挂钩，对标记过的 inode 隐藏 `/proc/self/maps` 条目。v1.5.5 的 `fs/susfs.c` 里可能有 `sus_map` 的雏形，先查再决定。
- `avc_log_spoofing`：在 `security/selinux/avc.c` 的 `avc_audit()` 或 `avc_denied()` 路径挂钩，过滤 ksu/susfs 相关域名的日志。
- `priority_uid_filter`：在 `sucompat.c` 的 `ksu_handle_execveat_*` 或 `ksu_handle_setresuid` 里按 uid 优先级过滤。

**验收**：`ksud susfs status` 或管理器特性页里，这三项显示为「支持」时，必须真的能观察到效果（比如 `sus_map` 隐藏 maps 条目、`avc_log_spoofing` 屏蔽日志）。做不到就按 A 标「不支持」。

### 1.2 `sus_path_loop` 退化成一次性添加

**现状**：ABI 有命令，但底层只支持一次性 `sus_path`。

**建议**：同上，要么补循环机制，要么在 ABI 层明确返回「不支持」，不要静默降级。

---

## 2. 应该修：两个配置取舍

### 2.1 `CONFIG_KALLSYMS_ALL=y`

**现状**：为了让 `CONFIG_KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS` 生效而打开。

**问题**：它把**全部内核符号**暴露给 root，本身就是一个可被检测的特征，而且内核变大、首次开机变慢。

**建议**：
1. 先验证 `KALLSYMS_ALL=n` 时符号隐藏是否仍然有效。如果无效，看 `hide_ksu_susfs_symbols` 的实现是否只依赖 `kallsyms` 里存在 `ksu_`/`susfs_` 符号（`KALLSYMS` 就够，不一定要 `ALL`）。
2. 如果必须 `KALLSYMS_ALL`，考虑在 `kallsyms_show_value()` 或 `/proc/kallsyms` 的读路径上加过滤，只对非特权进程隐藏，而不是全量暴露。
3. 如果都不行，保留 `KALLSYMS_ALL=y`，但在 README 里写清楚「这是一项可被检测的取舍」。

**验收**：`KALLSYMS_ALL=n` 时 `ksu_susfs` 的符号隐藏仍然工作；否则明确记录取舍。

### 2.2 `CONFIG_MIHW=n`

**现状**：开源树缺 `vendor/xiaomi/kernel_modules/mihw`，所以关掉。

**问题**：小米的 `mihw`/`millet` 可能影响游戏加速、网络优化、部分电源/传感器策略。基本开机大概率不受影响，但属于未知面。

**建议**：
1. 先从原厂 `boot.img` 的 ramdisk 或 `vendor_boot` 里找 `mihw.ko`（`bootimg.py unpack` 已经能解包，直接 `find` 一下）。
2. 如果能提取到预编译模块，作为 `vendor_dlkm` 或 modules 加载；如果提取不到，保持关闭。
3. 在 README 的「已知限制」里写：「`mihw` 关闭，若真机出现小米专有功能异常，优先怀疑此项」。

**验收**：开机后检查 `dmesg` 有没有相关报错；如果有，记录具体现象。

---

## 3. 收尾项

### 3.1 版本号不一致

`tools/camellian-susfs/VERSION` 写 `0.0.5`，Release tag 是 `v0.0.4`。统一到一个版本，避免用户对不上。

### 3.2 AVB 哈希未重签

无法解决（没有厂商私钥），保持现状，在 README 写清楚：「解锁 bootloader 下校验错误不致命；重新上锁会无法启动」。

### 3.3 真机验证（由本机执行，不要自己刷）

提供一份**可判定的验证清单**，由持有手机的机器执行：

1. 能开机、无重启循环（首次可能慢，超过 3 分钟无反应视为失败）
2. 管理器显示「工作中」
3. 进程列表有 `com.sukisu.ultra:root:0`
4. `ksud susfs status` 报 `v2.3.0 / NON-GKI`
5. 管理器 SuSFS 页能读到特性列表
6. Momo 复测：记录「找到 Magisk / Zygisk / 代码注入」哪几项变化
7. **不要**用 `adb shell su` 判断成败（调试模式关闭时本来不可用）

---

## 4. 建议的分阶段计划

**阶段 1（今天就能做）**
- 把三个「假支持」特性改成明确「不支持」（1.1 的 A 方案）
- 统一版本号
- 出一版新镜像（只改 ABI 返回值和版本号，不改内核逻辑）

**阶段 2（验证后）**
- 真机验证阶段 1 的镜像
- 根据结果决定是否补 `sus_map` 等钩子

**阶段 3（可选）**
- `KALLSYMS_ALL` 方案验证
- `mihw` 模块提取
- `sus_path_loop` 循环实现

**不要**在阶段 1 就同时改内核钩子和配置——变量太多，出问题无法定位。

---

## 5. 给下一个 AI 的直接指令

> 按 `docs/20261108-0335-SuSFS镜像修改建议-Claude-Opus-6.md` 执行。
> 先做「阶段 1」：把 `sus_map`、`avc_log_spoofing`、`priority_uid_filter`、`sus_path_loop` 在 ABI 层改成明确的「不支持」返回，统一 `VERSION`，重新编译并发布新 Release。
> 不要改内核逻辑，不要动 `KALLSYMS_ALL` 和 `MIHW`。
> 产物命名沿用 `boot-sukisu-susfs-lto-stockdtb.img`，发布到 `pixian5/SukiSU-Ultra` 的 Release，并更新 `tools/camellian-susfs/README.md` 的「已知限制」。
> 刷机由持有手机的机器负责，你只负责编译和发布。

---

## 关联文档

- [SUSFS 可刷镜像构建与产物](./20261108-0250-SUSFS可刷镜像构建与产物-DeepSeek-V4.1-Flash.md)
- [SUSFS v2.3.0 移植与编译验证](./20261108-0210-SUSFS-v2.3.0移植与编译验证-DeepSeek-V4.1-Flash.md)
- [SukiSU 用户态链路修复与授权验证](./20261107-2230-SukiSU用户态链路修复与授权验证-Claude-Opus-6.md)
