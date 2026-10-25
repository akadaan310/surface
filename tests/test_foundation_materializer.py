import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


class FoundationMaterializerTests(unittest.TestCase):
    def tool(self):
        path = Path(__file__).resolve().parents[1] / 'tools/materialize_foundation.py'
        self.assertTrue(path.exists(), 'the immutable foundation materializer must exist')
        spec = importlib.util.spec_from_file_location('foundation_materializer', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def file_checker(self, module):
        checker = getattr(module, 'check_files', None)
        self.assertTrue(callable(checker), 'A file-manifest checker is needed below the pinned receipt boundary.')
        return checker

    def test_chunks_restore_exact_source_and_detect_corruption(self):
        m = self.tool()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            chunks = [b'PK\x03\x04\x00\xff', bytes(range(256))]
            entries = []
            offset = 0
            for n, b in enumerate(chunks):
                p = root / f'{n}.bin'; p.write_bytes(b)
                entries.append({'path': p.name, 'offset': offset, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()})
                offset += len(b)
            raw = b''.join(chunks)
            manifest = {'schema': 'surface.immutable-chunks.v1', 'logical_path': 'archive.zip', 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'parts': entries}
            self.assertEqual(m.read_chunks(root, manifest), raw)
            (root/'0.bin').write_bytes(b'broken')
            with self.assertRaises(ValueError): m.read_chunks(root, manifest)

    def test_zip_paths_duplicates_symlinks_and_budget_reject(self):
        m = self.tool()
        for kind in ('traversal', 'duplicate', 'symlink', 'over-budget'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as d:
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, 'w') as z:
                    if kind == 'traversal': z.writestr('../escape', b'x')
                    elif kind == 'duplicate':
                        z.writestr('a', b'x'); z.writestr('a', b'y')
                    elif kind == 'symlink':
                        info = zipfile.ZipInfo('a'); info.external_attr = 0o120777 << 16; z.writestr(info, b'target')
                    else: z.writestr('a', b'x'*20)
                with self.assertRaises(ValueError): m.unpack(buf.getvalue(), Path(d), max_total=10 if kind == 'over-budget' else 1024)
                self.assertFalse((Path(d).parent/'escape').exists())

    def test_check_receipt_detects_changed_reference(self):
        m = self.tool()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'a').write_bytes(b'original')
            receipt={'schema':'surface.foundation-materialization.v1','files':[{'path':'a','bytes':8,'sha256':hashlib.sha256(b'original').hexdigest()}]}
            (root/'MATERIALIZATION.json').write_text(json.dumps(receipt))
            checker=self.file_checker(m)
            self.assertEqual(checker(root,receipt['files'])['checked_files'],1)
            (root/'a').write_bytes(b'altered')
            with self.assertRaises(ValueError): checker(root,receipt['files'])

    def test_default_check_refuses_unanchored_empty_receipt(self):
        m=self.tool()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'MATERIALIZATION.json').write_text(json.dumps({'schema':'surface.foundation-materialization.v1','files':[]}))
            with self.assertRaisesRegex(ValueError,'receipt identity'):
                m.check(root)

    def test_file_census_rejects_unlisted_files_and_deleted_entries(self):
        m=self.tool();checker=self.file_checker(m)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'a').write_bytes(b'a');(root/'b').write_bytes(b'b')
            files=[{'path':name,'bytes':1,'sha256':hashlib.sha256(name.encode()).hexdigest()} for name in ('a','b')]
            self.assertEqual(checker(root,files)['checked_files'],2)
            with self.assertRaisesRegex(ValueError,'census'):
                checker(root,files[:1])
            (root/'extra').write_bytes(b'extra')
            with self.assertRaisesRegex(ValueError,'census'):
                checker(root,files)

    def test_root_receipt_and_reference_ancestors_cannot_be_symlinks(self):
        m=self.tool()
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);root=base/'root';root.mkdir();outside=base/'outside';outside.mkdir()
            (outside/'a').write_bytes(b'a')
            receipt={'schema':'surface.foundation-materialization.v1','files':[]}
            (root/'MATERIALIZATION.json').write_text(json.dumps(receipt))
            alias=base/'alias';alias.symlink_to(root,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'linked'):
                m.check(alias)
            through_parent=base/'parent';through_parent.symlink_to(base,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'linked'):
                m.check(through_parent/'root')
            (root/'MATERIALIZATION.json').unlink()
            (outside/'receipt').write_text(json.dumps(receipt))
            (root/'MATERIALIZATION.json').symlink_to(outside/'receipt')
            with self.assertRaisesRegex(ValueError,'linked'):
                m.check(root)
            (root/'MATERIALIZATION.json').unlink()
            (root/'linked').symlink_to(outside,target_is_directory=True)
            checker=self.file_checker(m)
            with self.assertRaisesRegex(ValueError,'linked'):
                checker(root,[{'path':'linked/a','bytes':1,'sha256':hashlib.sha256(b'a').hexdigest()}])

    def test_chunk_ancestor_symlink_is_refused(self):
        m=self.tool()
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);root=base/'repo';root.mkdir();outside=base/'outside';outside.mkdir()
            (outside/'part').write_bytes(b'archive');(root/'linked').symlink_to(outside,target_is_directory=True)
            h=hashlib.sha256(b'archive').hexdigest()
            manifest={'schema':'surface.immutable-chunks.v1','bytes':7,'sha256':h,
                      'parts':[{'path':'linked/part','offset':0,'bytes':7,'sha256':h}]}
            with self.assertRaisesRegex(ValueError,'linked'):
                m.read_chunks(root,manifest)

    def test_explicit_directory_after_child_preserves_file(self):
        m=self.tool()
        with tempfile.TemporaryDirectory() as d:
            raw=io.BytesIO()
            with zipfile.ZipFile(raw,'w') as z:
                z.writestr('folder/a',b'original');z.writestr('folder/',b'')
            try:m.unpack(raw.getvalue(),Path(d))
            except ValueError as error:self.fail('A later directory entry must preserve its existing real directory: '+str(error))
            self.assertEqual((Path(d)/'folder/a').read_bytes(),b'original')


if __name__ == '__main__': unittest.main()
