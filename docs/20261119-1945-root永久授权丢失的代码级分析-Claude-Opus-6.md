# 永久 root 授权为什么会丢：三条代码级路径

- 时间：2026-11-19 19:45（GMT+8）
- 设备：Redmi Note 10 5G（M2103K19C / camellia），Android 13，自编内核 `#11`，开机 23 小时
- 用户反馈：**「我明明给授权的是永久的 root」**，并要求我自己验证
- 本次只读：没改配置、没动模块、没重启手机。`/data/adb` 对普通 shell 不可读，所以文件级证据需要一次 root 授权；下面先把代码链路和判据讲清楚。

---

## 一、先更正上一轮的结论

上一轮我说「授权自动消失是临时 root 租约到期」，**证据不充分**：

- `ksud` 带 `temporary-root watch` 启动，是开机时**无条件**启动的监视器（`init_event.rs` 里 `on_post_fs_data` 直接调 `start()`），**不代表当前存在租约**；
- 管理器的开关保存走的是 `updateLease = true`、`seconds = null`，即 `mode = permanent`，`apply()` 里会**主动清掉该 uid 的旧租约**（`if (!p.allow_su || mode == "permanent") { leases.retain(uid != curr_uid); save(); }`）。

所以「永久授权被旧租约撤销」这条路径基本可以排除。真正需要查的是下面三条。

---

## 二、永久授权的完整写入链路

1. 管理器打开 root 开关 → `TemporaryRoot.saveProfile(profile, expectedRoot=true, updateLease=true, seconds=null)`；
2. 拼出命令：`/data/adb/ksud temporary-root apply <管理器 uid> permanent true <profile json>`；
3. `ksud` 校验身份后，通过 `ksuctl(KSU_IOCTL_SET_APP_PROFILE)` 写内核；
4. 内核 `ksu_set_app_profile()` **只改内存里的哈希表**；
5. 回到 `do_set_app_profile()`，成功后调用 `ksu_persistent_allow_list()`；
6. 落盘函数把「写文件」这件事作为 **task_work 挂到 PID 1（init）**，等 init 下次回到用户态才真正执行；
7. 真正的写入在 `do_persistent_allow_list()`：`filp_open("/data/adb/ksu/.allowlist", O_WRONLY|O_CREAT|O_TRUNC, 0644)`，写入 magic、版本号、然后逐条写授权。

---

## 三、三条会让永久授权消失的路径

### 路径 A：异步落盘失败，没有重试

`ksu_persistent_allow_list()` 只做一件事：`task_work_add(init, cb, TWA_RESUME)`。

- 如果 `task_work_add` 失败，只打印 `save_allow_list add task_work failed`，**内存里的授权不回滚，也不重试**；
- 如果 PID 1 长时间不回到用户态（高负载、IO 卡住），写盘被无限期推迟；
- 如果 `filp_open` 失败（路径被隐藏、权限变化、磁盘问题），只打印 `save_allow_list create file failed`，同样不重试。

结果：**内存里有、磁盘上没有**。这台机器在跑，应用能拿到 root；一旦重启，`ksu_load_allow_list()` 读到的是旧文件，授权就没了。这条路径的特征是「**重启后丢**」。

### 路径 B：内核按已安装列表清理授权（prune）

`track_throne()` 会在几个时机执行：开机完成（`on_boot_completed` → `track_throne(true)`）、应用安装/卸载/更新（`pkg_observer` → `track_throne(false)`）、管理器变化。

它读 `/data/system/packages.list`，对每条授权调 `is_uid_exist()`：

```c
np->uid == uid % PER_USER_RANGE && strncmp(np->package, package, KSU_MAX_PACKAGE_NAME) == 0
```

只有「**uid 取模后相等 且 包名逐字符相等**」才保留，否则**直接从内核表删除，并立即写盘**（`ksu_prune_allowlist` 里 `modified = true` → `ksu_persistent_allow_list()`）。

可能误删的情况：

- 应用在**应用双开 / 工作资料 / 隐私空间**里（uid 带用户前缀，或包名带后缀）；
- `/data/system/packages.list` 正在更新、读取不完整（高负载、IO 压力）；
- 授权记录的 `key` 不是标准包名（管理器传的 `name` 字段异常）。

这条路径的特征是「**不重启也可能丢，而且通常只丢一个应用**」。

### 路径 C：授权文件被写坏，启动时整份放弃

`do_persistent_allow_list()` 用的是 `O_TRUNC` 直接覆盖原文件，**没有临时文件 + 原子替换**。如果写到一半失败（磁盘满、掉电、进程被杀），文件会变成半截：

- `ksu_load_allow_list()` 先校验 magic（`0x7f4b5355`）和版本号（必须是 2–4）；
- 任何一项不通过就 `goto exit`，**整份授权都不加载**，也没有备份可回退。

这条路径的特征是「**重启后所有授权一起丢**」。

---

## 四、不用你动手的判据

| 现象 | 指向 |
| --- | --- |
| 只有一个应用的授权消失，其他还在 | **路径 B**（prune 误删），多发于安装/更新应用之后 |
| 重启后所有授权都没了 | **路径 A**（没落盘）或 **路径 C**（文件写坏） |
| 不重启、只是过一会开关自己关 | 先看是不是真的存在临时租约（`ksud temporary-root status <uid>`），但按你说的「永久」，更可能是 B |

当前系统状态对这个判断有参考价值：负载 22、内存可用仅 1.1 GB、4 GB swap 用掉 2.3 GB、磁盘 88%——高负载和 IO 压力会同时放大 A（PID 1 写盘被推迟）和 C（写到一半失败）的风险。

---

## 五、需要改的代码（供后续修）

1. `do_persistent_allow_list` 改为「写临时文件 → `fsync` → `rename` 原子替换」，失败重试并保留上一份备份；
2. `ksu_persistent_allow_list` 对 `task_work_add` 失败做兜底（例如同步写一次或标记 dirty，下次开机先写）；
3. `ksu_prune_allowlist` 在读到的 `packages.list` 条目数明显少于上次（如少于一半）时**跳过本轮清理**，避免读不完整导致误删；
4. 管理器在授权被内核清理时给出可见提示，而不是静默把开关关掉。

---

## 六、边界与后续

- 本次只读：没有改任何配置、没有执行 `temporary-root` 命令、没有重启手机。
- `/data/adb/ksu/.allowlist` 对普通 shell 是 `Permission denied`，要拿文件级证据（文件是否存在、大小、修改时间、内容）需要一次 root 授权。你同意的话我用最小只读命令取一次，不改任何东西。
- 在此之前，上面的判据已经能区分三条路径，不需要你去管理器里反复开关验证。

---

## 关联文档

- [root 授权自动消失原因分析（上一轮，含本次更正说明）](./20261119-1915-root授权自动消失原因分析-Claude-Opus-6.md)
- [首次真机试刷与 SukiSU 接入验证](./20261107-1110-首次真机试刷与SukiSU接入验证-Claude-Opus-6.md)
