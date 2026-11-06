#!/usr/bin/env python3
import struct, sys, binascii

p = sys.argv[1]
d = open(p, 'rb').read()
print('file_size', len(d))
print('header bytes 1600..1680:', binascii.hexlify(d[1600:1680]).decode())

# locate FDT magic d00dfeed in whole file
needle = b'\xd0\x0d\xfe\xed'
poses = []
i = 0
while True:
    j = d.find(needle, i)
    if j < 0:
        break
    poses.append(j)
    i = j + 1
print('FDT magic positions (first 20):', poses[:20], 'total', len(poses))
for j in poses[:6]:
    tot = struct.unpack_from('>I', d, j+4)[0]
    print('  at', j, 'totalsize', tot, 'ends', j+tot)

# AVB vbmeta blob full parse (big endian, 256 byte header)
foot = d[-64:]
orig, vbmeta_off, vbmeta_sz = struct.unpack_from('>QQQ', foot, 12)
blob = d[vbmeta_off:vbmeta_off+vbmeta_sz]
maj, minr, auth_sz, aux_sz, algo = struct.unpack_from('>IIQQI', blob, 4)
hash_off, hash_sz, sig_off, sig_sz, pk_off, pk_sz = struct.unpack_from('>6Q', blob, 32)
pkm_off, pkm_sz, desc_off, desc_sz, rb_index = struct.unpack_from('>5Q', blob, 80)
flags, rb_loc = struct.unpack_from('>2I', blob, 120)
print('--- vbmeta inside boot.img ---')
print('ver', maj, minr, 'auth', auth_sz, 'aux', aux_sz, 'algo', algo)
print('hash', hash_off, hash_sz, 'sig', sig_off, sig_sz, 'pubkey', pk_off, pk_sz)
print('descriptors', desc_off, desc_sz, 'rollback', rb_index, 'flags', flags, 'rb_loc', rb_loc)
print('release_string', blob[128:176].split(b'\x00')[0])
aux = blob[256+auth_sz:256+auth_sz+aux_sz]
ds = aux[desc_off:desc_off+desc_sz]
print('descriptor blob len', len(ds))
pos = 0
n = 0
while pos + 16 <= len(ds):
    tag, nb = struct.unpack_from('>2Q', ds, pos)
    if nb < 16 or pos + nb > len(ds):
        print('  stop at', pos, 'tag', tag, 'nb', nb); break
    print('  descriptor', n, 'tag', tag, 'len', nb)
    if tag == 2:  # AvbHashDescriptor
        img_sz, = struct.unpack_from('>Q', ds, pos+16+8+8+32+32)
        pname = ds[pos+16+8+8+32+32+8:pos+nb].split(b'\x00')[0]
        print('    hash desc partition_name', pname, 'image_size(img?)', img_sz)
        print('    raw', binascii.hexlify(ds[pos:pos+min(nb,120)]).decode())
    elif tag == 1: # chain partition
        print('    raw', binascii.hexlify(ds[pos:pos+min(nb,120)]).decode())
    pos += nb; n += 1
print('  count', n)

# boot payload region between ramdisk end and vbmeta
ks, = struct.unpack_from('<I', d, 8)
rs, = struct.unpack_from('<I', d, 16)
ps, = struct.unpack_from('<I', d, 36)
def al(x,a): return (x+a-1)//a*a
ok = ps
orr = al(ok+ks, ps)
re = orr+rs
print('--- layout ---')
print('kernel', ok, ks, 'ramdisk', orr, rs, 'ramdisk_end', re)
print('vbmeta_offset', vbmeta_off, 'gap', vbmeta_off-re)
gap = d[re:vbmeta_off]
print('gap nonzero', sum(1 for b in gap if b), 'first nonzero at', next((i for i,b in enumerate(gap) if b), None))
print('gap head@first', binascii.hexlify(gap[max(0,next((i for i,b in enumerate(gap) if b),0)-8):][:64]).decode())
# gzip stream end inside kernel region
kdata = d[ok:ok+ks]
print('kernel region tail 64:', binascii.hexlify(kdata[-64:]).decode())
