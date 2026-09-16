#!/usr/bin/env python3
# Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠
# Provenance marker: sk-168bjwt
"""Transparent metadata triage. Scores do not measure expertise or substance."""
import argparse
import datetime
import math
from common import Error,dump_new,load,path,records,run

CFG={'target':28,'max_per_channel':3,'low_reach_ceiling':20000}


def date_of(value):
    try:return datetime.datetime.strptime(value,'%Y%m%d').date()
    except (TypeError,ValueError):return None


def score_all(cands):
    records({'candidates':cands},'candidates')
    ranked=[]
    for row in cands:
        views=row.get('view_count');likes=row.get('like_count');comments=row.get('comment_count')
        rate=(likes+3*comments)/views if views and likes is not None and comments is not None else None
        reach=min(12,math.log10(max(views or 0,1))*2)
        score=min(40,(rate or 0)*4000)+reach
        published=date_of(row.get('upload_date'))
        age=(datetime.date.today()-published).days if published else None
        ranked.append(dict(row,score=round(score,3),engagement_rate=rate,
                           bucket='unknown' if age is None else ('future_date' if age<0 else ('recent' if age<=365 else 'older')),
                           low_reach=views is not None and 0<views<=CFG['low_reach_ceiling'],
                           reasons=['Metadata triage only; review relevance, evidence and creator qualifications.',
                                    'Engagement unavailable.' if rate is None else 'Likes + 3× comments per view; arbitrary capped heuristic.']))
    return sorted(ranked,key=lambda x:(-x['score'],x['id']))


def select(scored,target,max_per_channel=3):
    chosen=[];counts={}
    for row in scored:
        if len(chosen)>=target:break
        ch=row.get('channel_id') or row.get('channel') or 'unknown-channel'
        if counts.get(ch,0)>=max_per_channel:continue
        counts[ch]=counts.get(ch,0)+1;chosen.append(row)
    return chosen


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('out_dir');p.add_argument('target',type=int,nargs='?',default=28)
    p.add_argument('--since',type=datetime.date.fromisoformat);p.add_argument('--max-per-channel',type=int,default=3);a=p.parse_args()
    if not 1<=a.target<=200 or not 1<=a.max_per_channel<=200:raise Error('count out of range')
    out=path(a.out_dir);data=load(out/'candidates.json');rows=records(data,'candidates');unknown=[]
    if a.since:
        unknown=[r['id'] for r in rows if date_of(r.get('upload_date')) is None]
        rows=[r for r in rows if date_of(r.get('upload_date')) and a.since<=date_of(r['upload_date'])<=datetime.date.today()]
    ranked=score_all(rows);chosen=select(ranked,a.target,a.max_per_channel)
    if not chosen:raise Error('no candidates selected; no selected.json written')
    result={'schema_version':1,'topic':data['topic'],'engine':data.get('engine'),'retrieved_at':data.get('retrieved_at'),
            'selected':chosen,'ranked_all':ranked,'requested':a.target,'unknown_date_excluded':unknown,
            'since':a.since.isoformat() if a.since else None,'status':'awaiting_content_review'}
    dump_new(out/'selected.json',result)
    return {'selected':len(chosen),'requested':a.target,'content_reviewed':False,'unknown_date_excluded':unknown}

if __name__=='__main__':raise SystemExit(run(main))
