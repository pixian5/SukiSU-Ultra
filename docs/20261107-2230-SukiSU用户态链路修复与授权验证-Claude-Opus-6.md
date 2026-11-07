# SukiSU 用户态链路修复与授权验证：从「开关打不开」到授权成功

> 状态：**已修复并验证**。用户可以正常在管理器里授权 root，应用能拿到权限。
> 前置：首次真机试刷已成功（见 [首次真机试刷与 SukiSU 接入验证](./20261107-1110-首次真机试刷与SukiSU接入验证-Claude-Opus-6.md)），但当时授权失败。
> 撰写时间：2026-11-07 22:30（本机时间）。

---

## 0. 一句话结论

授权失败不是内核集成坏了，而是**三个接口细节没对齐**：后台程序缺少申请内核通道的入口、读取「应用配置」时内核返回了官方管理器不认识的「不存在」、以及管理器界面入口被它自己的隐藏功能禁用。三个都修好后，管理器日志出现 `install result: true`，授权成功。

---

## 1. 现象

- 管理器显示「工作中」，但授权时开关打不开，提示「更新 app profile 失败」
- 日志反复出现：
  - `ksud::cli: Error: could not retrieve kernelsu driver fd`
  - `KsuCli: ksu failed` / `Unable to create a shell!`
  - `ksud::temporary_root: ksuctl failed: No such file or directory (os error 2)`
- 管理器界面有时直接打不开，`am start` 报「Activity class does not exist」

---

## 2. 三个根因与修复

### 2.1 `reboot` 系统调用缺钩子（后台程序拿不到通道）

**机制**：管理器本身拿到通道，是靠内核在它切换用户身份时注入一个匿名文件描述符。但这个描述符带「exec 时关闭」标志，所以管理器另起的子进程（`ksud`）继承不到。`ksud` 的标准做法是通过一个**带特定魔数的 `reboot` 系统调用**向内核「自我申请」通道。

**问题**：我们的集成只改了文件系统相关的四个挂钩点，**没有在 `kernel/reboot.c` 的 `reboot` 系统调用里挂钩子**，所以这条申请路径根本不存在。

**修复**：在 `SYSCALL_DEFINE4(reboot)` 开头（权限检查之前）加入：

```c
#ifdef CONFIG_KSU
	{
		extern int ksu_handle_sys_reboot(int magic1, int magic2, unsigned int cmd, void __user **arg);
		int ksu_ret = ksu_handle_sys_reboot(magic1, magic2, cmd, &arg);
		if (ksu_ret == 0)
			return 0;
	}
#endif
```

修复后，日志从「拿不到通道」变成 `[ksu_driver] fd installed`，后台子进程可以正常申请。

### 2.2 读取不存在的应用配置时返回错误（管理器误判）

**机制**：管理器在授权前会先「读取该应用的配置」。我们的内核对没有记录的应用返回 `-ENOENT`（不存在）。

**问题**：官方 release 版管理器期望这里返回**一份默认配置**（`use_default = true`），它把「不存在」当成失败，于是中止授权流程，界面就显示「更新 app profile 失败」，开关也写不下去。

**修复**：在 `kernel/supercall/dispatch.c` 的 `do_get_app_profile()` 里，把「没找到」的分支改为返回一份默认配置：

```c
if (!profile) {
    struct app_profile fallback;
    memset(&fallback, 0, sizeof(fallback));
    fallback.version = KSU_APP_PROFILE_VER;
    fallback.curr_uid = uid;
    fallback.allow_su = false;
    fallback.nrp_config.use_default = true;
    fallback.nrp_config.profile.umount_modules = true;
    /* copy_to_user(...) */
}
```

内核日志里能看到管理器实际调用的是 `cmd=0xc0004b0b`，解码后正是「读取应用配置」，印证了判断。

### 2.3 管理器界面入口被隐藏功能禁用（打不开）

**现象**：`cmd package resolve-activity` 返回「No activity found」，`am start` 报入口不存在；但进程能被拉起、界面却进不去。

**原因**：管理器自带的「隐藏应用」机制把启动入口（activity 别名）禁用了。一旦禁用，用户自己也会打不开。

**修复**：用同一个安装包**覆盖重装**（`adb install -r`，保留数据），入口会重新注册：

```bash
adb install -r SukiSU_v4.3.0-r2_41150-release.apk
```

**注意**：这不是每次都需要做的常规步骤，只在入口被禁用时使用。以后尽量不要在管理器里开「隐藏应用」，否则只能靠电脑重装恢复。

---

## 3. 验证证据

修复版（最终第三版，调试模式关闭）刷入后的日志：

```text
KernelSU: [ksu_driver] fd installed: 3 for pid 9009
KsuCli  : install result: true, cost: 108ms
```

- 用户态安装**真正成功**（此前多次尝试都是失败）
- 管理器首页显示「**工作中**」
- 进程列表出现以 `root` 运行的 `com.sukisu.ultra:root:0`
- 没有「拿不到通道」和 `ksuctl` 错误
- 用户在管理器里授权应用，**成功**，开关可以正常打开

---

## 4. 当前运行版本

| 项 | 值 |
| --- | --- |
| 镜像 | `backup/camellian/boot-sukisu-final3-lto-stockdtb.img` |
| MD5 | `3f687ecbc07f24ac0ecfbea56ebe14f5` |
| SHA256 | `96584b65f0010b889250e7d36c042efcb582caf989f50ec1e2cc19676c9c2727` |
| 内核 | `4.14.186-perf-gf4e416aea-dirty`，构建 `#11`，2026-11-07 03:45 UTC |
| 管理器 | `v4.3.0-r2`（41150-6），内核完整版本 `v4.3.0-r2-1cfa5734@builtin` |
| 钩子类型 | Manual Hook |
| 系统 | `V14.0.4.0.TKSEUXM`，槽位 b |
| 调试模式 | 关闭（`adb shell su` 不可用，这是正常安全设计） |

**回退件**：`backup/camellian/boot_b-before.img`（MD5 `531c534bcc8d3172e03b12a2f6dd135d`），刷回即恢复刷机前的 Magisk 状态，需另行授权。

---

## 5. 还需要用户处理的事项

**建议优先做**：

1. **重启一次**：管理器提示 Zygisk Next 需要重启才生效。重启后 Zygisk 相关模块才会真正工作。
2. **逐个启用模块**：当前 16 个模块，多数处于 disabled。一次启用一到两个，重启验证没问题再加下一个，避免一次全开导致冲突难以定位。
3. **确认授权列表**：在「超级用户」页核对已授权应用，不需要的及时撤销。

**可选**：

4. **Magisk 残留**：`/data/adb/magisk`、`magisk.db`、`post-fs-data.d`、`service.d` 仍在。SukiSU 不会使用 Magisk 本体，但兼容读取模块目录；如果后续出现异常，可以再评估是否清理，清理前必须备份。
5. **记录当前可用配置**：模块启用清单、授权清单、镜像校验值，方便以后复现。

**不要做**：

- 不要再刷调试版内核（`allow_shell = true`，任何能连 adb 的人都能 root）
- 不要在管理器里开「隐藏应用」，否则入口会再次消失
- 不要期待 KPM 或 SuSFS 可用：KPM 缺 KernelPatch 钩子、SuSFS 未集成，都属于结构性不可用

---

## 6. 本轮写入记录

| 分区 | 是否写入 | 说明 |
| --- | --- | --- |
| `boot_b` | 写入多次 | 推荐版 → 调试版 → 修复版（reboot 钩子）→ 修复版（profile fallback，当前） |
| `boot_a` | 未写入 | 一个字节没动 |
| 校验分区 / 用户数据 | 未写入 | 未动 |
| 应用 | 管理器重装过数次 | 仅覆盖安装，数据保留 |

---

## 关联文档

- [首次真机试刷与 SukiSU 接入验证](./20261107-1110-首次真机试刷与SukiSU接入验证-Claude-Opus-6.md)
- [红米 Note 10 5G 刷机执行方案与回退剧本](./20261107-0029-红米Note10-5G刷机执行方案与回退剧本-Claude-Opus-6.md)
- [手机分区只读备份与传输污染排查](./20261107-0852-手机分区只读备份与传输污染排查-Claude-Opus-6.md)
- [启动镜像版本核对与回退件定位](./20261107-0905-启动镜像版本核对与回退件定位-Claude-Opus-6.md)
