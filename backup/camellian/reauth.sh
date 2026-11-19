#!/system/bin/sh
# 批量把已授权应用写成带包名的永久配置，避免被按安装清单清理
M=10509
for pair in "10800:com.rosan.installer.x" "10267:app.morphe.manager"; do
  uid=${pair%%:*}; name=${pair#*:}
  J="{\"name\":\"$name\",\"currentUid\":$uid,\"allowSu\":true,\"rootUseDefault\":true,\"rootTemplate\":null,\"uid\":0,\"gid\":0,\"groups\":[],\"capabilities\":[],\"context\":\"u:r:ksu:s0\",\"namespace\":0,\"nonRootUseDefault\":true,\"umountModules\":true,\"flags\":1}"
  /data/adb/ksud temporary-root apply $M permanent false "$J"
  echo "$name rc=$?"
done
