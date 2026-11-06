#!/usr/bin/env python3
"""Rebuild the factory boot.img with the locally built SukiSU kernel.

Layout is byte-compatible with the factory Android boot image header v2:
  page 0                : boot header v2 (2048 bytes)
  page 1                : kernel  = gzip-compressed Image (NO appended DTB)
  next page boundary    : ramdisk = factory ramdisk, untouched
  next page boundary    : DTB     = factory DTB region, untouched (includes MTK vendor header)
  next page boundary    : vbmeta blob from factory boot.img (hash is intentionally stale)
  end of 64 MiB image   : AVB footer, relocated to the new vbmeta offset

Nothing here writes to a phone. Output is an inspectable file only.
"""
import hashlib
import os
import struct
import sys

STOCK = '/workspace/rom/camellian_eea_global_images_V14.0.4.0.TKSEUXM_13.0/images/boot.img'
KERNEL = '/workspace/out/arch/arm64/boot/Image.gz'
OUT_DIR = '/workspace/dist'
OUT_IMG = sys.argv[1] if len(sys.argv) > 1 else OUT_DIR + '/boot-sukisu-stockdtb.img'

def align(x, a):
    return (x + a - 1) // a * a

def md5(b):
    return hashlib.md5(b).hexdigest()

stock = open(STOCK, 'rb').read()
kernel = open(KERNEL, 'rb').read()
print('stock size       ', len(stock))
print('stock md5        ', md5(stock))
print('built kernel     ', len(kernel), 'md5', md5(kernel), 'magic', kernel[:4].hex())
assert kernel[:4] == b'\x1f\x8b\x08\x00', 'kernel must be gzip'

ks, rs, ss, ps = struct.unpack_from('<4I', stock, 8)[0], struct.unpack_from('<I', stock, 16)[0], struct.unpack_from('<I', stock, 24)[0], struct.unpack_from('<I', stock, 36)[0]
hv = struct.unpack_from('<I', stock, 40)[0]
print('header_version   ', hv, 'page_size', ps, 'kernel_size', ks, 'ramdisk_size', rs, 'second_size', ss)
assert hv == 2 and ps == 2048 and ss == 0

o_k = ps
o_r = align(o_k + ks, ps)
o_dtb = align(o_r + rs, ps)
foot = stock[-64:]
assert foot[:4] == b'AVBf'
orig, vbo, vbs = struct.unpack_from('>3Q', foot, 12)
print('factory offsets  kernel', o_k, 'ramdisk', o_r, 'dtb', o_dtb, 'vbmeta', vbo, 'vbmeta_size', vbs)
print('factory original_image_size', orig)
assert vbo == align(o_dtb + struct.unpack_from('<I', stock, 1648)[0], ps), 'unexpected dtb/vbmeta layout'

ramdisk = stock[o_r:o_r + rs]
dtb_region = stock[o_dtb:vbo]
vbblob = stock[vbo:vbo + vbs]
print('ramdisk          ', len(ramdisk), ramdisk[:4].hex(), 'md5', md5(ramdisk))
print('dtb region       ', len(dtb_region), 'FDT magic offset inside region', dtb_region.find(b'\xd0\x0d\xfe\xed'), 'md5', md5(dtb_region))
print('vbmeta blob      ', len(vbblob), vbblob[:4], 'md5', md5(vbblob))
assert ramdisk[:4] == b'\x1f\x8b\x08\x00'
assert dtb_region.find(b'\xd0\x0d\xfe\xed') >= 0
assert vbblob[:4] == b'AVB0'

# ---- build the new image -------------------------------------------------
hdr = bytearray(stock[:ps])
struct.pack_into('<I', hdr, 8, len(kernel))          # kernel_size
# boot header 'id' is a build-time SHA1 fingerprint, not a security check.
# Mirror mkbootimg's intent with a deterministic digest of the payloads.
hdr[576:596] = hashlib.sha1(kernel + ramdisk + dtb_region).digest()
hdr[596:608] = b'\x00' * 12

n_r = align(o_k + len(kernel), ps)
n_dtb = align(n_r + rs, ps)
n_vbo = align(n_dtb + len(dtb_region), ps)
print('new offsets      kernel', o_k, 'ramdisk', n_r, 'dtb', n_dtb, 'vbmeta', n_vbo)

img = bytearray(len(stock))                          # keep the exact 64 MiB partition size
img[:ps] = hdr
img[o_k:o_k + len(kernel)] = kernel
img[n_r:n_r + len(ramdisk)] = ramdisk
img[n_dtb:n_dtb + len(dtb_region)] = dtb_region
img[n_vbo:n_vbo + len(vbblob)] = vbblob

newfoot = bytearray(foot)
struct.pack_into('>3Q', newfoot, 12, n_vbo, n_vbo, vbs)
img[-64:] = newfoot

os.makedirs(OUT_DIR, exist_ok=True)
open(OUT_IMG, 'wb').write(img)

# ---- verify --------------------------------------------------------------
v = open(OUT_IMG, 'rb').read()
vk, vr = struct.unpack_from('<I', v, 8)[0], struct.unpack_from('<I', v, 16)[0]
v_o_r, v_o_dtb = align(ps + vk, ps), align(align(ps + vk, ps) + vr, ps)
vf = v[-64:]
vo, vvo, vvs = struct.unpack_from('>3Q', vf, 12)
checks = [
    ('size matches factory 64 MiB', len(v) == len(stock)),
    ('header magic', v[:8] == b'ANDROID!'),
    ('kernel_size patched', vk == len(kernel)),
    ('ramdisk_size unchanged', vr == rs),
    ('kernel payload intact', v[ps:ps + len(kernel)] == kernel),
    ('ramdisk payload intact', v[v_o_r:v_o_r + rs] == ramdisk),
    ('dtb payload intact', v[v_o_dtb:v_o_dtb + len(dtb_region)] == dtb_region),
    ('vbmeta payload intact', v[vvo:vvo + vvs] == vbblob),
    ('AVB footer magic', vf[:4] == b'AVBf'),
    ('AVB original_image_size relocated', vo == n_vbo),
    ('AVB vbmeta_offset relocated', vvo == n_vbo),
    ('no stray bytes in padding', all(b == 0 for b in v[ps + len(kernel):v_o_r])),
]
print('--- verification ---')
ok = True
for name, res in checks:
    print(('  PASS  ' if res else '  FAIL  ') + name)
    ok &= bool(res)
if not ok:
    sys.exit('verification failed')
print('output           ', OUT_IMG)
print('size             ', os.path.getsize(OUT_IMG))
print('md5              ', md5(v))
print('sha256           ', hashlib.sha256(v).hexdigest())
print()
print('NOTE: the AVB hash descriptor inside the retained vbmeta blob still describes'),
print('      the factory payload. It cannot be re-signed without the vendor private key.')
print('      On an unlocked bootloader verification errors are non-fatal; this is the')
print('      same condition the currently installed Magisk Alpha already relies on.')
