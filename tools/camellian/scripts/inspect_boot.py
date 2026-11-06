#!/usr/bin/env python3
import struct, sys, binascii

p = sys.argv[1]
with open(p, 'rb') as f:
    d = f.read()
print('file_size', len(d))

# Android boot image header v2
magic = d[:8]
print('magic', magic)
k, ramdisk_sz, second_sz, dtb_sz, page_sz = struct.unpack_from('<IIIII', d, 8)
# v2 header fields: kernel_size(8), ramdisk_size(12), second_size? actually layout:
#   magic[8], kernel_size[4]=8, kernel_addr[4]=12, ramdisk_size[4]=16,
#   ramdisk_addr[4]=20, second_size[4]=24, second_addr[4]=28,
#   tags_addr[4]=32, page_size[4]=36, header_version[4]=40, os_version[4]=44,
#   name[16]=48, cmdline[512]=64, id[32]=576, extra_cmdline[1024]=608,
#   recovery_dtbo_size[4]=1632, recovery_dtbo_offset[8]=1636,
#   header_size[4]=1644, dtb_size[8]=1648, dtb_addr[8]=1656  (v2)
kernel_sz, kernel_addr, ramdisk_sz, ramdisk_addr, second_sz, second_addr, tags_addr, page_sz, hdr_ver, os_ver = struct.unpack_from('<10I', d, 8)
cmdline = d[64:64+512].split(b'\x00')[0].decode('utf-8', 'replace')
extra = d[608:608+1024].split(b'\x00')[0].decode('utf-8', 'replace')
header_size = struct.unpack_from('<I', d, 1644)[0]
dtb_sz = struct.unpack_from('<Q', d, 1648)[0]
dtb_addr = struct.unpack_from('<Q', d, 1656)[0]
print('kernel_size', kernel_sz, 'ramdisk_size', ramdisk_sz, 'second_size', second_sz)
print('page_size', page_sz, 'header_version', hdr_ver, 'header_size', header_size)
print('dtb_size', dtb_sz, 'dtb_addr', hex(dtb_addr))
print('cmdline', repr(cmdline))
print('extra_cmdline', repr(extra))

def align(x, a):
    return (x + a - 1) // a * a

off_kernel = page_sz
off_ramdisk = align(off_kernel + kernel_sz, page_sz)
print('offset_kernel', off_kernel, 'offset_ramdisk', off_ramdisk,
      'ramdisk_end', off_ramdisk + ramdisk_sz)
print('kernel_magic', binascii.hexlify(d[off_kernel:off_kernel+4]))
print('ramdisk_magic', binascii.hexlify(d[off_ramdisk:off_ramdisk+4]))

# AVB footer is the last 64 bytes
foot = d[-64:]
print('footer_magic', foot[:4])
if foot[:4] == b'AVBf':
    major, minor = struct.unpack_from('>II', foot, 4)
    original_size, vbmeta_off, vbmeta_sz = struct.unpack_from('>QQQ', foot, 12)
    print('avb_version', major, minor)
    print('original_image_size', original_size)
    print('vbmeta_offset', vbmeta_off, 'vbmeta_size', vbmeta_sz)
    print('footer_at', len(d)-64)
    blob = d[vbmeta_off:vbmeta_off+vbmeta_sz]
    print('vbmeta_blob_magic', blob[:4])
    print('vbmeta_blob_head', binascii.hexlify(blob[:120]).decode())
    # parse vbmeta header (big endian)
    if blob[:4] == b'AVB0':
        vmajor, vminor, auth_sz, aux_sz, algo = struct.unpack_from('>IIQQI', blob, 4)
        flags = struct.unpack_from('>I', blob, 16+auth_sz+aux_sz)[0] if False else None
        print('vbmeta_header_ver', vmajor, vminor, 'auth_block', auth_sz, 'aux_block', aux_sz)
        print('avb_algorithm_id', algo)
        # descriptors live in aux block
        aux = blob[16+auth_sz:16+auth_sz+aux_sz]
        pos = 0
        n = 0
        while pos + 16 <= len(aux):
            tag, num_bytes = struct.unpack_from('>QQ', aux, pos)
            if num_bytes == 0 or num_bytes > len(aux):
                break
            print('  descriptor', n, 'tag', hex(tag), 'bytes', num_bytes)
            if tag == 2:  # hash descriptor
                print('    hash descriptor head', binascii.hexlify(aux[pos+16:pos+16+64]).decode())
            pos += num_bytes
            n += 1
        print('  descriptor_count', n)

# what lies between ramdisk end and vbmeta offset
start = off_ramdisk + ramdisk_sz
if foot[:4] == b'AVBf':
    end = vbmeta_off
else:
    end = len(d)
region = d[start:end]
print('gap_region', start, end, 'len', len(region),
      'nonzero_bytes', sum(1 for b in region if b != 0))
print('gap_head', binascii.hexlify(region[:64]).decode())
