# Google Play 崩溃弹窗定位：PlayIntegrityFix 写系统身份字段失败

- 时间：2026-11-15 18:08（GMT+8）
- 设备：Redmi Note 10 5G（M2103K19C / camellia），Android 13，MIUI EEA，自编内核 `#11`，槽 b
- 用户问题：「分析手机偶尔弹窗 Google Play 崩溃窗口」
- 本次只做**只读**分析：没清日志、没停应用、没改模块、没写手机。

---

## 一、结论

弹窗来自 **PlayIntegrityFix（简称 PIF，一个伪装设备指纹以通过 Google 完整性校验的 root 模块）**，不是内核、不是 SukiSU、也不是 SuSFS。

它在 Google Play 服务的完整性检测子进程里，按**旧版本的字段位置**去改系统身份信息（`android.os.Build` 里的静态字段），而当前这版 Google Play 服务里那个位置已经不存在，Android 运行时检测到非法字段 ID，直接把进程杀掉（SIGABRT）。系统随即弹出「Google Play 服务已停止运行」。

---

## 二、现场证据

**崩溃进程**：`com.google.android.gms.unstable`（uid 10156），这是 Google Play 服务专门用来跑完整性检测/设备认证的沙盒进程，对应服务名 `com.google.android.gms/.chimera.UnstableInternalBoundBrokerService`。

**崩溃类型**：每次都是同一个原生崩溃。

```
signal 6 (SIGABRT)
Abort message: 'Direct field pointer 0x80000070d6f7e8 not found in hierarchy of
                class java.lang.Class<android.os.Build>'
```

**调用堆栈（关键几帧）**：

```
#04 libart.so   art::DecodeArtFieldInternal(...)          ← 运行时发现字段 ID 非法
#05 libart.so   art::JNI<false>::SetStaticObjectField(...) ← 有人要写静态字段
#06 /data/adb/modules/playintegrityfix/zygisk/arm64-v8a.so ← 就是 PIF 模块
#07-#09 /data/adb/modules/zygisksu/lib64/libzygisk.so      ← Zygisk Next 注入框架
```

**频率**：17:11 开始出现，17:25–18:02 之间密集发生 20 多次；事件日志里全部记为 `am_crash: com.google.android.gms.unstable, Native crash, Aborted`。

**时间点高度吻合**：

| 项 | 时间 |
| --- | --- |
| 崩溃首次出现 | 17:11 |
| Play 商店自动更新到 `54.1.11` | **17:21:40** |
| 崩溃变密集 | 17:25 之后 |
| Google Play 服务版本 | `26.44.31`（11-07 更新） |

**指纹伪装痕迹**：崩溃日志里的系统指纹是 `Redmi/marble/marble:13/TKQ1.221114.001/V14.0.25.0.TMRCNXM`，即 **POCO F5（marble）**，而设备真实型号是 camellian。说明 PIF 的指纹伪装已经生效了一部分，但写字段这一步失败。

---

## 三、用生活化的话解释

PIF 这类模块的做法，是在 Google 服务启动检查时，**直接改系统「身份牌」上的字**：把型号改成 POCO F5、把系统指纹改成别的机型，让 Google 以为这是一台没 root 的普通手机。

改字的方式不是「按名字找字段」，而是**按预先算好的内存位置直接写**。这要求模块和系统版本严丝合缝。Play 商店 17:21 自动更新后，Google 服务里这个类结构变了，PIF 还按旧位置写，Android 运行时发现「这个位置根本不属于这个类」，出于内存安全直接终止进程。

所以它表现为：**Google 服务每次做完整性检查就崩一次**，系统把它拉起来，下次检查再崩，用户看到的就是间断性的崩溃弹窗。

---

## 四、为什么可以排除内核

- 崩溃堆栈里只有 PIF、Zygisk Next、Android 运行时（libart）、zygote，没有任何内核符号；
- 崩溃进程是 Google 服务的子进程，不是内核线程；
- 崩溃原因写得很明确：JNI 写静态字段时字段 ID 非法，属于用户态模块的错误用法；
- 本机自编内核 `#11` 只提供 root 与注入底座，Zygisk Next 能正常加载（否则堆栈里不会出现它的 so）。

因此**不要为此重刷内核或改 SuSFS 配置**，那不会解决弹窗。

---

## 五、可选方案（都需要写手机，本次未执行）

| 方案 | 具体做什么 | 代价 / 风险 |
| --- | --- | --- |
| **A. 先禁用 PIF 验证根因** | 在 root 管理器里关掉 PlayIntegrityFix 模块 → 重启 | 弹窗应立刻消失；Play Integrity 会失败，个别银行、支付、游戏可能提示「设备不安全」；可随时开回，完全可逆 |
| **B. 升级 PIF 到最新版** | 确认新版支持当前 Google 服务 `26.44`，下载后刷入模块 → 重启 | 可能直接解决；若新版仍按旧字段写，会继续崩；需要下载与重启，约 10 分钟 |
| **C. 换用 Tricky Store + 有效 keybox** | 另一套完整性方案，需要额外密钥文件 | 复杂、维护成本高，只有「必须通过完整性校验」才值得 |
| **D. 清 Google 服务数据 / 降级商店** | 重置账号状态或装旧版商店 | 治标不治本：商店会自动更新，下次检查仍崩；清数据还会丢登录状态，不推荐 |

**推荐顺序**：先做 A（最快、可逆，能一次性确认弹窗确实来自 PIF），确认后再决定是否做 B。如果你本来就不需要 Play Integrity（不用 Google Pay、不玩强制完整性校验的游戏），A 就可以长期保持。

---

## 六、边界

本次只读：没有清日志、没有强制停止应用、没有禁用/卸载模块、没有重启手机。上述任何方案都需要写手机，需用户明确授权后执行。

---

## 关联文档

- [首次真机试刷与 SukiSU 接入验证](./20261107-1110-首次真机试刷与SukiSU接入验证-Claude-Opus-6.md)
- [SuSFS 错误修复、来源统一与 v0.0.6 重编译](./20261108-0428-SuSFS错误修复与v0.0.6重编译-Claude-Opus-6.md)
