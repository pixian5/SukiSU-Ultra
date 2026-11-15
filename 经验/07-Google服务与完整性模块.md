# Google 服务与完整性模块

## 崩溃弹窗怎么定位

- 先看崩溃缓冲区：`adb shell logcat -b crash -d -v time`，找 `Fatal signal` 与 `Abort message`。
- 再看系统记录：`adb shell dumpsys dropbox --print`，里面有 `system_app_native_crash`，带包名、版本、启动时长和完整堆栈。
- 统计频次：`adb shell logcat -b events -d | grep am_crash`。
- 对照更新时间：`dumpsys package <包名> | grep -E 'versionName|lastUpdateTime'`，崩溃起点常与某个组件自动更新对得上。

## PlayIntegrityFix（PIF）的典型崩溃

特征：

- 进程是 `com.google.android.gms.unstable`（Google Play 服务跑完整性检测的沙盒，服务名 `chimera.UnstableInternalBoundBrokerService`）；
- Abort message 形如 `Direct field pointer 0x... not found in hierarchy of class java.lang.Class<android.os.Build>`；
- 堆栈里出现 `/data/adb/modules/playintegrityfix/zygisk/*.so` 与 `/data/adb/modules/zygisksu/lib64/libzygisk.so`。

原因：PIF 按旧版本算好的字段偏移去写 `android.os.Build` 的静态字段（伪装型号/指纹），Google 服务更新后类结构变化，字段 ID 非法，Android 运行时直接 abort。表现为每次完整性检查崩一次，所以用户看到的是间断弹窗。

要点：

- 这**不是内核 / SukiSU / SuSFS 的问题**，不要为此重刷内核；
- 崩溃时间点与 Play 商店 / Google Play 服务更新时间对齐，就是强证据；
- 处理顺序：先禁用 PIF 验证弹窗是否消失（完全可逆），再考虑升级到支持当前 Google 服务版本的新版；
- 清 Google 服务数据、降级商店都治标不治本，商店会自动更新，下次检查仍崩。

## 只读排查注意

- 调试模式关闭时 `adb shell su -c ...` 不可用，读 `/data/adb/modules` 会没有输出；**不要据此判断模块不存在**，用崩溃堆栈里的模块路径作为证据即可。
- 排查时不要清日志（`logcat -c`）、不要强停应用、不要禁用模块，这些都属于写手机。
