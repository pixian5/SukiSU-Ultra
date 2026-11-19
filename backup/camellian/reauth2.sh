#!/system/bin/sh
M=10509
apply() {
  uid=$1; name=$2
  J="{\"name\":\"$name\",\"currentUid\":$uid,\"allowSu\":true,\"rootUseDefault\":true,\"rootTemplate\":null,\"uid\":0,\"gid\":0,\"groups\":[],\"capabilities\":[],\"context\":\"u:r:ksu:s0\",\"namespace\":0,\"nonRootUseDefault\":true,\"umountModules\":true,\"flags\":1}"
  /data/adb/ksud temporary-root apply $M permanent false "$J" >/dev/null 2>&1 && echo "OK $uid $name" || echo "FAIL $uid $name"
}
apply 10730 com.termux
apply 10697 com.speedsoftware.rootexplorer
apply 10298 com.modify.installer
apply 10520 rikka.appops
apply 10608 ltd.nextalone.pkginstallerplus
apply 10694 app.revanced.manager.flutter
apply 10695 io.github.chsbuffer.revancedxposed
apply 10324 moe.shizuku.redirectstorage
apply 10799 eu.hxreborn.gplayadblock
