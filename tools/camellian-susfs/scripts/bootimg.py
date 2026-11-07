#!/usr/bin/env python3
"""Android boot image header v2 解包 / 重打包（camellian 专用，64 MiB 分区）。

用法：
    # 查看结构
    python3 bootimg.py info factory-boot.img

    # 解包出 kernel / ramdisk / dtb / vbmeta
    python3 bootimg.py unpack factory-boot.img -o unpacked/

    # 用新内核重打包（保留原厂 ramdisk / dtb / vbmeta）
    python3 bootimg.py repack factory-boot.img new-Image.gz -o boot-new.img

重打包逻辑与 tools/camellian/scripts/pack_boot.py 一致：
保留 64 MiB 分区大小、原厂 ramdisk 与 DTB 区段、AVB footer 重定位；
vbmeta 内的哈希描述仍是原厂的，无法在没有厂商私钥的情况下重签。
"""
import argparse
import hashlib
import os
import struct
import sys

AVB_MAGIC = b'AVBf'


def align(x, a):
    return (x + a - 1) // a * a


def parse(blob):
    if blob[:8] != b'ANDROID!':
        sys.exit('不是 Android boot image（缺少 ANDROID! magic）')
    kernel_size = struct.unpack_from('<I', blob, 8)[0]
    ramdisk_size = struct.unpack_from('<I', blob, 16)[0]
    second_size = struct.unpack_from('<I', blob, 24)[0]
    page_size = struct.unpack_from('<I', blob, 36)[0]
    header_version = struct.unpack_from('<I', blob, 40)[0]
    if header_version != 2:
        sys.exit(f'只支持 header v2，当前 v{header_version}')
    if second_size != 0:
        sys.exit(f'second_size 非 0（{second_size}），此设备不应出现')
    o_kernel = page_size
    o_ramdisk = align(o_kernel + kernel_size, page_size)
    o_dtb = align(o_ramdisk + ramdisk_size, page_size)
    dtb_size = struct.unpack_from('<I', blob, 1648)[0]
    o_vbmeta = align(o_dtb + dtb_size, page_size)
    footer = blob[-64:]
    if footer[:4] != AVB_MAGIC:
        sys.exit('AVB footer 缺失')
    _, vbmeta_offset, vbmeta_size = struct.unpack_from('>3Q', footer, 12)
    if vbmeta_offset != o_vbmeta:
        sys.exit(f'vbmeta 偏移不符：footer={vbmeta_offset} 计算={o_vbmeta}')
    return {
        'page_size': page_size,
        'kernel_size': kernel_size,
        'ramdisk_size': ramdisk_size,
        'dtb_size': dtb_size,
        'o_kernel': o_kernel,
        'o_ramdisk': o_ramdisk,
        'o_dtb': o_dtb,
        'o_vbmeta': o_vbmeta,
        'vbmeta_size': vbmeta_size,
        'footer': footer,
    }


def write(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


def cmd_info(args):
    blob = open(args.image, 'rb').read()
    info = parse(blob)
    print('file             ', args.image)
    print('size             ', len(blob))
    print('md5              ', hashlib.md5(blob).hexdigest())
    for k in ('page_size', 'kernel_size', 'ramdisk_size', 'dtb_size',
              'o_kernel', 'o_ramdisk', 'o_dtb', 'o_vbmeta', 'vbmeta_size'):
        print(f'{k:<17}', info[k])


def cmd_unpack(args):
    blob = open(args.image, 'rb').read()
    i = parse(blob)
    out = args.output
    write(os.path.join(out, 'kernel'),
          blob[i['o_kernel']:i['o_kernel'] + i['kernel_size']])
    write(os.path.join(out, 'ramdisk'),
          blob[i['o_ramdisk']:i['o_ramdisk'] + i['ramdisk_size']])
    write(os.path.join(out, 'dtb'),
          blob[i['o_dtb']:i['o_dtb'] + i['dtb_size']])
    write(os.path.join(out, 'vbmeta'),
          blob[i['o_vbmeta']:i['o_vbmeta'] + i['vbmeta_size']])
    write(os.path.join(out, 'header'), blob[:i['page_size']])
    print('unpacked to', out)


def repack(stock, kernel):
    i = parse(stock)
    ps = i['page_size']
    ramdisk = stock[i['o_ramdisk']:i['o_ramdisk'] + i['ramdisk_size']]
    dtb = stock[i['o_dtb']:i['o_dtb'] + i['dtb_size']]
    vbmeta = stock[i['o_vbmeta']:i['o_vbmeta'] + i['vbmeta_size']]
    assert kernel[:4] == b'\x1f\x8b\x08\x00', '内核必须是 gzip（Image.gz）'

    hdr = bytearray(stock[:ps])
    struct.pack_into('<I', hdr, 8, len(kernel))
    hdr[576:596] = hashlib.sha1(kernel + ramdisk + dtb).digest()
    hdr[596:608] = b'\x00' * 12

    o_k = ps
    o_r = align(o_k + len(kernel), ps)
    o_dtb = align(o_r + len(ramdisk), ps)
    o_vb = align(o_dtb + len(dtb), ps)

    img = bytearray(len(stock))
    img[:ps] = hdr
    img[o_k:o_k + len(kernel)] = kernel
    img[o_r:o_r + len(ramdisk)] = ramdisk
    img[o_dtb:o_dtb + len(dtb)] = dtb
    img[o_vb:o_vb + len(vbmeta)] = vbmeta
    foot = bytearray(stock[-64:])
    struct.pack_into('>3Q', foot, 12, o_vb, o_vb, len(vbmeta))
    img[-64:] = foot
    return bytes(img)


def verify(img, stock, kernel):
    i = parse(stock)
    ps = i['page_size']
    v = parse(img)
    checks = [
        ('size matches factory', len(img) == len(stock)),
        ('header magic', img[:8] == b'ANDROID!'),
        ('kernel_size patched', v['kernel_size'] == len(kernel)),
        ('ramdisk_size unchanged', v['ramdisk_size'] == i['ramdisk_size']),
        ('kernel intact', img[v['o_kernel']:v['o_kernel'] + len(kernel)] == kernel),
        ('ramdisk intact', img[v['o_ramdisk']:v['o_ramdisk'] + i['ramdisk_size']]
         == stock[i['o_ramdisk']:i['o_ramdisk'] + i['ramdisk_size']]),
        ('dtb intact', img[v['o_dtb']:v['o_dtb'] + i['dtb_size']]
         == stock[i['o_dtb']:i['o_dtb'] + i['dtb_size']]),
        ('vbmeta intact', img[v['o_vbmeta']:v['o_vbmeta'] + i['vbmeta_size']]
         == stock[i['o_vbmeta']:i['o_vbmeta'] + i['vbmeta_size']]),
        ('AVB footer magic', img[-64:][:4] == AVB_MAGIC),
        ('padding zeroed', all(b == 0 for b in img[ps + len(kernel):v['o_ramdisk']])),
    ]
    ok = True
    for name, res in checks:
        print(('  PASS  ' if res else '  FAIL  ') + name)
        ok &= bool(res)
    return ok


def cmd_repack(args):
    stock = open(args.stock, 'rb').read()
    kernel = open(args.kernel, 'rb').read()
    img = repack(stock, kernel)
    write(args.output, img)
    print('output           ', args.output)
    print('size             ', len(img))
    print('md5              ', hashlib.md5(img).hexdigest())
    print('sha256           ', hashlib.sha256(img).hexdigest())
    if not verify(img, stock, kernel):
        sys.exit('结构校验失败')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('info'); p.add_argument('image'); p.set_defaults(func=cmd_info)
    p = sub.add_parser('unpack'); p.add_argument('image'); p.add_argument('-o', '--output', required=True)
    p.set_defaults(func=cmd_unpack)
    p = sub.add_parser('repack')
    p.add_argument('stock'); p.add_argument('kernel'); p.add_argument('-o', '--output', required=True)
    p.set_defaults(func=cmd_repack)
    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
