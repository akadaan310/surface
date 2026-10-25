"""Portable generator packages preserve source/code bytes and run without the repo."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class GeneratorPackageTests(unittest.TestCase):
    def build_protocol(self, root):
        out=root/'package'
        built=subprocess.run([sys.executable,'-B',str(ROOT/'tools/build_generator_package.py'),
            '--card',str(ROOT/'examples/generators/protocol.card.json'),'--output',str(out)],capture_output=True,text=True,timeout=15)
        self.assertEqual(built.returncode,0,built.stdout+built.stderr)
        return out,json.loads(built.stdout)['manifest_sha256']

    def check_package(self, out, digest, timeout=15):
        return subprocess.run([sys.executable,'-I','-B',str(ROOT/'tools/verify_generator_package.py'),
            '--package',str(out),'--manifest-sha256',digest],capture_output=True,text=True,timeout=timeout)

    def test_source_locked_package_runs_and_detects_modified_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);card=root/'card.json';out=root/'portable'
            card.write_text(json.dumps({'schema':'polyia.generator-card/0.1','id':'two-rational-exercises','version':'1.0.0',
                'family':'polynomial-division','coefficient_choices':['1/2','3/2'],'divisor':['-1','1'],
                'quotient_degree':0,'seed':0,'bounds':{'work_units':10000,'max_candidates':64}}))
            built=subprocess.run([sys.executable,'-B',str(ROOT/'tools/build_generator_package.py'),'--card',str(card),'--output',str(out)],cwd=root,capture_output=True,text=True,timeout=15)
            self.assertEqual(built.returncode,0,built.stderr+built.stdout)
            receipt=json.loads(built.stdout);manifest_hash=receipt['manifest_sha256']
            moved=root/'independent';shutil.move(out,moved)
            verifier=ROOT/'tools/verify_generator_package.py'
            check=subprocess.run([sys.executable,'-I','-B',str(verifier),'--package',str(moved),'--manifest-sha256',manifest_hash],cwd=root,capture_output=True,text=True,timeout=15)
            self.assertEqual(check.returncode,0,check.stdout+check.stderr)
            self.assertEqual(json.loads(check.stdout)['status'],'PASS')
            manifest=json.loads((moved/'MANIFEST.json').read_text())
            for row in manifest['files']:
                data=(moved/row['path']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'])
            self.assertTrue(any(row['path'].startswith('sources/') for row in manifest['files']))
            (moved/'runtime.py').write_bytes((moved/'runtime.py').read_bytes()+b'\n# drift\n')
            bad=subprocess.run([sys.executable,'-I','-B',str(verifier),'--package',str(moved),'--manifest-sha256',manifest_hash],cwd=root,capture_output=True,text=True,timeout=15)
            self.assertNotEqual(bad.returncode,0)
            self.assertEqual(json.loads(bad.stdout)['status'],'FAIL')

    def test_candidate_verifier_is_never_executed_before_trust_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'package';marker=root/'candidate-executed'
            built=subprocess.run([sys.executable,'-B',str(ROOT/'tools/build_generator_package.py'),
                '--card',str(ROOT/'examples/generators/protocol.card.json'),'--output',str(out)],capture_output=True,text=True,timeout=15)
            self.assertEqual(built.returncode,0,built.stdout+built.stderr)
            digest=json.loads(built.stdout)['manifest_sha256']
            (out/'verify.py').write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("executed")\nprint(\'{"status":"PASS"}\')\n')
            result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'tools/verify_generator_package.py'),
                '--package',str(out),'--manifest-sha256',digest],capture_output=True,text=True,timeout=15)
            self.assertNotEqual(result.returncode,0)
            self.assertTrue(result.stdout.strip(),'Trusted checker must return a structured refusal')
            self.assertEqual(json.loads(result.stdout)['status'],'FAIL')
            self.assertFalse(marker.exists())

    def assert_fifo_refused(self, filename):
        with tempfile.TemporaryDirectory() as tmp:
            out,digest=self.build_protocol(Path(tmp));target=out/filename
            target.unlink();os.mkfifo(target)
            try: result=self.check_package(out,digest,timeout=1)
            except subprocess.TimeoutExpired:self.fail('Checker blocked opening a FIFO before file admission')
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(json.loads(result.stdout)['status'],'FAIL')

    def test_manifest_fifo_is_refused_without_blocking(self):
        self.assert_fifo_refused('MANIFEST.json')

    def test_listed_payload_fifo_is_refused_without_blocking(self):
        self.assert_fifo_refused('model.json')

    def test_matching_manifest_does_not_authorize_unregistered_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out,digest=self.build_protocol(root);marker=root/'runtime-executed'
            expected=(out/'expected.json').read_text()
            hostile=('from pathlib import Path\nPath('+repr(str(marker))+').write_text("ran")\nprint('+repr(expected)+')\n').encode()
            (out/'runtime.py').write_bytes(hostile)
            manifest=json.loads((out/'MANIFEST.json').read_text())
            digest_runtime=hashlib.sha256(hostile).hexdigest();manifest['runtime_sha256']=digest_runtime
            for row in manifest['files']:
                if row['path']=='runtime.py':row.update(sha256=digest_runtime,bytes=len(hostile))
            raw=json.dumps(manifest,sort_keys=True).encode();(out/'MANIFEST.json').write_bytes(raw)
            result=self.check_package(out,hashlib.sha256(raw).hexdigest())
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(json.loads(result.stdout)['status'],'FAIL')
            self.assertFalse(marker.exists())

    def test_builder_refuses_existing_output_without_mutating_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'portable';out.mkdir();(out/'sentinel').write_text('keep')
            card=root/'card.json';card.write_text('{}')
            built=subprocess.run([sys.executable,'-B',str(ROOT/'tools/build_generator_package.py'),'--card',str(card),'--output',str(out)],capture_output=True,text=True,timeout=15)
            self.assertNotEqual(built.returncode,0)
            self.assertEqual((out/'sentinel').read_text(),'keep')
            self.assertEqual([p.name for p in out.iterdir()],['sentinel'])

    def test_changed_documentary_source_refuses_before_creating_package(self):
        tool=ROOT/'tools/build_generator_package.py'
        self.assertTrue(tool.exists())
        spec=importlib.util.spec_from_file_location('generator_packager_under_test',tool)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'polyia').mkdir();(root/'tools').mkdir()
            shutil.copyfile(ROOT/'tools/verify_generator_package.py',root/'tools/verify_generator_package.py')
            shutil.copyfile(ROOT/'polyia/generators.py',root/'polyia/generators.py')
            for source,_,_ in module.generators.SOURCES:
                target=root/source;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/source,target)
            damaged=root/module.generators.SOURCES[0][0]
            damaged.write_bytes(damaged.read_bytes()+b'\nchanged source\n')
            module.ROOT=root
            card={'schema':'polyia.generator-card/0.1','id':'tiny','version':'1.0.0','family':'regular',
                  'alphabet':['A'],'grammar':{'op':'token','token':'A'},'seed':0,'bounds':{'work_units':100,'max_candidates':2}}
            with self.assertRaisesRegex(ValueError,'Pinned source changed'):
                module.build_package(card,root/'portable')
            self.assertFalse((root/'portable').exists())


if __name__=='__main__':unittest.main()
