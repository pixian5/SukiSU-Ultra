# SukiSU 集成与用户态链路

## 挂钩模型

- 非 GKI / 4.14 使用 `builtin` 分支的**手动挂钩**，需要改厂商内核源码；`main` 分支是 kprobe 运行时注册，不需要改源码。两者不能混用。
- 4.14 集成至少需要 4 个文件系统钩子：`fs/exec.c`（execve）、`fs/open.c`（faccessat）、`fs/stat.c`（stat）、`fs/read_write.c`（vfs_read）。
- 还需要内核树 `kernel/reboot.c` 的 `ksu_handle_sys_reboot` 调用，见下。

## 授权链路三个关键点

1. **内核通道申请**：管理器注入的匿名 fd 带 exec 关闭标志，`ksud` 子进程继承不到；`ksud` 通过带魔数的 `reboot` 系统调用重新申请。缺这个钩子会报 `could not retrieve kernelsu driver fd`。
2. **默认 app profile**：读取不存在的 uid 配置时，官方 release 管理器期望返回默认 profile；返回 `-ENOENT` 会被当成失败，界面提示「更新 app profile 失败」并中止授权。
3. **管理器入口**：管理器「隐藏应用」会禁用自身 activity 别名，`am start` 报入口不存在；用同包覆盖重装 `adb install -r` 恢复。

以上三处修复已固化：
- `tools/camellian/patches/kernel-reboot-ksu-hook.patch`
- `tools/camellian/patches/sukisu-dispatch-app-profile-fallback.patch`
- `tools/camellian/scripts/integrate.py` 第 8、9 步
- 管理器入口问题属于使用禁忌，不是代码补丁。

## 身份与版本耦合

- 管理器 APK 的证书大小与 SHA-256 在编译内核时写死；换签名、伪装包名或内核/管理器版本错配，都会导致「管理器认不出 root」。
- 当前配套：管理器 `v4.3.0-r2`（41150），内核完整版本 `v4.3.0-r2-1cfa5734@builtin`，UAPI 版本 6。
- 用户态组件（`ksud`/`ksuinit`）用官方 release，不要自行拼版本。

## 能力边界（不要夸大）

- **SUSFS**：4.14 采用「v1.5.5 原生核心 + v2.3.0 ABI 翻译层」的混合实现，已完整编译通过（见 `tools/camellian-susfs/`）。可用：sus_path / sus_mount / sus_kstat / uname / cmdline / open_redirect / 日志与符号隐藏；不生效：sus_map / avc_log_spoofing / priority_uid_filter；sus_path_loop 退化为一次性添加。产物尚未真机验证。
- **KPM**：只补回开关与框架；4.14 缺 KernelPatch 钩子，探测符号 `__arm64_sys_truncate` 等不存在，结构性不可用。
- 判断标准是「真机可用 + 有证据」，不是「编译通过 / 开关能打开」。

## SUSFS 上 4.14 的四个必改点

1. `sucompat.c` 的 SUSFS 实现是 5.x 专用（按 `struct filename *` 取值），4.14 必须加 `LINUX_VERSION_CODE >= 5.0` 守卫，否则开机 1 秒内 data abort；
2. SUSFS 下 LSM `task_fix_setuid` 不注册，必须在 `SYSCALL_DEFINE3(setresuid)` 调用 `ksu_handle_setresuid()`，否则应用不关 seccomp、拿不到驱动 fd；
3. `strncpy_from_user_nofault()` 5.8 才有，需要兼容宏；
4. adb_root 在 SUSFS 下只有 `ksu_adb_root_handle_execveat(const char *, void ***)`，envp 要传 `&envp.ptr.native`。
