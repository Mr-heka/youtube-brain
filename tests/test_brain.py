#!/usr/bin/env python3
# Provenance marker: sk-0dnoqd
# Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠
# Provenance marker: sk-168bjwt
"""Offline functional controls. No installed libraries, network or models touched."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import common, engine, discover, score, extract, build_brain, registry, verify
VID='abcdefghijk';OTHER='lmnopqrstuv'
VTT='WEBVTT\n\ncue-one\n00:00:01.000 --> 00:00:03.000\nKeep [context] &amp; test.\n\nNOTE metadata\nnot spoken\n\ncue-two\n00:00:03.000 --> 00:00:05.000\nNever assume causality.\n'


def row(vid=VID,**changes):
    return dict({'id':vid,'title':'Fictional trial | <script>x</script>','channel':'Fictional gardener','channel_id':'channel1','view_count':100,'like_count':10,'comment_count':0,'upload_date':'20260101','duration':90,'channel_subs':None},**changes)


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='brain-test-',dir=str(Path(tempfile.gettempdir()).resolve()))
        self.base=Path(self.temp.name);self.out=self.base/'run';self.out.mkdir()
        self.block=patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden'));self.block.start()
    def tearDown(self):self.block.stop();self.temp.cleanup()
    def call(self,module,args):
        with patch.object(sys,'argv',[module.__name__]+[str(v) for v in args]):return module.main()
    def prepare(self,rows=None):
        rows=rows or [row()]
        (self.out/'candidates.json').write_text(json.dumps({'topic':'seed trays','engine':'fixture','candidates':rows}))
        self.call(score,[self.out,5])
        vtt=self.out/'vtts';vtt.mkdir()
        for r in rows:(vtt/(r['id']+'.vtt')).write_text(VTT)
        self.call(extract,[self.out,'--vtt-dir',vtt])
        return self.out
    def build(self,**opts):
        target=self.base/opts.pop('name','brain-seed-trays')
        args=[self.out,'seed trays','--destination',target]
        for key,value in opts.items():args+=['--'+key.replace('_','-')]+([] if value is True else [value])
        self.call(build_brain,args);return target
    def fill(self,b):
        for f in [b/'SKILL.md',*(b/'references').glob('*.md')]:f.write_text(f.read_text().replace('<!-- FILL','Reviewed fixture only. <!-- REMOVED'))
        evidence={'source_reviews':{VID:{'disposition':'used','reason':'Read all two fictional cues; limited demonstration.'}},'claims':[{'id':'C1','statement':'The fictional speaker says to retain context.','kind':'source_report','citations':[{'source_id':VID,'cue_index':0}]}],
                  'quotes':[{'source_id':VID,'cue_index':0,'text':'Keep [context] & test.','verification':'caption_only'}],'reviewed_at':'2026-09-05'}
        (b/'evidence.json').write_text(json.dumps(evidence));return evidence
    def test_youtube_space_only_payload_lines(self):
        raw='WEBVTT\nKind: captions\n\n00:00:00.000 --> 00:00:02.000\n \nHello<c> world</c>\n\n00:00:02.000 --> 00:00:03.000\nHello world\n \n\n'
        cues=extract.parse_vtt(raw)
        self.assertEqual([c['text'] for c in cues],['Hello world','Hello world'])
        self.assertEqual(cues[1]['start'],2.0)
    def test_detect_never_installs_or_calls(self):
        with patch('shutil.which',return_value=None),patch('subprocess.run',side_effect=AssertionError('process forbidden')):
            self.assertFalse(engine.detect()['yt_dlp_installed'])
    def test_no_apify_fallback(self):
        with self.assertRaises(common.Error):engine.search('topic',1,'apify')
    def test_timeout_redacted(self):
        with patch('subprocess.run',side_effect=subprocess.TimeoutExpired('SECRET',2)):
            with self.assertRaisesRegex(common.Error,'timed out'):engine.ytdlp([])
    def test_failed_provider_output_redacted(self):
        with patch('subprocess.run',return_value=subprocess.CompletedProcess([],1,'SECRET','SECRET')):
            with self.assertRaises(common.Error) as c:engine.ytdlp([])
        self.assertNotIn('SECRET',str(c.exception))
    def test_ytdlp_args_do_not_load_config_cookie_plugins_or_remote_code(self):
        with patch('subprocess.run',return_value=subprocess.CompletedProcess([],0,'','')) as proc:engine.ytdlp(['--version'])
        args=proc.call_args.args[0]
        for flag in ('--ignore-config','--no-plugin-dirs','--no-remote-components','--no-cache-dir'):self.assertIn(flag,args)
        self.assertNotIn('--cookies-from-browser',args)
    def test_api_duration_and_caption_false_missing(self):
        for cap,expected in [('false',False),(None,None)]:
            cd={'duration':'PT1H2M3S'}
            if cap:cd['caption']=cap
            with patch.object(engine,'_api_get',return_value={'items':[{'id':VID,'snippet':{'title':'Fixture'},'contentDetails':cd}]}):
                r=engine.metadata([VID],'youtube_api')[0]
            self.assertEqual(r['duration'],3723);self.assertIs(r['has_captions'],expected);self.assertIsNone(r['like_count'])
    def test_api_error_does_not_print_key_url(self):
        with patch.dict(os.environ,{'YT_API_KEY':'FICTIONAL_SECRET'}),patch('urllib.request.urlopen',side_effect=OSError('FICTIONAL_SECRET')):
            with self.assertRaises(common.Error) as c:engine._api_get('videos',{})
        self.assertNotIn('FICTIONAL_SECRET',str(c.exception))
    def test_metadata_identity_mismatch(self):
        with patch.object(engine,'ytdlp',return_value=json.dumps({'id':OTHER})):
            with self.assertRaises(common.Error):engine.metadata([VID],'yt-dlp')
    def test_discovery_keeps_all_query_provenance(self):
        with patch.object(engine,'search',return_value=[{'id':VID}]),patch.object(engine,'metadata',return_value=[row()]):
            self.call(discover,['seed trays',self.out,1,'--engine','yt-dlp'])
        doc=common.load(self.out/'candidates.json');self.assertEqual(len(doc['candidates'][0]['found_via']),8)
    def test_partial_discovery_nonzero_with_evidence(self):
        with patch.object(engine,'search',side_effect=common.Error('failure')):
            with self.assertRaises(common.Error):self.call(discover,['seed trays',self.out,1,'--engine','yt-dlp'])
        self.assertEqual(len(common.load(self.out/'candidates.json')['failures']),8)
    def test_no_missing_metrics_as_hidden_gem(self):
        r=score.score_all([row(view_count=None,like_count=None,comment_count=None)])[0]
        self.assertIsNone(r['engagement_rate']);self.assertFalse(r['low_reach']);self.assertNotIn('expert', ' '.join(r['reasons']).lower())
    def test_invalid_numeric_metadata(self):
        for n in (-1,float('nan'),True):
            with self.assertRaises(common.Error):score.score_all([row(view_count=n)])
    def test_duplicate_id_refused(self):
        with self.assertRaises(common.Error):score.score_all([row(),row()])
    def test_since_unknown_and_future_not_new(self):
        rows=[row(),row(OTHER,upload_date=None),row('zyxwvutsrqp',upload_date='20990101')]
        (self.out/'candidates.json').write_text(json.dumps({'topic':'seed trays','candidates':rows}))
        self.call(score,[self.out,3,'--since','2026-01-01'])
        self.assertEqual([r['id'] for r in common.load(self.out/'selected.json')['selected']],[VID])
    def test_empty_and_negative_selection_no_output(self):
        (self.out/'candidates.json').write_text(json.dumps({'topic':'seed trays','candidates':[]}))
        for target in (0,2,-1):
            with self.assertRaises(common.Error):self.call(score,[self.out,target])
        self.assertFalse((self.out/'selected.json').exists())
    def test_channel_cap_and_deterministic_tie(self):
        rows=[row(vid) for vid in ('abcdefghijk','lmnopqrstuv','zyxwvutsrqp','ABCDEFGHIJK')]
        out=score.select(score.score_all(rows),10);self.assertEqual(len(out),3)
        self.assertEqual([r['id'] for r in out],sorted(r['id'] for r in rows)[:3])
    def test_vtt_keeps_timestamps_and_bracketed_words(self):
        cues=extract.parse_vtt(VTT);self.assertEqual(cues[0],{'start':1.0,'end':3.0,'text':'Keep [context] & test.'});self.assertEqual(len(cues),2)
    def test_vtt_invalid_and_short_valid(self):
        with self.assertRaises(common.Error):extract.parse_vtt('no captions')
        with self.assertRaises(common.Error):extract.parse_vtt(VTT.replace('00:00:03.000','00:00:00.000',1))
        self.assertEqual(len(extract.parse_vtt('WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nYes.\n')),1)
    def test_extract_missing_partial_and_stale_refused(self):
        (self.out/'selected.json').write_text(json.dumps({'selected':[row()]}));vtt=self.base/'vtts';vtt.mkdir()
        with self.assertRaises(common.Error):self.call(extract,[self.out,'--vtt-dir',vtt])
        self.assertEqual(common.load(self.out/'transcripts/_index.json')['sources'][VID]['status'],'unavailable')
        with self.assertRaises(FileExistsError):self.call(extract,[self.out,'--vtt-dir',vtt])
    def test_end_to_end_draft_truth_and_literal_metadata(self):
        self.prepare();(self.out/'transcripts/stale.txt').write_text('not selected')
        b=self.build();self.assertFalse((b/'sources/stale.txt').exists());m=common.load(b/'brain-manifest.json')
        self.assertEqual(m['status'],'draft');self.assertIsNone(m['last_synthesized'])
        self.assertIn('\\<script\\>',(b/'sources/sources-index.md').read_text())
        with self.assertRaisesRegex(common.Error,'unfilled'):verify.inspect(b)
        self.fill(b);self.assertEqual(verify.inspect(b)['status'],'local_evidence_checks_pass')
        self.assertEqual(common.load(b/'brain-manifest.json')['status'],'draft')
    def test_caption_hash_tamper_rejected(self):
        self.prepare();(self.out/'transcripts'/(VID+'.txt')).write_text('forged')
        with self.assertRaisesRegex(common.Error,'hash mismatch'):self.build()
        self.assertFalse((self.base/'brain-seed-trays').exists())
    def test_forged_quote_and_missing_source_rejected(self):
        self.prepare();b=self.build();e=self.fill(b);e['quotes'][0]['text']='invented quote';(b/'evidence.json').write_text(json.dumps(e))
        with self.assertRaisesRegex(common.Error,'literal span'):verify.inspect(b)
        e['quotes']=[];e['claims'][0]['citations'][0]['source_id']=OTHER;(b/'evidence.json').write_text(json.dumps(e))
        with self.assertRaises(common.Error):verify.inspect(b)
    def test_refresh_preserves_old_synthesis_and_dates(self):
        self.prepare();b=self.build();self.fill(b);before=(b/'references/synthesis.md').read_bytes()
        self.out=self.base/'run2';self.out.mkdir();self.prepare([row(OTHER)])
        new=self.build(name='brain-refresh',update_from=b)
        self.assertEqual((new/'references/synthesis.md').read_bytes(),before)
        m=common.load(new/'brain-manifest.json');self.assertEqual(len(m['sources']),2);self.assertEqual(m['status'],'draft_refresh');self.assertIsNone(m['last_synthesized'])
    def test_no_new_refresh_does_not_create(self):
        self.prepare();b=self.build()
        with self.assertRaisesRegex(common.Error,'no new sources'):self.build(name='repeat',update_from=b)
        self.assertFalse((self.base/'repeat').exists())
    def test_legacy_copy_keeps_content_but_cannot_pass(self):
        self.prepare();old=self.base/'legacy';old.mkdir();(old/'SKILL.md').write_text('Historical knowledge');(old/'references').mkdir();(old/'references/synthesis.md').write_text('Keep this old synthesis')
        with self.assertRaises(common.Error):self.build(update_from=old)
        b=self.build(update_from=old,legacy_copy=True)
        self.assertEqual((b/'references/synthesis.md').read_text(),'Keep this old synthesis')
        with self.assertRaisesRegex(common.Error,'legacy'):verify.inspect(b)
    def test_symlink_and_existing_output_preserved(self):
        self.prepare();existing=self.base/'occupied';existing.write_text('KEEP')
        with self.assertRaises(common.Error):self.build(name='occupied')
        link=self.base/'link';link.symlink_to(existing)
        with self.assertRaises(common.Error):common.write_new(link,'bad')
        self.assertEqual(existing.read_text(),'KEEP')
    def test_failed_write_cleans_new_draft(self):
        self.prepare()
        with patch.object(build_brain,'write_new',side_effect=OSError('disk')):
            with self.assertRaises(OSError):self.build()
        self.assertFalse((self.base/'brain-seed-trays').exists())
    def test_json_duplicates_nan_and_path_id(self):
        f=self.base/'bad.json'
        for value in ('{"x":1,"x":2}','{"x":NaN}'):
            f.write_text(value)
            with self.assertRaises(common.Error):common.load(f)
        with self.assertRaises(common.Error):common.video_id('../outside')
    def test_topic_yaml_injection_cannot_add_fields(self):
        self.prepare();doc=common.load(self.out/'selected.json');topic='seed "trays"\nmalicious: true';doc['topic']=topic;(self.out/'selected.json').write_text(json.dumps(doc))
        b=self.base/'safe';self.call(build_brain,[self.out,topic,'--destination',b]);fm=registry.frontmatter(b/'SKILL.md')
        self.assertEqual(fm['metadata']['topic'],topic);self.assertNotIn('malicious',fm)
    def test_registry_zero_sources_and_real_yaml_alias(self):
        b=self.base/'brain-test';b.mkdir();(b/'SKILL.md').write_text('---\nname: brain-test\nmetadata:\n  topic: seed trays\n  aliases: [seedling trays, garden starts]\n  sources: 50\n---\n')
        r=registry.scan(self.base)[0];self.assertEqual(r['sources'],0);self.assertIn('zero_sources',r['flags']);self.assertGreater(registry.overlap('seedling trays',r),0.6)
    def test_registry_duplicate_yaml_refused(self):
        f=self.base/'bad.md';f.write_text('---\nname: a\nname: b\n---\n')
        with self.assertRaises(common.Error):registry.frontmatter(f)
    def test_registry_missing_library_and_readonly_audit(self):
        with self.assertRaises(common.Error):registry.audit(self.base/'missing')
        before=set(self.base.iterdir());registry.audit(self.base);self.assertEqual(before,set(self.base.iterdir()))
    def test_maintenance_failure_nonzero_no_deletion(self):
        p=subprocess.run(['bash',str(ROOT/'scripts/maintain.sh'),str(self.base/'missing')],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertNotIn('healthy',p.stdout)
    def test_imports_no_files_created(self):
        before=set(self.base.rglob('*'))
        code='import sys;sys.dont_write_bytecode=True;sys.path.insert(0,sys.argv[1]);import engine,discover,score,extract,build_brain,registry,verify'
        p=subprocess.run([sys.executable,'-B','-c',code,str(ROOT/'scripts')],cwd=self.base,capture_output=True)
        self.assertEqual(p.returncode,0);self.assertEqual(set(self.base.rglob('*')),before)

    def test_concurrent_builds_do_not_overwrite(self):
        self.prepare();target=self.base/'race'
        args=[sys.executable,'-B',str(ROOT/'scripts/build_brain.py'),str(self.out),'seed trays','--destination',str(target)]
        procs=[subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
        results=[p.communicate() for p in procs]
        self.assertEqual(sorted(p.returncode for p in procs),[0,1])
        self.assertEqual(common.load(target/'brain-manifest.json')['status'],'draft')
    def test_legacy_source_index_preserved(self):
        self.prepare();old=self.base/'legacy';(old/'sources').mkdir(parents=True)
        (old/'SKILL.md').write_text('Old knowledge');(old/'sources/sources-index.md').write_text('Original creator/title provenance')
        b=self.build(update_from=old,legacy_copy=True)
        self.assertEqual((b/'history/legacy-sources-index.md').read_text(),'Original creator/title provenance')
    def test_topic_triple_dash_is_literal_yaml(self):
        f=self.base/'safe.md';f.write_text('---\nname: brain-test\nmetadata: {"topic":"one---two"}\n---\n')
        self.assertEqual(registry.frontmatter(f)['metadata']['topic'],'one---two')
    def test_vtt_invalid_minutes_rejected(self):
        with self.assertRaises(common.Error):extract.parse_vtt(VTT.replace('00:00:01.000','00:99:01.000'))
    def test_cli_bad_input_nonzero_json(self):
        p=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/build_brain.py'),str(self.out),'seed trays','--destination',str(self.base/'none')],capture_output=True,text=True)
        self.assertEqual(p.returncode,1);self.assertIn('error',json.loads(p.stderr));self.assertFalse((self.base/'none').exists())
    def test_registry_export_and_mirror_are_explicit_new_files(self):
        library=self.base/'library';library.mkdir();output=self.base/'index';mirror=self.base/'mirror.md'
        self.call(registry,['rebuild','--library',library,'--output',output,'--mirror',mirror])
        before=mirror.read_bytes();self.assertEqual(before,(output/'BRAINS-INDEX.md').read_bytes())
        with self.assertRaises(common.Error):self.call(registry,['rebuild','--library',library,'--output',self.base/'index2','--mirror',mirror])
        self.assertEqual(before,mirror.read_bytes());self.assertFalse((self.base/'index2').exists())

    def test_raw_caption_bytes_and_digest_preserved(self):
        f=self.base/'crlf.vtt';raw=VTT.replace('\n','\r\n').encode();f.write_bytes(raw)
        self.assertEqual(common.read_text(f).encode(),raw)
        self.assertEqual(common.digest(f),hashlib.sha256(raw).hexdigest())

    def test_vtt_control_prefix_ids_preserve_qualification_through_verification(self):
        header='WEBVTT Fictional test\n\nNOTE metadata\nnot spoken\n\nNOTE\nnot spoken either\n\nNOTE\tmetadata\nalso not spoken\n\nSTYLE\n::cue { color: red; }\n\nREGION\nid:fiction\n\n'
        labels=('NOTEBOOK','STYLEguide','REGIONA','WEBVTT-cue','STYLE','REGION')
        raw=header+''.join(f'{label}\n00:00:{i+1:02}.000 --> 00:00:{i+2:02}.000\nDo not use on food crops.\n\n' for i,label in enumerate(labels))
        raw+='plain\n00:00:07.000 --> 00:00:08.000\nApply the mixture.\n'
        for newline in ('\n','\r\n','\r'):
            self.assertEqual(len(extract.parse_vtt(raw.replace('\n',newline))),7)
        with self.assertRaises(common.Error):extract.parse_vtt(raw.replace('WEBVTT Fictional test','WEBVTT-invalid',1))
        raw=raw.replace('\n','\r')  # Exercise real CLI/raw-byte preservation for CR too.
        (self.out/'selected.json').write_text(json.dumps({'topic':'seed trays','selected':[row()]}))
        vtt=self.base/'vtt';vtt.mkdir();(vtt/(VID+'.vtt')).write_text(raw)
        p=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/extract.py'),str(self.out),'--vtt-dir',str(vtt)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        b=self.build();e=self.fill(b)
        e['claims'][0]['statement']='The fictional caption prohibits use on food crops.'
        e['quotes'][0]['text']='Do not use on food crops.'
        (b/'evidence.json').write_text(json.dumps(e))
        cues=common.load(b/'sources'/(VID+'.json'))['cues']
        self.assertEqual(len(cues),7);self.assertEqual(cues[0],{'start':1.0,'end':2.0,'text':'Do not use on food crops.'})
        self.assertEqual(cues[-1]['text'],'Apply the mixture.')
        self.assertEqual(common.read_text(b/'sources'/(VID+'.vtt')),raw)
        self.assertEqual(verify.inspect(b)['caption_spans'],1)

    def test_registry_cli_crlf_and_lf_equal_without_rewriting_source(self):
        b=self.base/'brain-fiction';b.mkdir()
        skill=b/'SKILL.md';raw='---\nname: brain-fiction\nmetadata:\n  topic: fiction\n---\n# Fiction\n'
        outputs=[]
        for newline in ('\n','\r\n'):
            original=raw.replace('\n',newline).encode();skill.write_bytes(original)
            p=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/registry.py'),'audit','--library',str(self.base)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr);outputs.append(json.loads(p.stdout))
            self.assertEqual(skill.read_bytes(),original)
            self.assertEqual(common.digest(skill),hashlib.sha256(original).hexdigest())
        self.assertEqual(outputs[0],outputs[1]);self.assertEqual(outputs[1]['total'],1)

if __name__=='__main__':unittest.main(verbosity=2)
