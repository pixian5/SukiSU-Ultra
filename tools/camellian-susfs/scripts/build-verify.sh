#!/bin/sh
# 编译验证脚本（x86_64 沙箱 / Ubuntu 24.04 实测通过）
# 用法: ./build-verify.sh /path/to/camellian-kernel /path/to/clang-r383902 /path/to/out
set -e

K="${1:?内核源码目录}"
TC="${2:?clang 工具链目录（AOSP r383902）}"
OUT="${3:?输出目录}"

export PATH="$TC/bin:$PATH"

mkdir -p "$OUT"
make -C "$K" O="$OUT" ARCH=arm64 camellian_defconfig \
	CC=clang CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=aarch64-linux-gnu-

# SUSFS 配置
"$K/scripts/config" --file "$OUT/.config" \
	-e KSU -d KSU_DEBUG -e KSU_MANUAL_SU \
	-e KSU_SUSFS -e KSU_SUSFS_SUS_PATH -e KSU_SUSFS_SUS_MOUNT -e KSU_SUSFS_SUS_KSTAT \
	-e KSU_SUSFS_SPOOF_UNAME -e KSU_SUSFS_ENABLE_LOG -e KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS \
	-e KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG -e KSU_SUSFS_OPEN_REDIRECT -e KSU_SUSFS_SUS_MAP \
	-e HQ_SYSFS_SUPPORT -d KPM

# 仅编译验证用：关闭 LTO/CFI 以缩短时间；关掉本树缺失的闭源 MIHW；
# FRAME_WARN=0 绕过三处厂商触摸屏驱动的 4KB 栈帧告警（-Werror 下会中断）。
"$K/scripts/config" --file "$OUT/.config" \
	-d LTO -d LTO_CLANG -d THINLTO -d CFI -d CFI_CLANG -e LTO_NONE \
	-d MIHW --set-val FRAME_WARN 0

make -C "$K" O="$OUT" ARCH=arm64 olddefconfig \
	CC=clang CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=aarch64-linux-gnu-

make -C "$K" O="$OUT" -j"$(nproc)" ARCH=arm64 Image.gz \
	CC=clang CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=aarch64-linux-gnu- \
	LD=ld.lld NM=llvm-nm OBJCOPY=llvm-objcopy AR=llvm-ar \
	OBJDUMP=llvm-objdump READELF=llvm-readelf STRIP=llvm-strip

echo "== 产物 =="
ls -l "$OUT/arch/arm64/boot/Image.gz"
md5sum "$OUT/arch/arm64/boot/Image.gz"
sha256sum "$OUT/arch/arm64/boot/Image.gz"
