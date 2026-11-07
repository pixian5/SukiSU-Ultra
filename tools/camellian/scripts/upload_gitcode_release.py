#!/usr/bin/env python3
"""Upload one local artifact to a GitCode release (mirror of the GitHub release).

Credentials are NEVER stored here. The GitCode token is read at runtime from
``backup/HANDOFF-CREDENTIALS.txt`` (gitignored, mode 600). Nothing in this
script touches a phone.

Usage::

    python3 tools/camellian/scripts/upload_gitcode_release.py \
        --tag camellian-susfs-v0.0.6 \
        --file backup/camellian/boot-sukisu-susfs-v0.0.6.img \
        --asset-name boot-sukisu-susfs-lto-stockdtb.img \
        --name "camellian SuSFS v0.0.6" \
        --body-file /path/to/notes.md \
        --sha256sums

GitCode's release attachments require a presigned upload URL: first
``GET /releases/{tag}/upload_url?file_name=...``, then PUT the bytes to the
returned URL together with the returned headers. Anonymous downloads of
these attachments return 401 (login required), so GitHub stays the primary
download source.
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CRED = ROOT / 'backup' / 'HANDOFF-CREDENTIALS.txt'
API = 'https://gitcode.com/api/v5/repos/laotongtian/SukiSU-Ultra/releases'


def token() -> str:
    import re
    text = CRED.read_text()
    m = re.search(r'GITCODE_TOKEN\s*=\s*(\S+)', text)
    if not m:
        sys.exit('GitCode token missing from backup/HANDOFF-CREDENTIALS.txt')
    return m.group(1).strip()


def auth_headers(tok: str) -> dict:
    return {
        'Authorization': 'Bearer ' + tok,
        'Content-Type': 'application/json',
        'User-Agent': 'workbuddy-release-uploader',
    }


def call(method: str, url: str, tok: str, payload=None, raw=None, extra=None, timeout=300):
    headers = dict(auth_headers(tok) if not extra else extra)
    data = raw if raw is not None else (json.dumps(payload).encode() if payload is not None else None)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        return r.status, (json.loads(body) if body.startswith(b'{') or body.startswith(b'[') else body)


def ensure_release(tag: str, name: str, body: str, tok: str):
    try:
        status, d = call('POST', API, tok, {
            'tag_name': tag,
            'name': name,
            'body': body,
            'prerelease': True,
            'target_commitish': 'main',
        })
        print('release created:', tag, status)
    except urllib.error.HTTPError as e:
        msg = e.read().decode('utf-8', 'replace')[:200]
        if e.code in (400, 409, 422) and ('exist' in msg.lower() or 'already' in msg.lower() or '422' in msg):
            print('release already exists:', tag)
        else:
            sys.exit(f'cannot create release {tag}: HTTP {e.code}: {msg}')


def upload(tag: str, local: Path, asset_name: str, tok: str):
    q = urllib.parse.quote(asset_name, safe='')
    status, d = call('GET', f'{API}/{tag}/upload_url?file_name={q}', tok)
    if not isinstance(d, dict) or 'url' not in d:
        sys.exit(f'unexpected upload_url response: {str(d)[:200]}')
    headers = dict(d.get('headers') or {})
    headers.setdefault('Content-Type', 'application/octet-stream')
    data = local.read_bytes()
    headers['Content-Length'] = str(len(data))
    try:
        req = urllib.request.Request(d['url'], data=data, headers=headers, method='PUT')
        with urllib.request.urlopen(req, timeout=600) as r:
            print('uploaded:', asset_name, len(data), 'bytes, HTTP', r.status)
    except urllib.error.HTTPError as e:
        sys.exit(f'upload failed for {asset_name}: HTTP {e.code}: {e.read()[:200]!r}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True)
    ap.add_argument('--file', required=True, type=Path)
    ap.add_argument('--asset-name', default=None)
    ap.add_argument('--name', default=None)
    ap.add_argument('--body', default='')
    ap.add_argument('--body-file', type=Path, default=None)
    ap.add_argument('--sha256sums', action='store_true')
    a = ap.parse_args()

    if not a.file.is_absolute():
        a.file = ROOT / a.file
    if not a.file.is_file():
        sys.exit(f'no such file: {a.file}')
    asset = a.asset_name or a.file.name
    notes = a.body_file.read_text() if a.body_file else a.body
    tok = token()

    ensure_release(a.tag, a.name or a.tag, notes, tok)
    upload(a.tag, a.file, asset, tok)

    if a.sha256sums:
        digest = hashlib.sha256(a.file.read_bytes()).hexdigest()
        sums = ROOT / 'backup' / 'camellian' / f'SHA256SUMS-{a.tag}.txt'
        sums.write_text(f'{digest}  {asset}\n')
        upload(a.tag, sums, 'SHA256SUMS.txt', tok)
        print('SHA256', digest, 'written to', sums)


if __name__ == '__main__':
    main()
