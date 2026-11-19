# v5 刷入后 su 仍未恢复：execve 钩子没有触发

- 时间：2026-11-20 03:45（GMT+8）
- 镜像：v5（`#7 SMP PREEMPT Fri Nov 20 02:18:21`）

## 实测

```
uname -v                 → #7 SMP PREEMPT Fri Nov 20 02:18:21 CST 2026
head -c 4 /system/bin/su → 7f 45 4c 46（open 钩子生效，读到 ELF）
ls -l /system/bin/su     → 328384，与 /system/bin/sh 完全一致
su -c id                 → /system/bin/su: No such file or directory
logcat 中的 su->ksud / su->sh 日志 → 一条都没有
```

WiFi、相机、指纹服务均正常。

## 判断

`head` 能读说明 open 层修复生效；但 `su` 执行失败且没有任何 sucompat 日志，说明 `ksu_handle_execveat` 没有被有效分派到 sucompat，`su` 没有被改写，真实 su 不存在 → ENOENT。

## 对方后续查明

`KSU_COMPAT_USE_STATIC_KEY` 开启时，zygote 分支用 `static_branch_disable(&is_first_zygote)` 而不调用 `stop_execve_hook()`，`ksu_execveat_hook` 永远为 true，分派永远走 ksud 钩子，sucompat 从未执行。v6 修正了分派跳转（见 v6 验证报告）。

## 关联文档

- [v6 验证通过：分派跳转已修正](./20261120-0400-v6验证通过-分派跳转已修正-Claude-Opus-6.md)
