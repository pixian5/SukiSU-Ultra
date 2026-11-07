#!/usr/bin/env python3
"""从 Android 内核镜像中提取内嵌的 ikconfig（/proc/config.gz 的来源）。

用法:
    python3 extract-ikconfig.py Image.gz -o factory.config

原理同内核源码的 scripts/extract-ikconfig：
内核把 .config 用 gzip 压缩后夹在 IKCFG_ST / IKCFG_ED 两个标记之间。
"""
import argparse
import gzip
import sys
import zlib


def decompress_kernel(blob):
    """输入可能是 gzip 的 Image.gz，也可能是裸 Image，统一返回裸 Image。"""
    if blob[:2] == b'\x1f\x8b':
        return gzip.decompress(blob)
    # Android boot v2 里常见的是 lz4/gzip，这里只处理 gzip；裸 Image 直接返回
    return blob


def extract(blob):
    raw = decompress_kernel(blob)
    start = raw.find(b'IKCFG_ST')
    if start < 0:
        sys.exit('镜像里没有 IKCFG_ST 标记：该内核未启用 CONFIG_IKCONFIG')
    gz = raw[start + 8:]
    end = gz.find(b'IKCFG_ED')
    if end >= 0:
        gz = gz[:end]
    d = zlib.decompressobj(16 + zlib.MAX_WBITS)
    try:
        config = d.decompress(gz)
    except zlib.error:
        # 有些镜像在 gzip 流后还有别的数据，按可读部分输出
        config = d.flush()
    text = config.decode('utf-8', errors='replace')
    if 'CONFIG_' not in text:
        sys.exit('解压结果不像 .config')
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image')
    ap.add_argument('-o', '--output', required=True)
    args = ap.parse_args()
    data = open(args.image, 'rb').read()
    text = extract(data)
    with open(args.output, 'w') as f:
        f.write(text)
    print('wrote', args.output, len(text), 'bytes')
    for key in ('CONFIG_LOCALVERSION', 'CONFIG_IKCONFIG', 'CONFIG_LTO_CLANG',
                'CONFIG_CFI_CLANG', 'CONFIG_THREAD_INFO_IN_TASK'):
        for line in text.splitlines():
            if line.startswith(key + '=') or line == ('# ' + key + ' is not set'):
                print(' ', line)
                break


if __name__ == '__main__':
    main()
