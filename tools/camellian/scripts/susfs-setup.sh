#!/system/bin/sh
K=/data/adb/ksud
# 持久化：隐藏路径列表（不含 su / ksud 自身，避免 v5 的提权入口被藏）
$K susfs config set sus_paths "/data/adb/ksu,/data/adb/lspd,/data/adb/modules,/data/adb/modules_update,/data/adb/post-fs-data.d,/data/adb/service.d"
$K susfs config set auto_start_enabled 1
$K susfs config set execute_in_post_fs_data 1
# 立即生效
for p in /data/adb/ksu /data/adb/lspd /data/adb/modules /data/adb/modules_update /data/adb/post-fs-data.d /data/adb/service.d; do
  $K susfs add-sus-path "$p" && echo "OK $p" || echo "FAIL $p"
done
echo '--- config ---'
$K susfs config list
