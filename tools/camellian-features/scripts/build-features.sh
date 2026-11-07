#!/bin/bash
# Incremental full build, resumable. Keeps the production LTO/CFI config.
cd /workspace/camellian-kernel || exit 99
export PATH=/workspace/aosp/clang-r383902/bin:$PATH
export LD_LIBRARY_PATH=/workspace/aosp/clang-r383902/lib64:${LD_LIBRARY_PATH:-}
timeout 540 make O=/workspace/out -j4 \
  ARCH=arm64 CC=clang CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=aarch64-linux-gnu- \
  LD=ld.lld NM=llvm-nm OBJCOPY=llvm-objcopy AR=llvm-ar \
  >> /workspace/build-features.log 2>&1
rc=$?
echo $rc > /workspace/build-features.rc
exit $rc
