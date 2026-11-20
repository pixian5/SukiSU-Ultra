# Ruru 复测：HMA 已生效，但 PM 查询仍被发现

- 时间：2026-11-20 12:50（GMT+8）
- 前提：HMA 已确认加载到 system_server（pid 1000），手机重启过，Ruru 重新启动

---

## 一、复测结果

| 检测项 | 配置前 | 重启+HMA 后 |
| --- | --- | --- |
| 环境检测 | ✅ 未发现 | ✅ 未发现 |
| PM 命令查询 | ❌ 发现 | ❌ **仍发现** |
| PM 常规 Api 查询 | ❌ 发现 | ❌ **仍发现** |
| PM 混合 API 查询 | ❌ 发现 | ❌ **仍发现** |
| PM 主界面查询 | ❌ 发现 | ❌ **仍发现** |
| Libc 文件检查 | ❌ 发现 | ❌ **仍发现** |
| Syscall 文件检查 | ❌ 发现 | ❌ **仍发现** |
| Xposed 模块 | ❌ 发现 | ❌ **仍发现** |
| LSPatch 软件 | ❌ 发现 | ❌ **仍发现** |
| Magisk 软件 | ✅ 未发现 | ✅ 未发现 |

**全部没有变化。**

---

## 二、结论

1. **HMA 确实在工作**（Vector 日志确认加载进 system_server），但它拦不住 Ruru：
   - Ruru 的 PM 查询大概率直接读 `/data/system/packages.list` 或走 native，而不是 Java PM API；
   - Libc/Syscall 检查直接读 `/data/app` 下的 APK 文件，更不可能被 PM hook 拦截。
2. `sus_path` 也只能隐藏具体路径，且 Ruru 检测的是**真实安装的应用**，不是残留。
3. **在 SukiSU 生态内，没有能完全骗过 Ruru 的方案**：
   - Shamiko：只隐藏 root 痕迹（su、模块挂载），不隐藏正常安装的应用；
   - SuSFS：隐藏文件/挂载，不隐藏包名；
   - HMA：隐藏 PM 列表，但 Ruru 绕过 PM。

---

## 三、建议

1. **接受 Ruru 的检测结果**：它是安全研究工具，检测强度远高于实际风控（银行/支付类应用通常不会用这种级别的包名+文件枚举）；
2. **减少检测面**：卸载确实不用的 Xposed 模块，`Xposed 模块`、`LSPatch` 两项会相应减少；
3. **保留现有组合**：Shamiko + SuSFS 已经覆盖 root 痕迹（su、模块挂载、/data/adb 路径），这是 SukiSU 上最合理的配置；
4. 不要为了骗 Ruru 去隐藏 `/data/app` 或 `su` 路径——前者可能让应用启动失败，后者会破坏提权。

---

## 四、本次确认的 SukiSU 兼容隐藏能力

| 手段 | 状态 | 有效范围 |
| --- | --- | --- |
| Shamiko v1.2.5 | 已装、working（黑名单模式） | Zygisk 层 root 痕迹 |
| SuSFS sus_path/sus_mount | 已配置持久化 | 文件路径、挂载 |
| HMA | 已装、system_server 加载成功 | Java PM 层（Ruru 不买账） |
| Zygisk Assistant | 未装 | 与 Shamiko 重叠，可不装 |

---

## 关联文档

- [HMA 已在 system_server 加载成功，待解锁复测](./20261120-1240-HMA已在system_server加载-待解锁复测-Claude-Opus-6.md)
- [SuSFS 配置后 Ruru 无变化：它检测的是包名，不是 /data/adb 路径](./20261120-1215-SuSFS配置后Ruru无变化-包名检测无法用sus_path解决-Claude-Opus-6.md)
- [Shamiko 已工作、HMA 作用域固定 system、Ruru 为 native 检测](./20261120-1220-Shamiko已工作-HMA作用域固定system-Ruru为native检测-Claude-Opus-6.md)
