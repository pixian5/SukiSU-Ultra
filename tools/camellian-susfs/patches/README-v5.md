# v5：open 层钩子与 execveat 去重

对应镜像：`boot-sukisu-susfs-allowlist-fix-v5.img`（VERSION 0.0.12）

## 为什么改

`head -c 4 /system/bin/su` 报 ENOENT，而 `ls -l` / `stat` 显示 328384 字节。
原因是三层钩子覆盖不均：

| 命令 | 命中钩子 | 行为 |
|---|---|---|
| `ls` / `stat` | `ksu_handle_stat`（`fs/stat.c`） | 文件名被就地改写成 `/system/bin/sh`，显示的是 sh 的大小 |
| `head` / `cat` | 无 | `do_sys_open()` 里没有 KSU 钩子，按真实路径查找 → ENOENT |
| `su -c` | `ksu_handle_execveat`（`fs/exec.c`） | 改写执行目标 |

系统本身不含真实 su（SukiSU 的设计前提），所以 open 必然 ENOENT。

## 改了什么

1. **`fs/open.c`**：`do_sys_open()` 里在 `getname()` 之前调用 `ksu_handle_open()`，
   并加对应 extern 声明。
2. **`kernel/feature/sucompat.c`**：新增 `ksu_handle_open()`。
   - `escalate = false`，只改路径不提权；
   - **只处理只读打开**：带 `O_WRONLY|O_RDWR|O_CREAT|O_TRUNC` 的直接放行，
     否则会把写操作重定向到 `/system/bin/sh` 并损坏系统 shell。
3. **`fs/exec.c`**：原文件在 `do_execveat_common()` 内有**两次** `ksu_handle_execveat()`
   调用、前面还有**两个**重复 extern 块。钩子会就地改写 `filename`，重复调用
   会拿已改写的结果再跑一遍匹配逻辑，因此合并为各一次。

## 补丁文件

| 文件 | 作用域 | 基线 |
|---|---|---|
| `40_sucompat-open-hook.patch` | SukiSU 树 `kernel/feature/sucompat.c` | 已应用 `30_sucompat-ksud-path-candidates.patch` 之后 |
| `41_kernel-open-hook.patch` | 内核树 `fs/open.c`、`fs/exec.c` | 内核 HEAD（v1~v4 改动已含在基线外） |

两个补丁都已用 `patch --dry-run` 验证可干净应用。

## 不在补丁里的一处

`fs/susfs.c` 的白名单加固（路径规范化、拒绝 `..`/超长、目录黑名单）直接改在
`tools/camellian-susfs/kernel/fs/susfs.c`，由 `integrate-susfs.py` 安装，
不走 patch。改动内容见该文件 100–194 行。

## 验证

- 编译 rc=0，0 error；
- 反汇编确认顺序正确：
  ```
  ffffff800842b6dc: bl #12886368 <ksu_handle_open>
  ffffff800842b6ec: bl #73212 <getname_flags>
  ```
- 打包 12/12 结构校验通过；
- 白名单逻辑 19 项单元测试全通过（含 `/system/bin/sh`、`/data/adb/modules/*` 不被误拦）。
