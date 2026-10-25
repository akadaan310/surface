from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

TOOL=Path(__file__).resolve().parents[1]/'tools/verify_repository.py'

class RepositoryManifestTests(unittest.TestCase):
    def test_exact_bytes_and_git_census_detect_tamper_and_omission(self):
        self.assertTrue(TOOL.exists(),'repository verifier must exist')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            subprocess.run(['git','init','-q',str(root)],check=True)
            (root/'source.bin').write_bytes(bytes(range(256)))
            subprocess.run(['git','-C',str(root),'add','source.bin'],check=True)
            def run(*extra):
                return subprocess.run([sys.executable,str(TOOL),'--root',str(root),*extra],capture_output=True,text=True)
            self.assertEqual(run('--write-manifest').returncode,0)
            self.assertEqual(run().returncode,0)
            (root/'source.bin').write_bytes(b'changed')
            self.assertNotEqual(run().returncode,0)
            (root/'source.bin').write_bytes(bytes(range(256)))
            manifest=root/'MANIFEST_SHA256.json';doc=json.loads(manifest.read_text());doc['files']=[];manifest.write_text(json.dumps(doc))
            self.assertNotEqual(run().returncode,0)

if __name__=='__main__':unittest.main()
