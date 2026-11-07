#!/bin/sh
# 校验产物里 SUSFS / SukiSU 符号是否齐全
# 用法: ./verify-symbols.sh /path/to/out
set -e
OUT="${1:?输出目录}"
NM="${NM:-llvm-nm}"
VMLINUX="$OUT/vmlinux"

test -f "$VMLINUX" || { echo "找不到 $VMLINUX"; exit 1; }

echo "susfs_ 符号总数: $("$NM" "$VMLINUX" | grep -c ' [tT] susfs_')"
echo "--- SUSFS 命令入口 ---"
for s in susfs_init susfs_add_sus_path susfs_add_sus_path_loop susfs_add_sus_kstat \
         susfs_add_open_redirect susfs_set_uname susfs_set_cmdline_or_bootconfig \
         susfs_add_sus_map susfs_set_avc_log_spoofing susfs_set_priority_uid_filter \
         susfs_show_version susfs_show_variant susfs_get_enabled_features \
         susfs_start_sdcard_monitor_fn; do
	printf '%-40s' "$s"
	"$NM" "$VMLINUX" | grep -qw "$s" && echo OK || echo MISSING
done

echo "--- SukiSU 钩子 ---"
for s in ksu_handle_sys_reboot ksu_handle_setresuid ksu_handle_execveat ksu_handle_stat; do
	printf '%-40s' "$s"
	"$NM" "$VMLINUX" | grep -qw "$s" && echo OK || echo MISSING
done

echo "--- 版本字符串 ---"
strings "$VMLINUX" | grep -m1 "susfs is initialized"
