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

## 临时 root 的租约（「授权自动消失」的坑）

- 管理器保存授权时会调 `ksud temporary-root apply <manager> keep|permanent|<秒数> <json>`；只有 `permanent` 才是永久授权，传秒数就是限时租约。
- 默认时长 **10 分钟**（`TemporaryRoot.defaultMinutes`，可改 5/10/30/60 或自定义，上限 7 天）；租约同时绑定本次开机的标识，**重启一律失效**，即使没设截止时间。
- `ksud` 以 `temporary-root watch` 常驻，每秒扫描，过期就撤销；应用详情页每秒读一次内核 profile，发现 `allowSu` 变回 `false` 就把开关自动关掉。
- 因此「授权成功后过一会自己消失、下次还要重新打开」通常是临时租约到期，**不是持久化失败或内核 bug**。
- 改永久授权：先在应用详情页关掉「临时 root」开关并保存一次（清掉旧租约），再打开 root 开关保存；用 `ksud temporary-root status <uid>` 验证，返回 `permanent` / `none` 才对。
- 排查辅助：`adb shell ps -A` 里 `ksud` 带 `temporary-root watch` 参数，只说明监视器常驻，不代表当前一定存在租约。

## 永久授权丢失的三条路径

- **异步落盘失败**：`ksu_set_app_profile` 只改内存；`do_set_app_profile` 成功后调 `ksu_persistent_allow_list`，它把写文件任务挂在 PID 1 上，`task_work_add` 失败或 `filp_open` 失败都只打日志、不重试。特征是**重启后丢**。
- **按安装列表误删**：`track_throne`（开机完成、应用安装/卸载/更新时触发）读 `/data/system/packages.list`，用「uid 取模相等 + 包名逐字符相等」校验，不匹配就删除并立即写盘。应用双开/工作资料、列表读取不完整时会误删。特征是**不重启也可能丢，通常只丢一个应用**。
- **授权文件写坏**：`do_persistent_allow_list` 用 `O_TRUNC` 直接覆盖，没有临时文件 + 原子替换；写一半失败后 magic/版本校验不通过，启动时整份放弃。特征是**重启后所有授权一起丢**。
- 判据：只丢一个 → 清理机制；重启后全丢 → 落盘失败或文件损坏。`/data/adb/ksu/.allowlist` 普通 shell 不可读，文件级证据需要 root。
- 不要只凭 `ksud` 带 `temporary-root watch` 参数就判断是临时授权：那是开机无条件启动的监视器。

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
