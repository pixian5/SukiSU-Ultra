#!/usr/bin/env python3
"""Optional companion: an empty vbmeta with verification + hashtree disabled.

This is exactly the shape `fastboot --disable-verity --disable-verification
flash vbmeta_b vbmeta.img` produces at flash time. It is NOT required if the
unlocked bootloader tolerates the stale AVB hash in the custom boot image.
It is only a fallback. Never flash it together with flash_all_lock.sh.
"""
import hashlib
import struct

OUT = '/workspace/dist/vbmeta-verification-disabled.img'
SIZE = 4096
FLAGS_HASHTREE_DISABLED = 1
FLAGS_VERIFICATION_DISABLED = 2

h = bytearray(256)
h[0:4] = b'AVB0'
struct.pack_into('>II', h, 4, 1, 0)                 # required libavb version 1.0
struct.pack_into('>QQ', h, 12, 0, 0)                # auth block = 0, aux block = 0
struct.pack_into('>I', h, 28, 0)                    # algorithm = NONE (no signature)
# 32..120: hash/signature/public_key/descriptor offsets and sizes all zero
struct.pack_into('>I', h, 120, FLAGS_HASHTREE_DISABLED | FLAGS_VERIFICATION_DISABLED)
struct.pack_into('>I', h, 124, 0)                   # rollback index location
h[128:176] = b'avbtool 1.2.0'.ljust(48, b'\x00')   # release string
h[176:256] = b'\x00' * 80                           # reserved

img = bytearray(SIZE)
img[:256] = h
open(OUT, 'wb').write(img)

# --- verify by parsing it back ---
v = open(OUT, 'rb').read()
magic = v[:4]
maj, minr = struct.unpack_from('>2I', v, 4)
auth, aux = struct.unpack_from('>2Q', v, 12)
algo = struct.unpack_from('>I', v, 28)[0]
do, dsz, rb = struct.unpack_from('>3Q', v, 96)
flags, rbl = struct.unpack_from('>2I', v, 120)
checks = [
    ('AVB0 magic', magic == b'AVB0'),
    ('no auth/aux blocks', auth == 0 and aux == 0),
    ('algorithm NONE (unsigned)', algo == 0),
    ('no descriptors', do == 0 and dsz == 0),
    ('verification + hashtree disabled', flags == 3),
    ('4 KiB partition image', len(v) == SIZE),
]
print('output', OUT)
for n, r in checks:
    print(('  PASS  ' if r else '  FAIL  ') + n)
assert all(r for _, r in checks)
print('md5    ', hashlib.md5(v).hexdigest())
print('sha256 ', hashlib.sha256(v).hexdigest())
