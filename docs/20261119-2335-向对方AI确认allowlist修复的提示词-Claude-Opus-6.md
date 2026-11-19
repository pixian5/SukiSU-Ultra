# 向对方 AI 确认 allowlist 修复的提示词

- 时间：2026-11-19 23:35（GMT+8）
- 用途：让对方 AI 证明它编译的 `boot-sukisu-susfs-allowlist-fix.img` 确实包含「清理时跳过空包名」这处修复；如果没有，要求它补上并重编
- 背景：镜像结构、配置、校验值都已核对通过，唯独「修复是否编进去」无法从二进制确认

---

## 提示词（可直接复制）

```
你之前编译并上传了 cst:xbz/camellian/boot-sukisu-susfs-allowlist-fix.img
（SHA256 7b24ba77ba79243a367e3b4b72ee4020886bb831e23b10535e6e377c6a265a1e）。

我需要确认这份镜像是否包含一处「授权空包名」修复。请逐条回答，不要只回「包含了」三个字。

1. 编译用的源码：
   - 厂商内核（MiCode/Xiaomi_Kernel_OpenSource）的分支与 commit
   - SukiSU（SukiSU-Ultra/SukiSU-Ultra）的分支与 commit
   - SuSFS 的来源与版本
   - 你应用过的所有补丁：文件名 + 关键 diff

2. 打开 kernel/policy/allowlist.c，找到 ksu_prune_allowlist()，回答：
   - 函数里是否有 `if (np->profile.key[0] == '\0') { continue; }`（或等价判断）？
   - 请贴出从 `hash_for_each_safe (...)` 到 `if (!is_preserved_uid && !is_uid_valid(...))` 的完整代码。

3. 贴出 .config 里以下项的实际值：
   CONFIG_KSU、CONFIG_KSU_SUSFS、CONFIG_KSU_SUSFS_SUS_PATH、
   CONFIG_KSU_SUSFS_SUS_MOUNT、CONFIG_KSU_SUSFS_SUS_KSTAT、
   CONFIG_KALLSYMS_ALL、CONFIG_LTO_CLANG、CONFIG_CFI_CLANG。

4. 编译命令、clang/LLD 版本、编译完成时间。

5. 如果第 2 条答案是「没有」：请补上这段判断并重新全量编译，用新文件名
   （如 boot-sukisu-susfs-allowlist-fix-v2.img）上传，给出新 SHA256，
   不要覆盖旧文件。补丁位置与内容：
       在 ksu_prune_allowlist() 里 `bool is_preserved_uid = ...;` 之后插入：
       // 空包名记录无法与已安装应用清单匹配，跳过而不是删除，避免误删有效授权
       if (np->profile.key[0] == '\0') {
           continue;
       }

6. 全程不要刷机、不要连接手机、不要发布到主线 Release。

回报格式：逐条回答 + 代码/配置片段 + 新镜像 SHA256（如重编）。
```

---

## 使用说明

- 这份提示词只要求对方**自证**，不要求它重新解释整条编译流程；第 5 条才触发重编。
- 对方贴回代码后，核对 `ksu_prune_allowlist` 里确实多了 `key[0] == '\0'` 的 `continue` 即可。
- 如果对方重编，新镜像按同样的 12 项结构 + SHA256 流程再核一遍，再考虑刷机。

---

## 关联文档

- [分析：S3 上对方编译的镜像](./20261119-2330-对方编译镜像分析-Claude-Opus-6.md)
- [交给其他 AI 的编译提示词](./20261119-2115-交给其他AI的编译提示词-Claude-Opus-6.md)
