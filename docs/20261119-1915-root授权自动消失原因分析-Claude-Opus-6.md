# root 授权自动消失的原因：给的是「临时 root」，不是永久授权

- 时间：2026-11-19 19:15（GMT+8）
- 设备：Redmi Note 10 5G（M2103K19C / camellia），Android 13，自编内核 `#11`，槽 b，开机 23 小时
- 用户问题：「授予 root 成功之后，root 权限会自动消失，我还得下次继续重新的打开这个 root 开关」
- 本次只读分析：没改配置、没动模块、没重启手机。

---

## 一、结论

**这不是授权写入失败，也不是内核 bug。** 管理器给这个应用授予的是 **「临时 root」（temporary root）**，它带一个租期：

- 默认 **10 分钟**（管理器的默认值，可改 5 / 10 / 30 / 60 分钟或自定义，上限 7 天）；
- 租期还与「本次开机」绑定，**只要重启就一律失效**，哪怕设成「永久」的租约也会因重启作废；
- 到期后，常驻的 `ksud`（SukiSU 的后台守护进程）会自动撤销授权，管理器的应用详情页每秒轮询一次，发现授权没了就把开关自动关掉。

所以你看到的「授权成功后自动消失、下次还要重新打开」，是临时租期到点的正常表现。

---

## 二、现场证据

**进程参数直接暴露了模式**：

```
root 802 1 ... ksud temporary-root watch
```

`ksud` 自开机起就带着 `temporary-root watch` 常驻（开机 23 小时未重启），说明临时 root 的监视器在工作。

**源码里的租约机制**（`userspace/ksud/src/temporary_root.rs`）：

- 状态目录 `/data/adb/ksu/temporary-root`；
- 每条租约记录 `boot`（本次开机的标识）与 `deadline`（到期秒数）；
- 判断过期：`lease.boot != 当前 boot` → 过期；`deadline` 到了 → 过期；
- 监视器每秒扫描一次，过期就执行撤销；
- 帮助文本明确写着「best-effort userspace temporary root leases (not kernel-enforced)」，即这是用户态尽力而为的临时授权，不是内核强制的永久状态。

**管理器的默认时长**（`manager/.../profile/TemporaryRoot.kt`）：

```kotlin
fun defaultMinutes(context: Context) =
    context.getSharedPreferences("temporary_root", 0)
        .getInt("minutes", 10)          // 默认 10 分钟
        .coerceIn(1, 10080)
```

**管理器的保存方式**（同一个文件）：

```kotlin
val mode = if (!updateLease) "keep" else seconds?.toString() ?: "permanent"
```

只有 `mode = permanent`（且 `updateLease = true`、`seconds = null`）才是永久授权；传了秒数就是限时租约。

**界面为什么自动关开关**（`AppProfileScreen.kt`）：

```kotlin
while (true) {
    delay(1000)
    if (!saving && profile.allowSu) {
        val current = Natives.getAppProfile(packageName, uid)
        if (!current.allowSu) {       // 租约被撤销后内核读回 false
            profile = current
            temporaryEnabled = false
            viewModel.loadAppList()
        }
    }
}
```

每秒对比一次内核里的授权状态，发现变回 `false` 就同步关闭界面开关。

---

## 三、为什么「授予成功」之后还会消失

授予那一刻确实成功了：内核里的应用配置被写入 `allowSu = true`，应用能拿到 root。但同时管理器给这个 uid 写了一条**带期限的租约**。期限一到（默认 10 分钟），或者手机重启（开机标识变了），`ksud` 的监视器撤销授权，内核状态回到 `false`，界面随即把开关关掉。

所以「成功」和「永久」是两件事：成功只代表当下生效，是否持久取决于保存时用的是 `permanent` 还是带秒数的租约。

---

## 四、怎么改成永久授权

在管理器的应用详情页里：

1. 先确认「临时 root」这个开关是**关闭**状态（关闭后再打开 root 开关，保存的是永久配置）；
2. 打开 root 开关并保存；
3. 之后可以验证：在终端里执行 `/data/adb/ksud temporary-root status <该应用 uid>`，返回 `permanent` 或 `none` 就对了；返回 `timed` / `boot` 说明还是临时。

注意一个容易踩的点：如果之前已经存在租约，之后再「打开开关」时管理器用的是 `keep` 模式（只保存配置、不动已有租约），旧租约仍会在到期时把授权撤掉。**先关掉临时开关、保存一次，再打开永久授权**，能确保租约被清掉。

---

## 五、顺带发现的系统状态（不是根因，但会影响体验）

- 负载 22、内存 5.7 GB 可用只剩 1.1 GB、4 GB swap 已用 2.3 GB，`kswapd0` 持续换页；
- 管理器**不在系统省电白名单**里，MIUI 可能冻结它的后台，导致界面状态同步延迟；
- 管理器当前用的是随机化的入口别名（`...ui.jeksggvxarxActivityAliasDefaultStatic`），说明「隐藏应用」功能是开着的；这不影响授权，但和之前的经验一致——排查问题时容易误判入口。

这些会让管理器变卡、开关状态显示滞后，但**不会把永久授权变没**；授权消失的唯一原因是临时租约。

---

## 六、边界

本次只读：没有改管理器设置、没有执行 `temporary-root` 命令、没有禁用模块、没有重启手机。改成永久授权需要你在管理器里操作（或在授权终端里执行命令），属于写手机，需你明确授权后我才会代做。

---

## 关联文档

- [首次真机试刷与 SukiSU 接入验证](./20261107-1110-首次真机试刷与SukiSU接入验证-Claude-Opus-6.md)
- [Google Play 崩溃弹窗定位](./20261115-1808-GooglePlay崩溃弹窗定位-Claude-Opus-6.md)
