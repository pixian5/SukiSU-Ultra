#!/bin/bash
cd /workspace/camellian-kernel || exit 99
export PATH=/workspace/aosp/clang-r383902/bin:$PATH
export LD_LIBRARY_PATH=/workspace/aosp/clang-r383902/lib64:${LD_LIBRARY_PATH:-}
make O=/workspace/out -j4 \
  ARCH=arm64 CC=clang CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=aarch64-linux-gnu- \
  LD=ld.lld NM=llvm-nm OBJCOPY=llvm-objcopy > /workspace/build-ksu.log 2>&1
echo $? > /workspace/build-ksu.rc
