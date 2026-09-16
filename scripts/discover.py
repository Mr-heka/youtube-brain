#!/usr/bin/env python3
# Provenance marker: sk-pv8zap
# Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠
# Provenance marker: sk-168bjwt
"""Discover metadata for review, not a certified list of experts."""
import argparse
from common import Error, dump_new, now, path, records, run, text_field, video_id
import engine

ANGLES = ['{t}', '{t} tutorial', 'how to {t}', '{t} mistakes', '{t} framework', '{t} explained', 'advanced {t}', '{t} strategy']


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('topic');p.add_argument('out_dir');p.add_argument('per_angle',type=int,nargs='?',default=10)
    p.add_argument('--engine',required=True,choices=['yt-dlp','youtube_api']);p.add_argument('--query',action='append',help='Explicit decision-led query; repeat to replace generic discovery angles');a=p.parse_args()
    topic=text_field(a.topic,'topic',300);out=path(a.out_dir)
    if not out.is_dir() or (out/'candidates.json').exists() or not 1<=a.per_angle<=50:
        raise Error('use an existing output directory without candidates.json and per_angle 1..50')
    queries=[text_field(q,'query',500) for q in a.query] if a.query else [angle.format(t=topic) for angle in ANGLES]
    queries=list(dict.fromkeys(queries))
    if not 1<=len(queries)<=30:raise Error('use 1..30 unique discovery queries')
    requested_queries=list(queries)
    found={};failures=[]
    for query in queries:
        try:
            for row in engine.search(query,a.per_angle,a.engine):
                vid=video_id(row.get('id'));found.setdefault(vid,[]).append(query)
        except (Error,ValueError,KeyError,TypeError):
            failures.append({'stage':'search','query':query})
    rows=[]
    for vid,queries in found.items():
        try:
            meta=engine.metadata([vid],a.engine)
            records({'candidates':meta},'candidates')
            if len(meta)!=1 or meta[0]['id']!=vid:raise Error('missing metadata')
            rows.append(dict(meta[0],found_via=queries,url='https://www.youtube.com/watch?v='+vid))
        except (Error,ValueError,KeyError,TypeError):failures.append({'stage':'metadata','id':vid})
    result={'schema_version':1,'topic':topic,'engine':a.engine,'requested_queries':requested_queries,'retrieved_at':now(),'candidates':rows,'failures':failures,'status':'partial' if failures else 'retrieved'}
    dump_new(out/'candidates.json',result)
    if not rows or failures:
        raise Error('discovery empty or partial; inspect candidates.json before deciding whether to continue')
    return {'candidates':len(rows),'status':'metadata_only','file':str(out/'candidates.json')}

if __name__ == '__main__':raise SystemExit(run(main))
