#!/usr/bin/env bash
# 用途：验证「公开的 4.14 扩展接口实现」能否在厂商 4.14 内核上编译通过。
#
# 运行环境：x86_64 / aarch64 Linux 编译服务器（有 AOSP clang-r383902 与
# aarch64 交叉 binutils）。**不要在 macOS 本机运行**，本机与服务器环境不同。
#
# 边界：只编译，不写手机、不发布、不覆盖仓库；无论成功失败都会把内核树
# 里被替换的文件恢复回去，方便继续用原树做其它构建。
#
# 用法：
#   verify-public-uapi.sh <内核源码目录> <构建输出目录> <clang 工具链目录> [参考文件目录]
# 例：
#   verify-public-uapi.sh /workspace/camellian-kernel /workspace/out \
#       /workspace/aosp/clang-r383902
#   LOG=/workspace/verify-uapi.log KEEP=1 verify-public-uapi.sh ...   # 保留替换后的树
set -u

KERNEL_SRC="${1:-/workspace/camellian-kernel}"
OUT="${2:-/workspace/out}"
CLANG="${3:-/workspace/aosp/clang-r383902}"
REF="${4:-$(cd "$(dirname "$0")/.." && pwd)/reference/4.14-extension-uapi}"
LOG="${LOG:-/workspace/verify-public-uapi.log}"
KEEP="${KEEP:-0}"

# 基本检查：目录、参考文件、工具链都必须就位
for d in "$KERNEL_SRC" "$OUT" "$CLANG" "$REF"; do
  if [ ! -d "$d" ]; then echo "错误：目录不存在 $d" >&2; exit 2; fi
done
for f in susfs.c susfs.h susfs_def.h mnt_compat.c; do
  if [ ! -f "$REF/$f" ]; then echo "错误：参考文件缺失 $REF/$f" >&2; exit 2; fi
done
if [ ! -f "$OUT/.config" ]; then echo "错误：构建目录里没有 .config（$OUT）" >&2; exit 2; fi

BACKUP="$OUT/backup-before-public-uapi"
mkdir -p "$BACKUP" || exit 2
JOBS="${JOBS:-2}"   # 并发数可调：这颗 4.14 树在小内存机器上 -j4 容易卡在依赖扫描

# 备份将被替换的文件（含可能不存在的 susfs_abi.c）
for rel in fs/susfs.c fs/susfs_abi.c include/linux/susfs.h include/linux/susfs_def.h fs/Makefile; do
  if [ -f "$KERNEL_SRC/$rel" ]; then
    mkdir -p "$BACKUP/$(dirname "$rel")"
    cp -a "$KERNEL_SRC/$rel" "$BACKUP/$rel"
  fi
done

restore() {
  # 恢复内核树，保证这次验证不会污染后续构建
  cp -a "$BACKUP/fs/susfs.c" "$KERNEL_SRC/fs/susfs.c" 2>/dev/null || true
  cp -a "$BACKUP/fs/susfs_abi.c" "$KERNEL_SRC/fs/susfs_abi.c" 2>/dev/null || true
  cp -a "$BACKUP/include/linux/susfs.h" "$KERNEL_SRC/include/linux/susfs.h" 2>/dev/null || true
  cp -a "$BACKUP/include/linux/susfs_def.h" "$KERNEL_SRC/include/linux/susfs_def.h" 2>/dev/null || true
  cp -a "$BACKUP/fs/Makefile" "$KERNEL_SRC/fs/Makefile" 2>/dev/null || true
  rm -f "$KERNEL_SRC/fs/susfs_mnt_compat.c" "$OUT/fs/susfs_mnt_compat.o" "$OUT/fs/susfs.o"
}
trap restore EXIT

# 用公开实现替换 SuSFS 三个核心文件，并加入 4.14 挂载编号兼容层
cp "$REF/susfs.c"        "$KERNEL_SRC/fs/susfs.c"
cp "$REF/susfs.h"        "$KERNEL_SRC/include/linux/susfs.h"
cp "$REF/susfs_def.h"    "$KERNEL_SRC/include/linux/susfs_def.h"
cp "$REF/mnt_compat.c"   "$KERNEL_SRC/fs/susfs_mnt_compat.c"

# 公开实现把命令入口都放在 susfs.c 里，不再需要 v2.3.0 路线那个翻译层；
# 从 fs/Makefile 去掉 susfs_abi.o，并把兼容层加进编译目标。
if grep -q 'susfs_abi' "$KERNEL_SRC/fs/Makefile"; then
  sed -i 's/[[:space:]]*susfs_abi\.o//g' "$KERNEL_SRC/fs/Makefile"
fi
if ! grep -q 'susfs_mnt_compat' "$KERNEL_SRC/fs/Makefile"; then
  echo 'obj-$(CONFIG_KSU_SUSFS) += susfs_mnt_compat.o' >> "$KERNEL_SRC/fs/Makefile"
fi

echo "参考实现：$REF" | tee "$LOG"
echo "内核源码：$KERNEL_SRC" | tee -a "$LOG"
echo "开始编译：$(date '+%F %T %Z')，并发 -j$JOBS" | tee -a "$LOG"

# 与量产构建完全一致的编译参数：保留 LTO/CFI，不改 .config
cd "$KERNEL_SRC" || exit 2
export PATH="$CLANG/bin:$PATH"
export LD_LIBRARY_PATH="$CLANG/lib64:${LD_LIBRARY_PATH:-}"
MAKE_ARGS=(O="$OUT" -j"$JOBS" ARCH=arm64 CC=clang
  CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=aarch64-linux-gnu-
  LD=ld.lld NM=llvm-nm OBJCOPY=llvm-objcopy AR=llvm-ar)

# 先单独编译两个目标文件：几秒钟就能拿到语法/字段层面的结论，
# 即使后面的全量编译卡住也不会一无所获。
make "${MAKE_ARGS[@]}" fs/susfs.o fs/susfs_mnt_compat.o >> "$LOG" 2>&1
single_rc=$?
echo "单文件编译返回码：$single_rc（$(date '+%F %T %Z')）" | tee -a "$LOG"
grep -i -m 10 'error:' "$LOG" | tail -10 | tee -a "$LOG"

# 再跑完整内核编译（可能耗时较久，建议后台运行本脚本）
make "${MAKE_ARGS[@]}" >> "$LOG" 2>&1
rc=$?

echo "编译结束：$(date '+%F %T %Z')，返回码 $rc" | tee -a "$LOG"
echo "错误行数：$(grep -c -i 'error:' "$LOG" 2>/dev/null || echo 0)" | tee -a "$LOG"
echo "--- 前 20 条错误 ---" | tee -a "$LOG"
grep -i -m 20 'error:' "$LOG" | tee -a "$LOG"

if [ "$rc" -eq 0 ] && [ -f "$OUT/arch/arm64/boot/Image.gz" ]; then
  echo "结论：编译通过，内核产物 $(stat -c '%s' "$OUT/arch/arm64/boot/Image.gz") 字节" | tee -a "$LOG"
else
  echo "结论：编译未通过，详见 $LOG（这只是兼容性验证，不影响主线 v0.0.6）" | tee -a "$LOG"
fi

if [ "$KEEP" = "1" ]; then
  # 保留替换后的树以便继续调试，此时不自动恢复
  trap - EXIT
  echo "KEEP=1：已保留替换后的内核树，备份在 $BACKUP" | tee -a "$LOG"
fi

exit "$rc"
