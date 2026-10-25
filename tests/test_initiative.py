import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL=Path(__file__).resolve().parents[1]/'tools/new_initiative.py'

class InitiativeTests(unittest.TestCase):
    def tool(self):
        spec=importlib.util.spec_from_file_location('initiative_under_test',TOOL)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def fixture(self,root):
        repo=root/'repo';repo.mkdir()
        def git(*args):
            return subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True,check=True).stdout.strip()
        git('init','-b','main');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid')
        (repo/'README.md').write_text('baseline\n')
        return repo,git

    def test_new_path_pins_base_and_refuses_collision_without_overwrite(self):
        self.assertTrue(TOOL.exists(), 'initiative helper must exist')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);repo=root/'repo';repo.mkdir()
            def git(*args):
                return subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True,check=True).stdout.strip()
            git('init','-b','main');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid')
            (repo/'README.md').write_text('baseline\n');git('add','README.md');git('commit','-m','baseline');base=git('rev-parse','HEAD')
            target=root/'worktrees'/'quantum-fixture'
            args=[sys.executable,str(TOOL),'quantum-fixture','--repo',str(repo),'--base',base,'--path',str(target)]
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            state=json.loads((target/'initiatives/quantum-fixture/INITIATIVE.json').read_text())
            self.assertEqual(state['base_commit'],base)
            self.assertEqual(state['branch'],'initiative/quantum-fixture')
            self.assertEqual(git('rev-parse','HEAD'),base)
            second=subprocess.run(args,capture_output=True,text=True)
            self.assertNotEqual(second.returncode,0)
            self.assertEqual((target/'README.md').read_text(),'baseline\n')
            bad=subprocess.run([sys.executable,str(TOOL),'../escape','--repo',str(repo),'--base',base,'--path',str(root/'escape')],capture_output=True,text=True)
            self.assertNotEqual(bad.returncode,0)
            self.assertFalse((root/'escape').exists())

    def test_tracked_record_prompt_and_directory_symlinks_cannot_write_outside(self):
        tool=self.tool()
        for kind in ('record','prompt','initiative-directory','initiatives-directory'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
                root=Path(d);repo,git=self.fixture(root);outside=root/'outside';outside.mkdir()
                directory=repo/'initiatives'/'fixture'
                if kind=='initiatives-directory':
                    (repo/'initiatives').symlink_to(outside,target_is_directory=True)
                elif kind=='initiative-directory':
                    directory.parent.mkdir();directory.symlink_to(outside,target_is_directory=True)
                else:
                    directory.mkdir(parents=True)
                    name='INITIATIVE.json' if kind=='record' else 'SELF_PROMPT.md'
                    (directory/name).symlink_to(outside/'escaped-file')
                git('add','.');git('commit','-m','symlink fixture');base=git('rev-parse','HEAD')
                with self.assertRaisesRegex(ValueError,'linked'):
                    tool.create('fixture',repo,base,root/'worktree')
                self.assertEqual(list(outside.iterdir()),[])
                self.assertEqual(git('rev-parse','HEAD'),base)
                self.assertEqual(git('status','--porcelain'),'')

    def test_destination_ancestor_symlink_is_refused_before_worktree_creation(self):
        tool=self.tool()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);repo,git=self.fixture(root);git('add','.');git('commit','-m','baseline')
            outside=root/'outside';outside.mkdir();alias=root/'alias';alias.symlink_to(outside,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'linked'):
                tool.create('fixture',repo,git('rev-parse','HEAD'),alias/'worktree')
            self.assertEqual(list(outside.iterdir()),[])
            self.assertEqual(git('branch','--list','initiative/fixture'),'')

    def test_existing_regular_prompt_is_preserved(self):
        tool=self.tool()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);repo,git=self.fixture(root)
            directory=repo/'initiatives/fixture';directory.mkdir(parents=True)
            (directory/'SELF_PROMPT.md').write_text('Original scoped instructions\n')
            git('add','.');git('commit','-m','baseline with prompt')
            target=root/'worktree';tool.create('fixture',repo,git('rev-parse','HEAD'),target)
            self.assertEqual((target/'initiatives/fixture/SELF_PROMPT.md').read_text(),'Original scoped instructions\n')
            self.assertEqual(json.loads((target/'initiatives/fixture/INITIATIVE.json').read_text())['status'],'SCOPED_NOT_ACCEPTED')

if __name__=='__main__':unittest.main()
