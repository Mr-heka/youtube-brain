#!/usr/bin/env python3
# Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠
# Provenance marker: sk-168bjwt
"""Local file/JSON boundaries shared by the brain tools. No import side effects."""
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile


class Error(Exception):
    pass


def run(fn):
    try:
        result = fn()
        if result is not None:
            print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (Error, OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        # Provider errors may contain request URLs/credentials; never print them.
        message = str(exc) if isinstance(exc, Error) else type(exc).__name__
        print(json.dumps({'error': message}), file=sys.stderr)
        return 1
    return 0


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def path(value):
    p = Path(os.path.abspath(os.path.expanduser(str(value))))
    if sys.platform == 'darwin':
        for alias in ('/tmp', '/var'):
            if str(p) == alias or str(p).startswith(alias+'/'):
                if Path(alias).is_symlink() and Path(alias).resolve() == Path('/private'+alias):
                    p = Path('/private'+str(p))
    for part in [p, *p.parents]:
        if part.is_symlink():
            raise Error('symlink path refused')
    return p


def read_text(value, limit=16_000_000):
    p = path(value)
    if not p.is_file() or p.stat().st_size > limit:
        raise Error('input missing, not a regular file, or over size limit')
    with p.open(encoding='utf-8', newline='') as stream:
        return stream.read()


def unique(pairs):
    result = {}
    for key, val in pairs:
        if key in result:
            raise Error('duplicate JSON key')
        result[key] = val
    return result


def load(value):
    def invalid(_):
        raise Error('non-finite JSON value')
    return json.loads(read_text(value), object_pairs_hook=unique, parse_constant=invalid)


def write_new(value, text):
    """Complete file publication without overwriting existing files or links."""
    p = path(value)
    if not p.parent.is_dir():
        raise Error('output parent must already exist')
    fd, tmp = tempfile.mkstemp(prefix='.brain-', dir=p.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text); f.flush(); os.fsync(f.fileno())
        os.link(tmp, p)  # exclusive, atomic publication
    finally:
        os.unlink(tmp)


def dump_new(value, data):
    write_new(value, json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def video_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}', value):
        raise Error('invalid YouTube video ID')
    return value


def text_field(value, name, maximum=5000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or '\x00' in value:
        raise Error('invalid '+name)
    return value.strip()


def records(data, field):
    if not isinstance(data, dict) or not isinstance(data.get(field), list):
        raise Error('invalid '+field+' document')
    rows = data[field]
    if len(rows) > 2000:
        raise Error('too many records')
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise Error('invalid record')
        vid = video_id(row.get('id'))
        if vid in seen:
            raise Error('duplicate video ID')
        seen.add(vid)
        text_field(row.get('title'), 'title')
        for key in ('view_count', 'like_count', 'comment_count', 'channel_subs', 'duration'):
            val = row.get(key)
            if val is not None and (isinstance(val, bool) or not isinstance(val, (float, int)) or not math.isfinite(val) or val < 0):
                raise Error('invalid numeric metadata')
    return rows


def digest(value):
    p = path(value)
    if not p.is_file() or p.stat().st_size > 16_000_000:
        raise Error('input missing, not regular, or over size limit')
    return hashlib.sha256(p.read_bytes()).hexdigest()


def md(value):
    """Escape source titles/metadata as literal inline Markdown."""
    s = str(value).replace('\n', ' ').replace('\r', ' ')
    return re.sub(r'([\\`*_[\]{}<>|#!])', r'\\\1', s)
