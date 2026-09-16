#!/usr/bin/env python3
# Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠
# Provenance marker: sk-168bjwt
"""Check local evidence links and quotation spans; never certify factual truth."""
import argparse
import datetime
from common import Error,load,path,read_text,run,text_field,video_id
from build_brain import verify_source


def inspect(brain):
    b=path(brain);manifest=load(b/'brain-manifest.json');sources=manifest.get('sources')
    if not isinstance(sources,dict) or not sources:raise Error('no manifest sources')
    if manifest.get('legacy_unverified'):raise Error('legacy source migration/review remains unresolved')
    for vid,entry in sources.items():video_id(vid);verify_source(b/'sources',vid,entry)
    files=[b/'SKILL.md',*(b/'references').glob('*.md')]
    if any('<!-- FILL' in read_text(f) for f in files):raise Error('unfilled synthesis')
    for name in ('synthesis','quote-library','experts'):
        if len(read_text(b/'references'/(name+'.md')).strip())<30:raise Error('missing substantive reference text')
    evidence=load(b/'evidence.json')
    if not isinstance(evidence.get('claims'),list) or not evidence['claims']:raise Error('claim ledger required')
    if not isinstance(evidence.get('quotes'),list):raise Error('quote list required, may be empty')
    reviewed=evidence.get('source_reviews')
    if not isinstance(reviewed,dict) or set(reviewed)!=set(sources):raise Error('every source needs review disposition')
    for value in reviewed.values():
        if not isinstance(value,dict) or value.get('disposition') not in ('used','excluded'):
            raise Error('invalid source review')
        text_field(value.get('reason'),'source review reason')
    seen=set()
    for claim in evidence['claims']:
        cid=text_field(claim.get('id'),'claim id',80)
        if cid in seen:raise Error('duplicate claim ID')
        seen.add(cid);text_field(claim.get('statement'),'claim statement')
        if claim.get('kind') not in ('source_report','interpretation','contested'):raise Error('invalid claim kind')
        spans=claim.get('citations')
        if not isinstance(spans,list) or not spans:raise Error('claim citations required')
        for span in spans:
            vid=video_id(span.get('source_id'))
            if vid not in sources or reviewed[vid]['disposition']!='used':raise Error('claim uses absent or excluded source')
            cues=load(b/'sources'/(vid+'.json'))['cues'];i=span.get('cue_index')
            if isinstance(i,bool) or not isinstance(i,int) or not 0<=i<len(cues):raise Error('invalid cue locator')
    for quote in evidence['quotes']:
        vid=video_id(quote.get('source_id'));i=quote.get('cue_index');text=text_field(quote.get('text'),'quote')
        if vid not in sources or reviewed[vid]['disposition']!='used':raise Error('quote source absent or excluded')
        cues=load(b/'sources'/(vid+'.json'))['cues']
        if isinstance(i,bool) or not isinstance(i,int) or not 0<=i<len(cues) or text not in cues[i]['text']:raise Error('quote is not a literal span in cited cue')
        if quote.get('verification')!='caption_only':raise Error('helper only verifies caption spans, not audio accuracy')
    date=evidence.get('reviewed_at');text_field(date,'reviewed_at')
    try:review_date=datetime.date.fromisoformat(date)
    except ValueError:raise Error('invalid reviewed_at') from None
    if review_date>datetime.date.today():raise Error('future review date')
    return {'status':'local_evidence_checks_pass','sources':len(sources),'claims':len(seen),'caption_spans':len(evidence['quotes']),
            'manifest_status':manifest.get('status'),'limits':'Does not prove support, completeness, independence, audio accuracy, copyright permissions or current facts; no status/date mutated.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('brain');a=p.parse_args();return inspect(a.brain)

if __name__=='__main__':raise SystemExit(run(main))
