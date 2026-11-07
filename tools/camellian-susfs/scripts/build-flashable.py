#!/usr/bin/env python3
"""用出厂配置 + LTO/CFI 编译 SUSFS 内核，并打成可刷入的 boot 镜像。

前置：
  - 内核树已运行过 integrate-susfs.py（SUSFS 已接入）
  - 内核树是 feat/susfs-4.14 或含同等改动的分支
  - 手上有一份原厂 boot.img（67,108,864 字节，MD5 f8e4f42a4538b03c519bb70921d88bcc）

用法：
  python3 build-flashable.py \
      --kernel /path/to/camellian-kernel \
      --factory-boot /path/to/boot-stock.img \
      --clang /path/to/clang-r383902 \
      --out /path/to/out

产物：<out>/dist/boot-sukisu-susfs.img（64 MiB，12 项结构校验）
"""
import argparse
import os
import pathlib
import shutil
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
BOOTIMG = HERE / 'bootimg.py'
IKCONFIG = HERE / 'extract-ikconfig.py'

ENABLE = [
    'KSU', 'KSU_MANUAL_SU', 'KSU_FEATURE_ADBROOT',
    'KSU_SUSFS', 'KSU_SUSFS_SUS_PATH', 'KSU_SUSFS_SUS_MOUNT', 'KSU_SUSFS_SUS_KSTAT',
    'KSU_SUSFS_SPOOF_UNAME', 'KSU_SUSFS_ENABLE_LOG', 'KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS',
    'KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG', 'KSU_SUSFS_OPEN_REDIRECT', 'KSU_SUSFS_SUS_MAP',
    'KALLSYMS', 'KALLSYMS_ALL',
]
DISABLE = ['KSU_DEBUG', 'KPM', 'MIHW']


def run(cmd, **kw):
    print('+', ' '.join(str(c) for c in cmd) if isinstance(cmd, list) else cmd)
    return subprocess.run(cmd, shell=isinstance(cmd, str), check=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kernel', required=True)
    ap.add_argument('--factory-boot', required=True)
    ap.add_argument('--clang', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--jobs', default=str(os.cpu_count()))
    ap.add_argument('--no-lto', action='store_true',
                    help='内存不足时关闭 LTO/CFI（产物可开机，但与出厂内核不完全一致）')
    args = ap.parse_args()

    k = pathlib.Path(args.kernel).resolve()
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / 'dist').mkdir(exist_ok=True)

    env = dict(os.environ)
    env['PATH'] = str(pathlib.Path(args.clang) / 'bin') + ':' + env['PATH']
    make_common = [
        f'O={out}', 'ARCH=arm64', 'CC=clang',
        'CLANG_TRIPLE=aarch64-linux-gnu-', 'CROSS_COMPILE=aarch64-linux-gnu-',
        'LD=ld.lld', 'NM=llvm-nm', 'OBJCOPY=llvm-objcopy', 'AR=llvm-ar',
        'OBJDUMP=llvm-objdump', 'READELF=llvm-readelf', 'STRIP=llvm-strip',
    ]

    # 1) 从出厂 boot.img 里取内核，提取 ikconfig
    print('== 1. 提取出厂 ikconfig ==')
    unpack_dir = out / 'factory'
    run(['python3', str(BOOTIMG), 'unpack', args.factory_boot, '-o', str(unpack_dir)])
    config = out / '.config'
    run(['python3', str(IKCONFIG), str(unpack_dir / 'kernel'), '-o', str(config)])

    # 2) 调整配置：SUSFS 全开，调试/KPM/闭源 MIHW 关闭
    cfg = ' '.join(f'-e {x}' for x in ENABLE) + ' ' + ' '.join(f'-d {x}' for x in DISABLE)
    run(f'{k}/scripts/config --file {config} {cfg}')
    if args.no_lto:
        run(f'{k}/scripts/config --file {config} -d LTO -d LTO_CLANG -d THINLTO '
            f'-d CFI -d CFI_CLANG -e LTO_NONE')
    # 厂商触摸屏驱动在 -Werror 下会因 4KB 栈帧报错；只放行该告警
    run(f'{k}/scripts/config --file {config} --set-val FRAME_WARN 0')

    run(['make', '-C', str(k)] + make_common + ['olddefconfig'], env=env)

    # 3) 编译
    print('== 2. 编译 Image.gz ==')
    run(['make', '-C', str(k)] + make_common + [f'-j{args.jobs}', 'Image.gz'], env=env)

    image_gz = out / 'arch/arm64/boot/Image.gz'
    if not image_gz.exists():
        sys.exit('编译未产出 Image.gz')

    # 4) 重打包
    print('== 3. 重打包 boot 镜像 ==')
    dst = out / 'dist' / 'boot-sukisu-susfs.img'
    run(['python3', str(BOOTIMG), 'repack', args.factory_boot, str(image_gz), '-o', str(dst)])

    print('\n== 完成 ==')
    print('产物:', dst)
    print('大小:', dst.stat().st_size)
    print('回退: 刷回原厂 boot-stock.img 或分区备份 boot_b-before.img')


if __name__ == '__main__':
    main()
