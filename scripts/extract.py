#!/usr/bin/env python3
# Provenance marker: sk-pv8zap
# Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠
# Provenance marker: sk-168bjwt
"""Keep raw captions, timestamped cues and readable text with explicit coverage."""
import argparse
import html
import re
import tempfile
from common import Error,digest,dump_new,load,now,path,read_text,records,run,write_new
import engine

TIME = r'(?:\d{2,}:)?[0-5]\d:[0-5]\d\.\d{3}'


def seconds(value):
    parts=value.split(':')
    return sum(float(x)*60**i for i,x in enumerate(reversed(parts)))


def parse_vtt(raw):
    raw=raw.lstrip('\ufeff').replace('\r\n','\n').replace('\r','\n')
    blocks=re.split(r'\n\n+',raw)
    header=blocks.pop(0).splitlines()
    if not header or not re.fullmatch(r'WEBVTT(?:[ \t].*)?',header[0]):
        raise Error('not a WebVTT document')
    cues=[]
    for block in blocks:
        lines=block.strip().splitlines()
        if not lines:continue
        if re.fullmatch(r'NOTE(?:[ \t].*)?',lines[0]):continue
        if re.fullmatch(r'(?:STYLE|REGION)[ \t]*',lines[0]) and '-->' not in block:continue
        timing=0 if '-->' in lines[0] else 1
        if timing>=len(lines):raise Error('malformed VTT cue')
        m=re.fullmatch(rf'({TIME})\s+-->\s+({TIME})(?:\s+.*)?',lines[timing])
        if not m:raise Error('malformed VTT timing')
        start,end=map(seconds,m.groups())
        if end<=start or (cues and start<cues[-1]['start']):raise Error('invalid VTT timeline')
        # Keep square brackets (they may be spoken content); no rolling-word deletion.
        text=html.unescape(re.sub(r'<[^>]*>','', ' '.join(lines[timing+1:])))
        text=re.sub(r'\s+',' ',text).strip()
        if text:cues.append({'start':start,'end':end,'text':text})
    if not cues:raise Error('no nonempty timed cues')
    return cues


def clean_vtt(value):
    return '\n'.join(f"[{c['start']:.3f}–{c['end']:.3f}] {c['text']}" for c in parse_vtt(read_text(value)))+'\n'


def fetch(vid,language):
    with tempfile.TemporaryDirectory(prefix='brain-captions-') as td:
        args=['--skip-download','--no-playlist','--write-subs','--sub-langs',language,'--sub-format','vtt',
              '--ignore-no-formats-error','-o',td+'/%(id)s.%(ext)s','https://www.youtube.com/watch?v='+vid]
        # Human captions first; one bounded auto-caption fallback. No cookies or remote code.
        for automatic in (False,True):
            engine.ytdlp(args+(['--write-auto-subs'] if automatic else ['--no-write-auto-subs']),timeout=180)
            files=list(path(td).glob(vid+'.*.vtt'))
            if files:
                return read_text(sorted(files)[0]), 'automatic_or_supplied' if automatic else 'supplied_captions'
    raise Error('captions unavailable')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('out_dir')
    mode=p.add_mutually_exclusive_group(required=True);mode.add_argument('--fetch',action='store_true');mode.add_argument('--vtt-dir')
    p.add_argument('--language',default='en');a=p.parse_args()
    if not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]+)*',a.language):raise Error('invalid exact language code')
    out=path(a.out_dir);selected=records(load(out/'selected.json'),'selected')
    if not selected:raise Error('empty selection')
    local=path(a.vtt_dir) if a.vtt_dir else None
    tdir=out/'transcripts';tdir.mkdir()  # refuse stale directory, even if empty
    index={}
    for row in selected:
        vid=row['id']
        try:
            raw,kind=(read_text(local/(vid+'.vtt')),'local_import_unverified') if local else fetch(vid,a.language)
            cues=parse_vtt(raw)
            write_new(tdir/(vid+'.vtt'),raw);dump_new(tdir/(vid+'.json'),{'id':vid,'cues':cues})
            write_new(tdir/(vid+'.txt'),'\n'.join(f"[{c['start']:.3f}–{c['end']:.3f}] {c['text']}" for c in cues)+'\n')
            index[vid]={'status':'retrieved','caption_kind':kind,'language':a.language,'retrieved_at':now(),
                        'hashes':{ext:digest(tdir/(vid+ext)) for ext in ('.vtt','.json','.txt')},'cue_count':len(cues),
                        'attribution':'User-supplied file association; verify against source.' if local else 'URL ID requested; verify caption accuracy against video.'}
        except (Error,OSError,ValueError):
            index[vid]={'status':'unavailable','reason':'caption retrieval or parsing failed; details suppressed'}
    dump_new(tdir/'_index.json',{'schema_version':1,'sources':index})
    count=sum(r['status']=='retrieved' for r in index.values())
    if count!=len(selected):raise Error('partial or empty captions; inspect transcripts/_index.json')
    return {'retrieved':count,'selected':len(selected),'status':'captions_not_content_review'}

if __name__=='__main__':raise SystemExit(run(main))
