import copy,io,json,pathlib,shutil,tempfile,unittest,zipfile
from hal_core.contracts import inspect,ContractError
from hal_core.engine import run
from hal_core.ports import feature_status

ROOT=pathlib.Path(__file__).resolve().parents[1]
RESEARCH=ROOT/'fixtures/research'
RETURNS=ROOT/'fixtures/returns'

class HalContractTests(unittest.TestCase):
    def test_inspect_research(self):
        p=inspect(RESEARCH);self.assertEqual(p.manifest['id'],'research-diagnostics');self.assertIn('UNSIGNED_PACKAGE',p.warnings)
    def test_inspect_returns(self):
        self.assertEqual(inspect(RETURNS).manifest['id'],'returns-operations')
    def test_digests_different(self):
        self.assertNotEqual(inspect(RESEARCH).digest, inspect(RETURNS).digest)
    def test_zip(self):
        with tempfile.TemporaryDirectory() as td:
            dst=pathlib.Path(td)/'fixture.zip'
            with zipfile.ZipFile(dst,'w') as z:
                for p in RESEARCH.rglob('*'):
                    if p.is_file():z.write(p,p.relative_to(RESEARCH).as_posix())
            self.assertEqual(inspect(dst).digest,inspect(RESEARCH).digest)
    def _modified_manifest(self,edit):
        td=tempfile.TemporaryDirectory()
        base=pathlib.Path(td.name)/'pkg'
        shutil.copytree(RESEARCH,base)
        manifest=json.loads((base/'harness.json').read_text())
        edit(manifest)
        (base/'harness.json').write_text(json.dumps(manifest))
        return td,base
    def test_missing_readme(self):
        t,p=self._modified_manifest(lambda m:m.update(readme='missing.md'))
        with t,self.assertRaisesRegex(ContractError,'MISSING_REQUIRED_FILE'):inspect(p)
    def test_missing_skill(self):
        t,p=self._modified_manifest(lambda m:m.update(skills=['skills/bad/SKILL.md']))
        with t,self.assertRaisesRegex(ContractError,'MISSING_SKILL_FILE'):inspect(p)
    def test_permission_declined(self):
        t,p=self._modified_manifest(lambda m:m['permissions'].update(external_write='always'))
        with t,self.assertRaisesRegex(ContractError,'UNSAFE_PERMISSION_DECLARATION'):inspect(p)
    def test_secret_field(self):
        t,p=self._modified_manifest(lambda m:m.update(api_key='UNTRUSTED_STRING'))
        with t,self.assertRaisesRegex(ContractError,'SECRET_FIELD_IN_MANIFEST'):inspect(p)
    def test_duplicate_feature(self):
        t,p=self._modified_manifest(lambda m:m['features'].append(copy.deepcopy(m['features'][0])))
        with t,self.assertRaisesRegex(ContractError,'DUPLICATE_FEATURE_ID'):inspect(p)
    def test_invalid_zip_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            z=pathlib.Path(td)/'attack.zip'
            with zipfile.ZipFile(z,'w') as f:f.writestr('../escape.txt','BAD');f.writestr('harness.json','{}')
            with self.assertRaisesRegex(ContractError,'PATH_TRAVERSAL'):inspect(z)
    def test_invalid_zip_secret(self):
        with tempfile.TemporaryDirectory() as td:
            z=pathlib.Path(td)/'bad.zip'
            with zipfile.ZipFile(z,'w') as f:f.writestr('.env','SECRET');f.writestr('harness.json','{}')
            with self.assertRaisesRegex(ContractError,'POTENTIAL_SECRET_FILE'):inspect(z)
    def test_reject_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'pack';shutil.copytree(RESEARCH,p)
            (p/'evil').symlink_to('/etc/passwd')
            with self.assertRaisesRegex(ContractError,'SYMLINK_NOT_ALLOWED'):inspect(p)
    def test_missing_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ContractError,'MISSING_MANIFEST'):inspect(td)
    def test_port_local(self):
        x=feature_status(inspect(RESEARCH),'calculate-margin')
        self.assertEqual(x['status'],'AVAILABLE_CURATED_LOCAL')
    def test_port_no_model(self):
        x=feature_status(inspect(RESEARCH),'ai-interpretation')
        self.assertEqual(x['status'],'BLOCKED');self.assertIn('LLM_DIRECT:NO_PROVIDER',x['missing_ports'])
    def test_port_managed_agent(self):
        x=feature_status(inspect(RESEARCH),'ai-interpretation','manus')
        self.assertIn('MANAGED_AGENT_PORT_MISMATCH',x['missing_ports'])
    def test_port_unverified_not_active(self):
        x=feature_status(inspect(RESEARCH),'ai-interpretation','openai')
        self.assertEqual(x['status'],'BLOCKED');self.assertFalse(x['live_model_verified'])
    def test_port_unknown_domain(self):
        t,p=self._modified_manifest(lambda m:m.update(id='untrusted-copy'))
        with t:self.assertEqual(feature_status(inspect(p),'calculate-margin')['status'],'BLOCKED')
    def test_no_spoofed_local_port(self):
        t,p=self._modified_manifest(lambda m:m['features'][0].update(required_ports=['LOCAL_TRIAGE']))
        with t:self.assertEqual(feature_status(inspect(p),'calculate-margin')['status'],'BLOCKED')
    def test_research_real(self):
        x=run(RESEARCH,'calculate-margin',{'revenue':1500,'cost':900})
        self.assertEqual(x['status'],'SUCCESS');self.assertEqual(x['result']['margin_pct'],40)
        self.assertFalse(x['live_model_used']);self.assertFalse(x['external_writes'])
    def test_returns_real(self):
        x=run(RETURNS,'triage-return',{'condition':'sealed','proof':'yes','days':5})
        self.assertEqual(x['result']['classification'],'STANDARD_RETURN')
    def test_returns_negative(self):
        x=run(RETURNS,'triage-return',{'condition':'sealed','proof':'no','days':5})
        self.assertEqual(x['result']['classification'],'MANUAL_REVIEW')
    def test_invalid_revenue(self):
        x=run(RESEARCH,'calculate-margin',{'revenue':0,'cost':10})
        self.assertEqual(x['status'],'BLOCKED');self.assertNotIn('result',x)
    def test_nan_revenue(self):
        x=run(RESEARCH,'calculate-margin',{'revenue':float('nan'),'cost':10})
        self.assertEqual(x['status'],'BLOCKED')
    def test_negative_days(self):
        x=run(RETURNS,'triage-return',{'condition':'sealed','proof':'yes','days':-1})
        self.assertEqual(x['status'],'BLOCKED')
    def test_do_not_run_ai(self):
        x=run(RESEARCH,'ai-interpretation',{'prompt':'test'})
        self.assertEqual(x['status'],'BLOCKED');self.assertFalse(x['live_model_used'])
    def test_no_unknown_domain_exec(self):
        t,p=self._modified_manifest(lambda m:m.update(id='untrusted-copy'))
        with t:self.assertEqual(run(p,'calculate-margin',{'revenue':5,'cost':4})['status'],'BLOCKED')
    def test_secret_payload_blocked(self):
        x=run(RESEARCH,'calculate-margin',{'revenue':1500,'cost':900,'api_key':'any'})
        self.assertEqual(x['status'],'BLOCKED');self.assertNotIn('any',str(x))
    def test_extra_fields_blocked(self):
        x=run(RESEARCH,'calculate-margin',{'revenue':1500,'cost':900,'extra':1})
        self.assertEqual(x['status'],'BLOCKED')
    def test_tool_budget(self):
        x=run(RESEARCH,'calculate-margin',{'revenue':1500,'cost':900},max_tool_calls=2)
        self.assertEqual(x['status'],'BLOCKED')
    def test_untrusted_source_not_executed(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'pack';shutil.copytree(RESEARCH,p)
            # A malicious entrypoint file can be present; core never imports or executes it.
            (p/'main.py').write_text("raise RuntimeError('UNTRUSTED CODE EXECUTED')\n")
            x=run(p,'calculate-margin',{'revenue':1500,'cost':900})
            self.assertEqual(x['status'],'SUCCESS')
            self.assertNotIn('UNTRUSTED CODE EXECUTED',str(x))

if __name__=='__main__':unittest.main()
