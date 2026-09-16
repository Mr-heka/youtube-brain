#!/usr/bin/env python3
# Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠
# Provenance marker: sk-168bjwt
"""Read a chosen library; indexes are derived exports, not canonical knowledge."""
import argparse
import datetime
import os
import re
from common import Error,dump_new,load,md,path,read_text,run,write_new

STOP=set('a an and are as at be by for from has how in is it of on or the this that to vs with your you what when why expert brain use using user skill'.split())


def _words(value):
    return {w for w in re.findall(r'[a-z0-9]+',value.lower()) if len(w)>2 and w not in STOP}


def frontmatter(value):
    import yaml
    # Reject duplicate YAML keys; a later field must not silently override earlier data.
    class Loader(yaml.SafeLoader):pass
    def mapping(loader,node):
        result={}
        for k,v in node.value:
            key=loader.construct_object(k)
            if key in result:raise Error('duplicate YAML key')
            result[key]=loader.construct_object(v,deep=True)
        return result
    Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,mapping)
    # Normalize only the parser view; raw caption bytes and hashes stay untouched.
    text=read_text(value).replace('\r\n','\n').replace('\r','\n')
    match=re.match(r'^---\n(.*?)\n---(?:\n|$)',text,re.S)
    if not match:raise Error('missing YAML frontmatter')
    try:data=yaml.load(match.group(1),Loader=Loader)
    except yaml.YAMLError:raise Error('invalid YAML frontmatter') from None
    if not isinstance(data,dict):raise Error('invalid frontmatter mapping')
    return data


def scan(library):
    root=path(library)
    if not root.is_dir():raise Error('library directory missing')
    brains=[]
    for folder in sorted(root.glob('brain-*')):
        path(folder)
        if not folder.is_dir():continue
        fm=frontmatter(folder/'SKILL.md');meta=fm.get('metadata',{})
        if not isinstance(meta,dict):raise Error('metadata must be a mapping')
        topic=meta.get('topic',fm.get('topic',folder.name[6:]))
        aliases=meta.get('aliases',fm.get('aliases',[]))
        if isinstance(aliases,str):aliases=[aliases]
        if not isinstance(topic,str) or not isinstance(aliases,list) or any(not isinstance(v,str) for v in aliases):raise Error('invalid topic or aliases')
        src=folder/'sources';n=0
        if src.exists():
            path(src)
            for f in src.glob('*.txt'):
                read_text(f);n+=1
        unfilled=sum(read_text(f).count('<!-- FILL') for f in [folder/'SKILL.md',*(folder/'references').glob('*.md')])
        manifest=load(folder/'brain-manifest.json') if (folder/'brain-manifest.json').exists() else None
        status=manifest.get('status','unknown') if manifest else 'legacy_unverified'
        touch=manifest.get('last_synthesized') if manifest else None
        flags=[]
        if status!='reviewed':flags.append(status)
        if unfilled:flags.append('unfilled')
        if n==0:flags.append('zero_sources')
        if not touch:flags.append('synthesis_date_unknown')
        else:
            try:
                date=datetime.date.fromisoformat(touch[:10]);age=(datetime.date.today()-date).days
                if age<0:flags.append('future_synthesis_date')
                elif age>180:flags.append('age_review_suggested')
            except (TypeError,ValueError):flags.append('invalid_synthesis_date')
        brains.append({'slug':folder.name,'topic':topic,'aliases':aliases,'angle':str(meta.get('angle','')),'domain':str(meta.get('domain','')),
                       'sources':n,'declared_sources':meta.get('sources'),'unfilled':unfilled,'status':status,'last_synthesized':touch,
                       'flags':flags,'load':str(folder/'SKILL.md'),'keywords':sorted(_words(topic+' '+' '.join(aliases)+' '+folder.name))})
    return brains


def overlap(query,row):
    a=_words(query);b=set(row['keywords'])
    return round(len(a&b)/min(len(a),len(b)),3) if a and b else 0


def audit(library):
    rows=scan(library)
    return {'total':len(rows),'refresh_queue':[r for r in rows if r['flags']],
            'no_structural_flags':[r['slug'] for r in rows if not r['flags']],
            'note':'Structure and dates only; no factual accuracy, source quality or live freshness proof.'}


def consolidate(library):
    rows=scan(library);pairs=[]
    for i,a in enumerate(rows):
        for b in rows[i+1:]:
            score=overlap(a['topic']+' '+' '.join(a['aliases']),b)
            if score>=0.6:pairs.append({'a':a['slug'],'b':b['slug'],'overlap':score,'different_angles':bool(a['angle'] and b['angle'] and a['angle']!=b['angle'])})
    return {'merge_candidates':pairs,'note':'Keyword suggestions only. Different angles are review context, not a permanent exemption. No merge or deletion performed.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['check','related','for-task','audit','consolidate','rebuild'])
    p.add_argument('query',nargs='?');p.add_argument('--library',default=os.environ.get('BRAIN_SKILLS_DIR'));p.add_argument('--output');p.add_argument('--mirror')
    a=p.parse_args()
    if not a.library:raise Error('explicit --library or BRAIN_SKILLS_DIR required')
    if a.command=='audit':return audit(a.library)
    if a.command=='consolidate':return consolidate(a.library)
    rows=scan(a.library)
    if a.command=='rebuild':
        if not a.output:raise Error('rebuild requires new --output directory; installed indexes are not overwritten')
        out=path(a.output)
        if out.exists() or not out.parent.is_dir():raise Error('index output must be new')
        text='# Brain index export\n\nDerived from the explicitly selected library; content needs independent review.\n\n| Brain | Topic | Status | Actual transcripts |\n| --- | --- | --- | --- |\n'
        text+='\n'.join(f"| {md(r['slug'])} | {md(r['topic'])} | {md(r['status'])} | {r['sources']} |" for r in rows)+'\n'
        mirror=path(a.mirror) if a.mirror else None
        if mirror and (mirror.exists() or not mirror.parent.is_dir()):raise Error('mirror must be a new file with existing parent')
        out.mkdir();dump_new(out/'brains-index.json',{'brains':rows,'count':len(rows)});write_new(out/'BRAINS-INDEX.md',text)
        if mirror:write_new(mirror,text)
        return {'count':len(rows),'output':str(out),'mirror':str(mirror) if mirror else None}
    if not a.query:raise Error('query required')
    hits=[dict(r,overlap=overlap(a.query,r)) for r in rows]
    hits=sorted((r for r in hits if r['overlap']>=0.2),key=lambda r:(-r['overlap'],r['slug']))[:5]
    return {'query':a.query,'matches':hits,'load_brains':hits[:3] if a.command=='for-task' else [],
            'verdict':'possible_update' if hits and hits[0]['overlap']>=0.6 else ('adjacent' if hits else 'no_keyword_match'),
            'advice':'Inspect scope, sources and current primary evidence. Matching words do not authorize merge, creation or execution.'}

if __name__=='__main__':raise SystemExit(run(main))
