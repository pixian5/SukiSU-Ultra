# HMA 已在 system_server 加载成功，等解锁后复测

- 时间：2026-11-20 12:40（GMT+8）
- 背景：为隐藏 Ruru 的包名检测，修改了 HMA 配置并重启手机；HMA 的作用域固定在 `system`

---

## 一、HMA 加载确认

重启后在 LSPosed/Vector 日志里找到：

```
D/VectorModuleManager: Loading module com.tsng.hidemyapplist
V/VectorModuleManager: Loading class class icu.nullptr.hidemyapplist.xposed.XposedEntry
D/VectorModuleManager: Loaded module com.tsng.hidemyapplist successfully.
```

进程号 `1000`（system_server），说明 **HMA 已经在系统进程里加载**，配置改动（给 Ruru 加隐藏列表）随重启生效。

注：当前 LSPosed 实际运行的是 **Vector 框架**（`vector-cli`、`VectorLegacyBridge`），HMA 以 legacy 模块方式加载成功，功能上可用。

---

## 二、为什么之前 Ruru 没变

- 改完 `config.json` 后没有重启，HMA 的 system 层注入还是旧的；
- 本次重启后才会用新配置。

**所以之前的「没变化」不能作为 HMA 无效的结论。**

---

## 三、待复测

屏幕当前是锁屏（`mDreamingLockscreen=true`），adb 无法解锁（不知道 PIN/密码）。

解锁后需要复测：

| 检测项 | 预期 |
| --- | --- |
| PM 命令查询 / 常规 / 混合 / 主界面 | 可能变为「未发现」（HMA 过滤 PM） |
| Libc 文件检查 / Syscall 文件检查 | 仍「发现」（native 直接读 `/data/app`，HMA 拦不住） |
| Xposed / LSPatch | 取决于检测方式，可能仍「发现」 |

---

## 四、如果 PM 项仍不变

说明 Ruru 的 PM 查询也绕过了 HMA 的 hook（例如直接调 `pm` 命令或 native 读 `/data/system/packages.list`），此时 HMA 这条路也走不通。

届时只有两个选择：

1. 接受 Ruru 的检测结果（它是安全研究工具，不代表实际风控）；
2. 用 SuSFS 的 `sus_path` 逐个隐藏 `/data/app` 下的具体目录——风险是应用自身也可能读不到自己的 APK，不建议全量。

---

## 关联文档

- [SuSFS 配置后 Ruru 无变化：它检测的是包名，不是 /data/adb 路径](./20261120-1215-SuSFS配置后Ruru无变化-包名检测无法用sus_path解决-Claude-Opus-6.md)
- [隐藏方案分层与重启要求](./20261120-1230-隐藏方案分层与重启要求-Claude-Opus-6.md)
