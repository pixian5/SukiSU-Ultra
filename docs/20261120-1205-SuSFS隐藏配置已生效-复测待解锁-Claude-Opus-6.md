# SuSFS 隐藏配置已生效，Ruru 复测被锁屏挡住

- 时间：2026-11-20 12:05（GMT+8）
- 设备：v6 内核（`#8`），SuSFS v2.3.0 Inline Hook

---

## 一、已完成的配置

用 `ksud susfs` 写入并立即应用：

```
sus_paths=/data/adb/ksu,/data/adb/lspd,/data/adb/modules,/data/adb/modules_update,/data/adb/post-fs-data.d,/data/adb/service.d
auto_start_enabled=1
execute_in_post_fs_data=1
```

- 6 条 `add-sus-path` 全部返回 OK（立即生效）；
- 持久化配置已写入，`auto_start_enabled=1` 保证下次开机自动应用；
- **没有**把 `/system/bin/su`、`/data/adb/ksud`、`/data/adb/ksu/bin/ksud` 加进隐藏列表，避免重演 v5 的提权入口被藏。

---

## 二、验证情况

| 检查 | 结果 |
| --- | --- |
| `ksud susfs config list` | 三项配置都在 |
| `add-sus-path` | 6/6 OK |
| root 身份读 `/data/adb/ksu` | 正常 |
| 非 root 读 `/data/adb/ksu` | Permission denied（受 `/data/adb` 0700 限制，不能单独证明 sus_path） |
| Ruru 复测 | **被锁屏挡住**：`deviceHasKeyguard=true`，截图全黑 |

---

## 三、待办

1. **解锁手机后复测 Ruru**：重点看 `Libc 文件检查`、`Syscall 文件检查` 是否从「发现」变为「未发现」；
2. **PM 查询的包名**（`com.sukisu.ultra`）不会因为 `sus_path` 消失——那是包名层面的检测，需要 `sus_map` 或包名伪装，属于下一步；
3. **重启一次**，确认 `auto_start_enabled` 与 `execute_in_post_fs_data` 真的在开机时应用了配置（可对比重启前后 `config list` 与 `add-sus-path` 的持久性）。

---

## 四、说明

- 本次只写了 SuSFS 配置（`/data/adb/ksu` 下的配置文件与内核 sus_path 表），没有改动系统分区、没有刷机；
- 锁屏无法通过 adb 解锁（不知道锁屏密码），所以 UI 复测只能等用户操作。

---

## 关联文档

- [SuSFS 隐藏效果初测：能力就绪但未配置](./20261120-1200-SuSFS隐藏效果初测-能力就绪但未配置-Claude-Opus-6.md)
- [v6 刷入成功：su 恢复、WiFi 正常、授权保留](./20261120-1145-v6刷入成功-su恢复与授权保留-Claude-Opus-6.md)
