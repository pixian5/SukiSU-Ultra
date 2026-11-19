# 要求对方修复「su 被 sus_path 隐藏」的提示词

- 时间：2026-11-20 01:10（GMT+8）
- 现象：v3 上 Shell 授权正常（列表 ROOT），但 `/system/bin/su` 的 `ls`/`stat` 正常、`open`/`exec` 返回 ENOENT
- 结论：SuSFS 的 `sus_path` 把 SukiSU 自己的提权入口隐藏了，所有 su 提权失败
- 来源判断：`sus_path` 是用户态配置（`ksud` 的 `susfs_config`，`KEY_SUS_PATHS`，默认空），说明有配置或预设把 `/system/bin/su` 加了进去

---

## 提示词（可直接复制）

```
v3 刷入后，Shell 在超级用户列表里是 ROOT（授权正常），但 /system/bin/su 打不开：

  ls -l /system/bin/su        → 正常，328384 字节
  stat /system/bin/su         → regular file，正常
  head -c 4 /system/bin/su    → No such file or directory
  su -c id                    → No such file or directory

这是 SuSFS 的 sus_path 隐藏特征：目录遍历不拦、路径打开返回 ENOENT。
结果是所有 APP 和 adb shell 都无法提权，root 实际不可用。

SuSFS 的 sus_path 是用户态配置（ksud 的 susfs_config，KEY_SUS_PATHS，默认空），
不是内核默认值。所以是有配置或预设把 /system/bin/su 加进了隐藏列表。

请修：

1. 检查 ksud 的 susfs_config 默认值、初始化逻辑，以及管理器侧的 SuSFS 预设，
   找出是谁把 /system/bin/su（以及 /system/xbin/su、/sbin/su）加进 sus_path 的。
2. 在应用 sus_path 之前加白名单，强制排除 SukiSU 自己的提权路径：
       /system/bin/su
       /system/xbin/su
       /sbin/su
       /data/adb/ksu/bin/su
   这些路径永远不能隐藏，否则所有 APP 的 root 都会失效。
3. 如果列表来自用户配置，提供管理器设置项或迁移逻辑，默认不包含上述路径。
4. 如果只改用户态（ksud/管理器），不需要重编内核；给出新的 ksud/管理器版本与 SHA256。
   如果确实要改内核，再按原流程重编 v4。
5. 验证判据（写进说明）：
   - adb shell su -c id 返回 uid=0；
   - ls /system/bin/su 与 head -c 4 /system/bin/su 都正常；
   - 管理器里给一个 APP 授权后，APP 内调用 su 能成功。
6. 不要刷机、不要连接手机、不要发布主线 Release。
```

---

## 补充判断

- 如果对方检查后发现 `sus_path` 列表里根本没有 `/system/bin/su`，那问题就不在 sus_path，而在 SuSFS 的 `sus_map`/`open_redirect` 或其他路径钩子；此时要求它提供具体的隐藏规则来源，不要继续猜。
- 无论哪种情况，**验收必须以 `su -c id` 能返回 uid=0 为准**，不能只看管理器列表。

---

## 关联文档

- [v3 的 su 被 SuSFS 隐藏](./20261120-0105-v3的su被SuSFS隐藏-Claude-Opus-6.md)
- [v3 刷入成功：WiFi 恢复、SuSFS 生效](./20261120-0100-v3刷入成功与WiFi恢复-Claude-Opus-6.md)
