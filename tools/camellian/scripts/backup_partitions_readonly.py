#!/usr/bin/env python3
"""Read-only partition backup: phone -> local Mac, for exact rollback.

This script NEVER writes to the phone. It only:
  * reads system properties (getprop),
  * reads kernel-reported partition sizes from /sys/class/block,
  * reads partition contents with `dd if=...` over `adb exec-out`.

Why the CRLF reversal is needed
-------------------------------
The `adb exec-out` channel on this device is NOT binary-clean: every 0x0A
byte in the payload is emitted as 0x0D 0x0A (LF -> CRLF), so a plain
`dd if=...` read comes back larger than the partition. On boot_b this added
exactly 105890 bytes and shifted the trailing AVB footer by the same amount.
Replacing every CRLF pair with a single LF is the exact inverse: an original
0x0D 0x0A pair becomes 0x0D 0x0D 0x0A on the wire and is restored to
0x0D 0x0A. The restored length must equal the kernel-reported size
(/sys/class/block/<dev>/size * 512), otherwise the file is rejected.

Each partition is read twice and the restored payloads are compared. As a
third, channel-independent witness, boot_b is additionally read through the
phone's base64 encoder, whose output contains no raw binary bytes at all.

Nothing here reboots the phone, switches slots, writes a partition, pushes a
file, or installs anything.
"""
import base64
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ADB = '/Users/x/Library/Android/sdk/platform-tools/adb'
OUT = Path('/Users/x/camellian-flash')

# Partition names only; the actual block device node is resolved live on the
# phone, because /dev/block/sdcNN numbering can change across reboots.
PARTS = [
    'boot_b', 'vbmeta_b', 'vbmeta_system_b', 'vbmeta_vendor_b',
    'dtbo_b', 'vendor_boot_b',
    'boot_a', 'vbmeta_a', 'vbmeta_system_a', 'vbmeta_vendor_a',
    'dtbo_a', 'vendor_boot_a',
]

PROPS = [
    'ro.product.model', 'ro.product.device', 'ro.board.platform',
    'ro.build.version.release', 'ro.build.version.incremental',
    'ro.boot.slot_suffix', 'ro.virtual_ab.enabled',
    'ro.boot.dynamic_partitions', 'ro.boot.verifiedbootstate',
    'ro.boot.flash.locked', 'ro.boot.vbmeta.avb_version',
    'ro.kernel.version', 'sys.boot_completed',
]


def adb(*args):
    return subprocess.run([ADB, *args], capture_output=True, timeout=300)


def prop(name):
    r = adb('shell', f'getprop {name}')
    return r.stdout.decode('utf-8', 'replace').strip()


def block_node(name):
    r = adb('shell', f"su -c 'readlink /dev/block/by-name/{name}'")
    node = r.stdout.decode('ascii', 'replace').strip().rsplit('/', 1)[-1]
    if not node:
        sys.exit(f'cannot resolve block node for {name}: {r.stdout!r} / {r.stderr!r}')
    return node


def kernel_size(dev):
    r = adb('shell', f"su -c 'cat /sys/class/block/{dev}/size'")
    txt = r.stdout.decode('ascii', 'replace').strip()
    if not txt.isdigit():
        sys.exit(f'cannot read size for {dev}: {txt!r} / {r.stderr!r}')
    return int(txt) * 512


def read_partition(name):
    """Read a partition and undo the channel's LF -> CRLF rewrite."""
    cmd = f"su -c 'dd if=/dev/block/by-name/{name} bs=4M 2>/dev/null'"
    r = adb('exec-out', cmd)
    return r.stdout.replace(b'\r\n', b'\n'), r.stderr


def read_base64(name):
    """Channel-independent read: encode on the phone, decode on the Mac."""
    cmd = (f"su -c 'dd if=/dev/block/by-name/{name} bs=4M 2>/dev/null "
           f"| base64 -w 0'")
    r = adb('exec-out', cmd)
    return base64.b64decode(b''.join(r.stdout.split()))


def hashes(data):
    return (hashlib.md5(data).hexdigest(), hashlib.sha256(data).hexdigest())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    devices = adb('devices', '-l').stdout.decode('utf-8', 'replace')
    lines = [l for l in devices.splitlines() if l.strip() and not l.startswith('List')]
    if not any('\tdevice' in l or ' device ' in l for l in lines):
        sys.exit('no authorized adb device connected:\n' + devices)
    print('device:', lines[0].strip())

    state = [
        'SukiSU-Ultra / camellian read-only device state snapshot',
        'captured: ' + datetime.now(timezone.utc).astimezone().isoformat(),
        'NOTHING ON THE PHONE WAS MODIFIED TO PRODUCE THIS FILE',
        '',
        '[adb devices -l]', devices.strip(), '',
        '[system properties]',
    ]
    for p in PROPS:
        state.append(f'{p} = {prop(p)}')
    state += ['', '[root context]']
    r = adb('shell', "su -c 'id'")
    state.append(r.stdout.decode('utf-8', 'replace').strip())
    state += ['', '[partition names]']
    r = adb('shell', "su -c 'ls -l /dev/block/by-name/'")
    state.append(r.stdout.decode('utf-8', 'replace').strip())
    (OUT / 'device-state-before.txt').write_text('\n'.join(state) + '\n')

    manifest = [
        'SukiSU-Ultra / camellian READ-ONLY PARTITION BACKUP MANIFEST',
        'captured: ' + datetime.now(timezone.utc).astimezone().isoformat(),
        'purpose: exact rollback of the current slot (boot_b / vbmeta_b),',
        '         plus related verification and device-tree partitions.',
        'transport note: adb exec-out rewrites 0x0A as 0x0D 0x0A (LF->CRLF).',
        '                Each image is restored by CRLF->LF reversal and is',
        '                REJECTED unless its length equals the kernel-reported',
        '                partition size (/sys/class/block/<dev>/size * 512).',
        '                Earlier truncated/raw copies were discarded as unsafe.',
        'Each partition was read twice and the restored payloads compared.',
        '',
    ]

    failures = []
    for name in PARTS:
        dev = block_node(name)
        size = kernel_size(dev)
        data1, err1 = read_partition(name)
        data2, err2 = read_partition(name)
        if len(data1) != size or len(data2) != size:
            failures.append(
                f'{name}: restored length {len(data1)}/{len(data2)} != kernel size {size}'
            )
            continue
        if data1 != data2:
            failures.append(f'{name}: the two independent reads differ')
            continue
        path = OUT / f'{name}-before.img'
        path.write_bytes(data1)
        md5, sha = hashes(data1)
        magic = data1[:8].hex()
        manifest.append(
            f'{name:20s} dev={dev:6s} size={size:>10d} '
            f'magic={magic}  md5={md5}  sha256={sha}'
        )
        print(f'  OK  {name:20s} {size:>10d} bytes  md5 {md5}')

    # Third, channel-independent witness for the single most important file.
    boot_path = OUT / 'boot_b-before.img'
    cross = 'NOT RUN (boot_b backup did not succeed)'
    if 'boot_b' not in ' '.join(failures) and boot_path.exists():
        try:
            witness = read_base64('boot_b')
            cross = 'MATCH' if witness == boot_path.read_bytes() else 'MISMATCH'
            if cross != 'MATCH':
                failures.append('boot_b: base64 witness does not match the saved image')
        except Exception as exc:                      # noqa: BLE001
            cross = 'ERROR: ' + str(exc)[:120]
            failures.append('boot_b: base64 witness failed: ' + str(exc)[:120])

    manifest += ['', f'boot_b base64 cross-check: {cross}',
                 'files: <name>-before.img in this directory',
                 'state snapshot: device-state-before.txt', '']
    if failures:
        manifest.append('FAILURES (do NOT use these files for rollback):')
        manifest += ['  ' + f[:200] for f in failures]
    else:
        manifest.append('RESULT: 12/12 partitions verified, nothing failed.')
    manifest += [
        '',
        'REMINDER: this backup is READ-ONLY evidence. Flashing anything back',
        'is a WRITE to the phone and still requires explicit user authorization.',
    ]
    (OUT / 'BACKUP-MANIFEST.txt').write_text('\n'.join(manifest) + '\n')
    print('\nmanifest ->', OUT / 'BACKUP-MANIFEST.txt')
    if failures:
        for f in failures:
            print('FAIL:', f)
        sys.exit(1)
    print('ALL PARTITIONS VERIFIED')


if __name__ == '__main__':
    main()
