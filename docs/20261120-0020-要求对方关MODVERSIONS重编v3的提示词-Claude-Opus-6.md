# 要求对方关闭 MODVERSIONS 重编 v3 的提示词

- 时间：2026-11-20 00:20（GMT+8）
- 背景：v2 内核 WiFi 打不开，根因是 `CONFIG_MODVERSIONS=y` + SuSFS 修改结构体 → vendor 预编译模块（`wlan_drv_gen4m`）符号 CRC 校验失败，内核拒绝加载
- 目标：让对方关闭 `CONFIG_MODVERSIONS` 重编 v3，其余不动

---

## 提示词（可直接复制）

```
v2 刷入后 WiFi 打不开：/sys/module 里只有内核自带的 cfg80211，没有厂商预编译的
wlan_drv_gen4m，/proc/net/dev 里没有 wlan0。已确认不是配置漏项：
两版的 CFG80211 / MTK_COMBO / MAC80211 配置完全相同，vermagic 也完全相同。

根因：CONFIG_MODVERSIONS=y 时内核会校验每个导出符号的 CRC，而 SuSFS 的 4.14 补丁
修改了 struct inode / task_struct / mount 等核心结构，导致大量符号 CRC 变化；
/vendor/lib/modules/wlan_drv_gen4m.ko 是厂商预编译的，CRC 对不上，内核拒绝加载。

请重编 v3，只改一个配置：

1. 在 .config 里关闭 CONFIG_MODVERSIONS：
       scripts/config --file /workspace/out/.config -d MODVERSIONS
   然后确认文件里是：
       # CONFIG_MODVERSIONS is not set
   （同时确认 CONFIG_MODULE_SIG_FORCE 未设置，避免签名校验再挡一层。）

2. 其余配置不要动：CONFIG_KSU=y、CONFIG_KSU_SUSFS 全套、CONFIG_KALLSYMS_ALL=y、
   CONFIG_LTO_CLANG=y、CONFIG_CFI_CLANG=y 保持原样；
   上一版的两处代码修复也必须保留：
   - kernel/policy/allowlist.c 的 ksu_prune_allowlist() 里 key[0] == '\0' 跳过；
   - kernel/supercall/dispatch.c 的 do_get_app_profile() 默认配置回退。

3. 因为改了配置，需要全量重编。确认返回 0、无 error。

4. 打包成 boot-sukisu-susfs-allowlist-fix-v3.img，12 项结构校验全过；
   上传 S3，不要覆盖 v1/v2，给 SHA256。

5. 刷后优先验证顺序（你不需要刷，只写进说明让用户验证）：
   WiFi 能否打开、wlan0 是否出现、相机能否打开、指纹是否正常，最后才是授权。

6. 如果关掉 MODVERSIONS 后 WiFi 仍然不行，请把 dmesg 里 wlan_drv_gen4m 的
   加载错误贴出来（常见是 Unknown symbol 或 disagrees about version of symbol），
   再决定下一步。

7. 不要刷机、不要连接手机、不要发布主线 Release。
```

---

## 已知风险

- 关闭 `CONFIG_MODVERSIONS` 后，内核不再校验模块符号版本。同版本内核的厂商模块通常能正常加载，但如果某个模块依赖的 ABI 真的变了，可能出现不稳定（概率不高，但存在）。
- 这是社区自定义内核解决 vendor 模块加载失败的常规做法，属于「先能用」的取舍；如果追求绝对稳定，只能放弃 SuSFS（回到 final3 路线）。

---

## 关联文档

- [v2 内核 WiFi 失效根因与回退](./20261120-0015-v2内核WiFi失效根因与回退-Claude-Opus-6.md)
- [刷入 v2 镜像与验证结果](./20261120-0005-刷入v2镜像与验证结果-Claude-Opus-6.md)
