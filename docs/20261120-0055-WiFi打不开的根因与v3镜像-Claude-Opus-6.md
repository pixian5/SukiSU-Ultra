# WiFi 打不开的根因与 v3 镜像（模块 CRC 放行）

- 时间：2026-11-20 00:55（GMT+8）
- 现象：v2 刷入后 WiFi 无法打开，`/sys/module` 只有内核自带 `cfg80211`，
  没有厂商 `wlan_drv_gen4m`，`/proc/net/dev` 无 `wlan0`
- 产物：`dist/boot-sukisu-susfs-allowlist-fix-v3.img`
  - 大小 67,108,864 B
  - MD5 `5085cea8e4592996ff9d35a559e1c82b`
  - SHA256 `a5eff0b63ac5e982e6935667c9f6a5a1e284cc41f28e79d6004fc4eb3692bf8d`
- 边界：未刷机、未连手机、未发布主线 Release，v1/v2 未覆盖

## 一、先做的验证（结论：CRC 不匹配，不是 Unknown symbol）

用构建树里 genksyms 生成的 `*.o.symversions` 直接比对符号 CRC：

| 符号 | 原始树 CRC |
| --- | --- |
| `kern_path` | `0xcbb2c0bb` |
| `vfs_read` | `0x16e60d72` |
| `vfs_kern_mount` | `0x58bb227c` |

A/B 实验：在 `struct vfsmount` 末尾额外加一个 `u64` 哑字段后重算，
`vfs_kern_mount` 的 CRC 从 `0x58bb227c` 变成 `0x669cb0cb`。

**结论：结构体布局变化确实会改变导出符号的 CRC**，与「CRC 不匹配」的诊断一致，
不是「Unknown symbol」（符号缺失会走 `find_symbol` 返回 NULL 的另一条路径）。

## 二、为什么没有采用「关闭 CONFIG_MODVERSIONS」

核实 `kernel/module.c` 的 `same_magic()`：

```c
#ifdef CONFIG_MODVERSIONS
if (has_crcs) {                       /* 厂商 ko 带 __versions 段 → true */
	amagic += strcspn(amagic, " ");   /* 跳过第一个字段（版本号） */
	bmagic += strcspn(bmagic, " ");
}
return strcmp(amagic, bmagic) == 0;
#else
return strcmp(amagic, bmagic) == 0;   /* 完整比较，版本号也参与 */
#endif
```

实测 vermagic：

| | vermagic |
| --- | --- |
| 出厂内核 | `4.14.186-perf-gf8d872e9279c SMP preempt mod_unload modversions aarch64` |
| v2（MODVERSIONS=y） | `4.14.186-perf-gf4e416aea-dirty SMP preempt mod_unload modversions aarch64` |
| 若关掉 MODVERSIONS | `4.14.186-perf-gf4e416aea-dirty SMP preempt mod_unload aarch64` |

关掉后走完整 `strcmp`，与厂商 ko 的 vermagic 不相等（且少 `modversions` 一词），
模块会在 vermagic 阶段就 `-ENOEXEC`，失败点从「CRC 不一致」**提前**成
「version magic ... should be ...」，WiFi 依然打不开。

因此保留 `CONFIG_MODVERSIONS=y`（vermagic 天然匹配），只放行 CRC 检查。

## 三、改动（`kernel/module.c`，唯一一处）

```diff
 bad_version:
-	pr_warn("%s: disagrees about version of symbol %s\n",
-	       info->name, symname);
-	return 0;
+	/* SukiSU/SUSFS：本内核为 SUSFS 修改了 task_struct / vfsmount 布局，
+	 * 这些结构进入 genksyms 的 CRC 计算，导致大量导出符号 CRC 与厂商
+	 * 预编译模块（wlan_drv_gen4m.ko 等）不一致。C ABI 层面函数签名未变，
+	 * 这里放行 CRC 不匹配，仅记录一次警告；符号存在性仍由 find_symbol
+	 * 在 resolve_symbol() 中强制校验（`Unknown symbol` 仍会失败）。 */
+	pr_warn_once("%s: ignoring crc mismatch for symbol %s (SUSFS custom kernel)\n",
+		     info->name, symname);
+	return 1;
 }
```

- `check_modstruct_version()` 内部调用的也是 `check_version()`，因此
  `module_layout` 的 CRC 一并放行，无需另改。
- **符号存在性检查保留**：`resolve_symbol()` 里 `find_symbol()` 返回 NULL
  仍然失败，缺符号时报 `Unknown symbol` 不变。

补丁已存为 `tools/camellian/patches/kernel-module-crc-bypass.patch`。

## 四、配置未动

```
CONFIG_MODVERSIONS=y      ← 特意保留，vermagic 才能匹配厂商 ko
CONFIG_KSU=y
CONFIG_KSU_SUSFS=y        （10 个子项全开，含 SUS_PATH/SUS_MOUNT/SUS_KSTAT）
CONFIG_KALLSYMS_ALL=y
CONFIG_LTO_CLANG=y
CONFIG_CFI_CLANG=y
# CONFIG_MODULE_SIG is not set
```

上一版两处代码修复均保留并经产物验证：
- `allowlist.c` 的 `if (np->profile.key[0] == '\0') { continue; }`
- `dispatch.c` 的 `do_get_app_profile()` 默认配置回退

## 五、编译

```
make O=/workspace/out -j3 ARCH=arm64 CC=clang \
  CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=aarch64-linux-gnu- \
  LD=ld.lld NM=llvm-nm OBJCOPY=llvm-objcopy AR=llvm-ar
```

- 返回 0，无 error
- clang `Android (6443078 based on r383902) clang version 11.0.1` / LLD `11.0.1`
- 内核 `#3 SMP PREEMPT Fri Nov 20 00:42:40 CST 2026`
- `Image.gz` 14,201,031 B，MD5 `6de36a35f13f16774f452bd499626b67`

## 六、产物校验

| 项 | 结果 |
| --- | --- |
| 12 项结构校验 | **12/12 PASS** |
| 镜像内 kernel 与 `out/.../Image.gz` | 逐字节相同 |
| vermagic 含 `modversions` | True |
| `ignoring crc mismatch` 字符串 | True |
| dispatch 回退字符串 | True |
| allowlist 修复串 | True |
| S3 下载复核 | SHA256 一致，`cmp` 逐字节相同 |

S3：
- `cst:xbz/camellian/boot-sukisu-susfs-allowlist-fix-v3.img`
- `cst:xbz/camellian/SHA256SUMS-allowlist-fix-v3.txt`

v1/v2 均保留。

## 七、刷后验证顺序（给用户，AI 不执行）

按以下顺序验证，前一项不过不必急着看后面：

1. **WiFi 能否打开**（最直接；打不开说明 CRC 放行未生效或另有原因）
2. **`wlan0` 是否出现**：`ls /sys/class/net/`、`cat /proc/net/dev`；
   再看 `/sys/module/wlan_drv_gen4m` 是否存在
3. **相机能否打开**（厂商 camera 相关模块同样依赖 CRC 校验）
4. **指纹是否正常**
5. **最后才是授权**：管理器显示「工作中」，新应用首次授权不再报
   「更新 app profile 失败」，且用 InstallerX 装应用后授权不丢

## 八、如果 WiFi 仍不行（排查指引）

在设备上取日志：

```bash
dmesg | grep -iE "wlan_drv_gen4m|Unknown symbol|disagrees|version magic|crc"
```

按报错分类：

| dmesg 关键串 | 含义 | 下一步 |
| --- | --- | --- |
| `Unknown symbol ...` | 符号确实缺失（不是 CRC） | 逐个补符号，或确认该版本 ko 依赖的符号是否在 4.14 树中导出 |
| `version magic ... should be ...` | vermagic 不匹配 | 说明 CRC 放行生效了但 vermagic 挡在前；核对 ko 的 vermagic 字符串 |
| `disagrees about version of symbol` | CRC 放行未生效 | 确认刷入的是 v3（内核 `#3`） |
| `exec format error` / `invalid module format` | 格式或架构问题 | 检查 ko 是否 64 位 aarch64、是否被压缩 |
| 无任何 `wlan_drv_gen4m` 记录 | 模块根本没被加载 | 查 `init.rc`/`vendor` 触发条件、`insmod` 路径权限 |

另需注意：**SUSFS 改了 `task_struct` / `vfsmount` 布局**。即使 ko 加载成功，
若厂商模块在编译时内联了这些结构的偏移或尺寸，运行时可能读到错位数据。
若出现「能打开 WiFi 但异常断连/崩溃」，优先怀疑这一点，而不是 CRC。

---

## 关联文档

- [首次授权报错修复与 v2 镜像](./20261119-2350-首次授权报错修复与v2镜像-Claude-Opus-6.md)
- [授权修复内核编译与可刷镜像](./20261119-2305-授权修复内核编译与可刷镜像-Claude-Opus-6.md)
