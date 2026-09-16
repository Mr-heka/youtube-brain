# Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠
# Provenance marker: sk-0dnoqd
"""Offline wiki compilation fixtures. Not a YouTube knowledge-base trial."""
import copy
import json
import sys
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_brain as fixtures
VID=fixtures.VID
import build_wiki
from common import Error

class WikiControls(unittest.TestCase):
    setUp=fixtures.Controls.setUp
    tearDown=fixtures.Controls.tearDown
    call=fixtures.Controls.call
    prepare=fixtures.Controls.prepare
    build=fixtures.Controls.build
    fill=fixtures.Controls.fill
    def setup_wiki(self):
        self.prepare();b=self.build();self.fill(b)
        plan={'version':1,'purpose':'Fictional fixture, not editing expertise.','pages':[{'id':'context','title':'Context','question':'What does the fictional speaker recommend?','summary':'Keep context; the fixture does not establish causality.','claim_ids':['C1'],'application':'Retain the context in this fictional trial.','limits':'Only a fixture. No universal causal claim.','related':[]}], 'known_gaps':['No real editing knowledge.'], 'calibration':[{'question':'What evidence is missing?','expected_behavior':'State this is fictional.','page_ids':['context'],'status':'pending'}]}
        f=self.base/'plan.json';f.write_text(json.dumps(plan));return b,plan,f
    def test_explicit_discovery_queries_replace_defaults(self):
        with patch.object(fixtures.engine,'search',return_value=[{'id':VID}]) as search, patch.object(fixtures.engine,'metadata',return_value=[fixtures.row()]):
            self.call(fixtures.discover,['seed trays',self.out,'--engine','yt-dlp','--query','specific question','--query','specific question','--query','opposing advice'])
        self.assertEqual([c.args[0] for c in search.call_args_list],['specific question','opposing advice'])
        data=json.loads((self.out/'candidates.json').read_text())
        self.assertEqual(data['requested_queries'],['specific question','opposing advice'])
    def test_compile_preserves_sources_and_pending_status(self):
        b,p,f=self.setup_wiki();before=(b/'SKILL.md').read_bytes();dest=self.base/'wiki-copy'
        result=build_wiki.build(b,f,dest)
        self.assertFalse(result['calibrated']);self.assertEqual((b/'SKILL.md').read_bytes(),before)
        self.assertEqual((b/'sources'/(VID+'.vtt')).read_bytes(),(dest/'sources'/(VID+'.vtt')).read_bytes())
        self.assertIn('Known gaps',(dest/'index.md').read_text());self.assertIn('1.000–3.000s',(dest/'wiki/context.md').read_text())
        self.assertEqual(json.loads((b/'brain-manifest.json').read_text()),json.loads((dest/'brain-manifest.json').read_text()))
    def test_missing_claim_rejected(self):
        b,p,f=self.setup_wiki();p['pages'][0]['claim_ids']=['NOT-A-CLAIM']
        with self.assertRaisesRegex(Error,'claim IDs'):build_wiki.validate(b,p)
    def test_traversal_rejected(self):
        b,p,f=self.setup_wiki();p['pages'][0]['id']='../escape'
        with self.assertRaisesRegex(Error,'page id'):build_wiki.validate(b,p)
    def test_dangling_relation_rejected(self):
        b,p,f=self.setup_wiki();p['pages'][0]['related']=['absent']
        with self.assertRaisesRegex(Error,'related'):build_wiki.validate(b,p)
    def test_claimed_pass_without_answer_rejected(self):
        b,p,f=self.setup_wiki();p['calibration'][0]['status']='pass'
        with self.assertRaisesRegex(Error,'observed answer'):build_wiki.validate(b,p)
    def test_changed_source_rejected(self):
        b,p,f=self.setup_wiki();(b/'sources'/(VID+'.vtt')).write_text('changed')
        with self.assertRaisesRegex(Error,'hash'):build_wiki.validate(b,p)
    def test_nested_destination_rejected(self):
        b,p,f=self.setup_wiki()
        with self.assertRaisesRegex(Error,'outside'):build_wiki.build(b,f,b/'nested')
        self.assertFalse((b/'nested').exists())
    def test_existing_destination_preserved(self):
        b,p,f=self.setup_wiki();dest=self.base/'occupied';dest.mkdir();(dest/'keep').write_text('user file')
        with self.assertRaisesRegex(Error,'destination'):build_wiki.build(b,f,dest)
        self.assertEqual((dest/'keep').read_text(),'user file')
    def test_check_writes_nothing(self):
        b,p,f=self.setup_wiki();before=sorted(str(v) for v in self.base.rglob('*'))
        self.assertEqual(build_wiki.build(b,f)['status'],'wiki_plan_checks_pass')
        self.assertEqual(before,sorted(str(v) for v in self.base.rglob('*')))
    def test_existing_wiki_refuses_silent_refresh(self):
        b,p,f=self.setup_wiki();dest=self.base/'wiki-copy';build_wiki.build(b,f,dest)
        with self.assertRaisesRegex(Error,'existing wiki'):build_wiki.build(dest,f,self.base/'second')

if __name__=='__main__':
    unittest.main()
