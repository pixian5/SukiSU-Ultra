# v3 的 su 打不开：SuSFS 把 `/system/bin/su` 路径隐藏了

- 时间：2026-11-20 01:05（GMT+8）
- 设备：Redmi Note 10 5G，v3 内核（`#3`，SuSFS v2.3.0 Inline Hook）
- 用户反馈：「刚才明明给你手动授权了 Shell，你复核一下」

---

## 一、复核结论：授权是成功的

管理器「超级用户」列表显示 **12 个授权**，其中包括：

```
Shell | com.android.shell | ROOT
```

也就是说，用户刚给 Shell 的授权**已经生效**，Shell 的 `allow_su` 是开着的。

---

## 二、真正的问题：su 文件被「隐藏」

```
$ ls -l /system/bin/su
-rwxr-xr-x 1 root shell 328384 2009-01-01 08:00 /system/bin/su

$ readlink -f /system/bin/su
/system/bin/su

$ stat -c "%F %s %i" /system/bin/su
regular file 328384 531

$ head -c 4 /system/bin/su
head: /system/bin/su: No such file or directory

$ su -c id
/system/bin/sh: /system/bin/su: No such file or directory
```

**`ls`/`stat` 正常，`open`/`exec` 返回 ENOENT**。这正是 SuSFS 的 `sus_path` 隐藏机制的特征：

- 目录遍历（`getdents`）不拦截，所以 `ls` 能列出；
- 路径查找/打开（`openat`、`execve`）被拦截，返回 `-ENOENT`。

对比：final3（无 SuSFS）上 `su` 是正常的。

---

## 三、影响范围

所有通过 `/system/bin/su` 提权的调用都会失败：

- `adb shell su`；
- 普通 APP 内调用 `su`；
- 依赖 su 的脚本/模块。

也就是说，**v3 上所有应用的 root 实际不可用**，虽然管理器里显示已授权。

---

## 四、为什么会这样

SuSFS 的默认 `sus_path` 列表把 `/system/bin/su`（以及类似的 root 痕迹路径）纳入隐藏，这本来是为了隐藏 Magisk 的 su；但 SukiSU 自己的 su 也放在这个路径，于是**把自己的提权入口一起隐藏了**。

这是 SuSFS 与 SukiSU 在 4.14 上的集成缺陷，不是授权数据的问题。

---

## 五、处理方案

| 方案 | 做法 | 代价 |
| --- | --- | --- |
| **A. 刷回 final3** | `fastboot flash boot_b boot-sukisu-final3-lto-stockdtb.img` | WiFi、su、授权全部正常；放弃 SuSFS |
| **B. 让对方修 SuSFS 配置** | 从 `sus_path` 列表移除 `/system/bin/su`（或改 SukiSU 的 su 路径），重编 v4 | 需要对方重编、再刷一次 |
| **C. 现场改 sus_path** | 编辑 `/data/adb/ksu/sus_path.txt` 之类 | **行不通**：改文件需要 root，而 su 已经不可用，死循环 |

**建议**：先用 A 把手机恢复到「WiFi + su + 授权」都正常的状态；要 SuSFS 就让对方按 B 修，修好再刷。

---

## 六、边界

本次只读：`ls`/`stat`/`head`/`logcat`，没有改任何文件、没有刷机。

---

## 关联文档

- [v3 刷入成功：WiFi 恢复、SuSFS 生效](./20261120-0100-v3刷入成功与WiFi恢复-Claude-Opus-6.md)
- [v2 内核 WiFi 失效根因与回退](./20261120-0015-v2内核WiFi失效根因与回退-Claude-Opus-6.md)
