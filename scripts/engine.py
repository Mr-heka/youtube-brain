#!/usr/bin/env python3
# Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠
# Provenance marker: sk-168bjwt
"""Explicit public YouTube discovery adapters; detect never installs or calls a service."""
import argparse
import json
import os
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from common import Error, run, video_id

YTDLP_BASE = ['yt-dlp', '--ignore-config', '--no-plugin-dirs', '--no-cache-dir',
              '--no-remote-components', '--no-warnings', '--socket-timeout', '20',
              '--retries', '1', '--extractor-retries', '1']


def detect():
    return {'yt_dlp_installed': bool(shutil.which('yt-dlp')),
            'youtube_api_key_present': bool(os.environ.get('YT_API_KEY')),
            'apify': 'not implemented', 'network_checked': False,
            'note': 'Discovery and caption access require separate verification; nothing installed.'}


def ytdlp(args, timeout=120):
    try:
        r = subprocess.run(YTDLP_BASE+args, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        raise Error('yt-dlp unavailable or timed out') from None
    if r.returncode:
        raise Error('yt-dlp failed; output suppressed')
    if len(r.stdout) > 16_000_000:
        raise Error('yt-dlp output over limit')
    return r.stdout


def _api_get(endpoint, params):
    key = os.environ.get('YT_API_KEY')
    if not key:
        raise Error('YT_API_KEY required for explicitly selected youtube_api')
    params = dict(params, key=key)
    url = 'https://www.googleapis.com/youtube/v3/'+endpoint+'?'+urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            raw = response.read(16_000_001)
        if len(raw) > 16_000_000:
            raise ValueError()
        data = json.loads(raw)
        if not isinstance(data, dict) or 'error' in data:
            raise ValueError()
        return data
    except Exception:
        raise Error('YouTube API request failed; details suppressed') from None


def duration(value):
    m = re.fullmatch(r'P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?', value or '')
    if not m:
        return None
    return sum(float(v or 0)*factor for v, factor in zip(m.groups(), (86400, 3600, 60, 1)))


def search(query, n, engine):
    if engine == 'yt-dlp':
        return [json.loads(line) for line in ytdlp(['--flat-playlist', '--dump-json', f'ytsearch{n}:{query}']).splitlines() if line.strip()]
    if engine == 'youtube_api':
        data = _api_get('search', {'part':'snippet', 'q':query, 'type':'video', 'maxResults':n})
        return [{'id':x['id']['videoId'], 'title':x['snippet']['title']} for x in data.get('items', [])]
    raise Error('unsupported engine')


def metadata(ids, engine):
    ids = [video_id(v) for v in ids]
    if engine == 'yt-dlp':
        rows = []
        for vid in ids:
            d = json.loads(ytdlp(['--dump-single-json', '--skip-download', '--no-playlist', 'https://www.youtube.com/watch?v='+vid]))
            if d.get('id') != vid:
                raise Error('metadata video identity mismatch')
            rows.append({'id':vid, 'title':d.get('title'), 'channel':d.get('channel') or d.get('uploader'),
                         'channel_id':d.get('channel_id'), 'channel_subs':d.get('channel_follower_count'),
                         **{k:d.get(k) for k in ('view_count','like_count','comment_count','upload_date','duration')},
                         'description':(d.get('description') or '')[:5000],
                         'has_captions':bool(d.get('subtitles') or d.get('automatic_captions'))})
        return rows
    if engine != 'youtube_api':
        raise Error('unsupported engine')
    rows = []
    for i in range(0,len(ids),50):
        data = _api_get('videos', {'part':'snippet,statistics,contentDetails','id':','.join(ids[i:i+50])})
        for item in data.get('items', []):
            sn, st, cd = (item.get(k,{}) for k in ('snippet','statistics','contentDetails'))
            vid = video_id(item.get('id'))
            if vid not in ids[i:i+50]:
                raise Error('metadata video identity mismatch')
            rows.append({'id':vid,'title':sn.get('title'),'channel':sn.get('channelTitle'),'channel_id':sn.get('channelId'),
                         'channel_subs':None, 'view_count':int(st['viewCount']) if 'viewCount' in st else None,
                         'like_count':int(st['likeCount']) if 'likeCount' in st else None,
                         'comment_count':int(st['commentCount']) if 'commentCount' in st else None,
                         'upload_date':(sn.get('publishedAt') or '')[:10].replace('-','') or None,
                         'duration':duration(cd.get('duration')), 'has_captions':{'true':True,'false':False}.get(cd.get('caption')),
                         'description':sn.get('description','')[:5000]})
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('command',choices=['detect']);p.parse_args()
    return detect()

if __name__ == '__main__':
    raise SystemExit(run(main))
