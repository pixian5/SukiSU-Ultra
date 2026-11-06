#!/usr/bin/env python3
"""Reproduce the kernel's manager-APK v2 signature check in user space.

The kernel does NOT hash the whole APK. It parses the APK Signing Block v2
and hashes the first signer's X.509 certificate, comparing its byte length and
SHA256 against a hardcoded whitelist in kernel/manager/apk_sign.c.
This script extracts the same two values so compatibility can be checked
without flashing anything.
"""
import hashlib
import struct
import sys


def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def main(path):
    d = open(path, 'rb').read()
    eocd = None
    for i in range(0x10000):
        p = len(d) - i - 2          # comment_size field of EOCD
        if p < 22:
            break
        if struct.unpack_from('<H', d, p)[0] == i:
            q = p - 20              # EOCD starts 20 bytes before comment_size
            if struct.unpack_from('<I', d, q)[0] == 0x06054B50:
                eocd = q
                break
    if eocd is None:
        sys.exit('EOCD not found')

    cd_size = u32(d, eocd + 12)
    cd_offset = u32(d, eocd + 16)
    print('APK:', path)
    print('size:', len(d), 'bytes  EOCD:', eocd, 'central_dir:', cd_offset, cd_size)
    if cd_size != eocd - cd_offset:
        sys.exit('unexpected central directory layout')
    pairs_end = cd_offset - 24
    if d[cd_offset - 16:cd_offset] != b'APK Sig Block 42':
        sys.exit('APK Signing Block magic not found')
    size_of_block = struct.unpack_from('<Q', d, pairs_end)[0]
    block_start = cd_offset - size_of_block - 8
    if struct.unpack_from('<Q', d, block_start)[0] != size_of_block:
        sys.exit('signing block size mismatch')

    pos = block_start + 8
    results = []
    while pos < pairs_end:
        pair_size = struct.unpack_from('<Q', d, pos)[0]
        q = pos + 8
        pair_end = q + pair_size
        pair_id = u32(d, q)
        print('  signing block pair id 0x%08x  size %d' % (pair_id, pair_size))
        if pair_id == 0x7109871A:
            v = d[q + 4:pair_end]
            signers_len = u32(v, 0)
            signers = v[4:4 + signers_len]
            signer_len = u32(signers, 0)
            signer = signers[4:4 + signer_len]
            sd_len = u32(signer, 0)
            sd = signer[4:4 + sd_len]
            digests_len = u32(sd, 0)
            p = 4 + digests_len
            certs_len = u32(sd, p)
            certs = sd[p + 4:p + 4 + certs_len]
            cert_len = u32(certs, 0)
            cert = certs[4:4 + cert_len]
            results.append((cert_len, hashlib.sha256(cert).hexdigest()))
        pos = pair_end

    print('v2 signing blocks:', len(results))
    for n, (size, digest) in enumerate(results):
        print('  signer %d certificate size: %d (0x%x)' % (n, size, size))
        print('  signer %d certificate sha256: %s' % (n, digest))
    return results


if __name__ == '__main__':
    main(sys.argv[1])
