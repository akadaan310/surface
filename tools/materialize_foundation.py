#!/usr/bin/env python3
"""Restore exact immutable reference inputs; never execute archive members.

Large original ZIP bytes are represented by ordered, digest-pinned Git chunks.
The original logical archive and every nested archive retain their identity.
Extraction is staged and published only after every member is checked.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import zipfile

REPO = Path(__file__).resolve().parents[1]
COSMOS_SHA = 'ca8f9202b4c4acc8ab39d3a7305f4ba4cf80d016a384db9714019208cd5ae622'
V3_SHA = '4b8decefc53d7f6776ed668cfc2f3ab48660f68e5a47ddfcd4fb346548c32ace'
MATERIALIZATION_SHA = '821b25643300b8db5b7d1dee68c7f9362ca0efccd160210bf14c06a8f4a4174c'
MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MAX_FILES = 5000

def require(condition, message):
    if not condition: raise ValueError(message)

def digest(data): return hashlib.sha256(data).hexdigest()

def relative(name):
    require(isinstance(name, str) and name and len(name) < 4096, 'invalid relative path')
    require('\\' not in name and '\0' not in name and ':' not in name, 'unsafe path')
    require(not name.startswith('/') and all(p not in ('', '.', '..', '.git') for p in name.split('/')), 'unsafe path component')
    return PurePosixPath(name)

def unlinked(path):
    """Reject symlinks before resolving a root or any of its ancestors."""
    path=Path(path).absolute()
    for component in (path, *path.parents):
        require(not component.is_symlink(), 'linked path component '+str(component))
    return path

def directory(root):
    root=unlinked(root)
    require(root.is_dir(), 'missing reference root')
    return root.resolve()

def contained(root, name):
    root=directory(root)
    path=unlinked(root.joinpath(*relative(name).parts))
    require(path.resolve().is_relative_to(root), 'reference path escapes root')
    return path

def read_file(root, name, limit=MAX_FILE):
    path=contained(root,name)
    require(path.is_file(), 'missing or nonregular reference '+name)
    require(path.stat().st_size <= limit, 'reference size budget '+name)
    with path.open('rb') as stream: data=stream.read(limit+1)
    require(len(data) <= limit, 'reference size budget '+name)
    return data

def read_chunks(repo, manifest):
    repo=directory(repo)
    require(manifest['schema'] == 'surface.immutable-chunks.v1', 'unsupported chunk schema')
    require(type(manifest['bytes']) is int and 0 < manifest['bytes'] <= MAX_FILE, 'chunk size budget')
    require(0 < len(manifest['parts']) <= 32, 'chunk count budget')
    parts=[]; offset=0
    for row in manifest['parts']:
        require(type(row['bytes']) is int and 0 <= row['bytes'] <= manifest['bytes']-offset, 'chunk size mismatch')
        data=read_file(repo,row['path'],row['bytes'])
        require(len(data) == row['bytes'], 'chunk size mismatch')
        require(row['offset'] == offset and digest(data) == row['sha256'], 'chunk identity/order mismatch')
        parts.append(data); offset += len(data)
    data=b''.join(parts)
    require(len(data) == manifest['bytes'] and digest(data) == manifest['sha256'], 'logical archive identity mismatch')
    return data

def unpack(data, root, *, max_total=MAX_TOTAL):
    root=directory(root)
    require(len(data) <= MAX_FILE, 'compressed archive size budget')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos=z.infolist(); require(len(infos) <= MAX_FILES, 'archive member budget')
        names=set(); total=0
        for info in infos:
            name=info.filename.rstrip('/') if info.is_dir() else info.filename
            relative(name)
            require(name not in names, 'duplicate archive member'); names.add(name)
            kind=stat.S_IFMT(info.external_attr >> 16)
            require(kind in (0, stat.S_IFREG, stat.S_IFDIR), 'archive links/special files refused')
            require(not info.flag_bits & 1, 'encrypted archive refused')
            require(0 <= info.file_size <= MAX_FILE, 'archive member size budget')
            total += info.file_size; require(total <= max_total, 'archive expansion budget')
        for info in infos:
            path=contained(root,info.filename.rstrip('/'))
            if info.is_dir():
                require(not path.exists() or path.is_dir(), 'archive directory conflicts with extracted file')
                path.mkdir(parents=True, exist_ok=True)
            else:
                require(not path.exists(), 'refusing to replace extracted path')
                path.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as stream: raw=stream.read(MAX_FILE+1)
                require(len(raw) == info.file_size, 'archive size/CRC failure')
                with path.open('xb') as f: f.write(raw)
                path.chmod(0o444)

def check_files(root, files):
    """Check bytes and exact file census; the caller must authenticate its manifest.

    This lower-level helper supports small fixtures. The CLI only calls check(),
    which first authenticates the immutable corpus receipt against a fixed pin.
    """
    root=directory(root)
    require(type(files) is list and 0 < len(files) <= MAX_FILES, 'receipt file budget')
    seen=set(); total=0
    for row in files:
        name=str(relative(row['path'])); require(name not in seen, 'duplicate receipt entry');seen.add(name)
        require(name != 'MATERIALIZATION.json', 'receipt cannot list itself')
        require(type(row['bytes']) is int and 0 <= row['bytes'] <= MAX_FILE, 'reference size budget '+name)
        total += row['bytes']; require(total <= MAX_TOTAL, 'aggregate foundation budget')
        data=read_file(root,name,row['bytes'])
        require(len(data) == row['bytes'], 'reference size changed '+name)
        require(digest(data) == row['sha256'], 'reference bytes changed '+name)
    actual=set(); pending=[root]; entries=0
    while pending:
        with os.scandir(pending.pop()) as listing:
            for entry in listing:
                entries += 1; require(entries <= MAX_FILES*4, 'reference census budget')
                require(not entry.is_symlink(), 'linked reference census entry '+entry.name)
                if entry.is_dir(follow_symlinks=False): pending.append(Path(entry.path))
                else:
                    require(entry.is_file(follow_symlinks=False), 'nonregular reference census entry')
                    actual.add(Path(entry.path).relative_to(root).as_posix())
    actual.discard('MATERIALIZATION.json')
    require(actual == seen, 'reference file census changed')
    return {'status':'PASS', 'checked_files':len(seen), 'checked_bytes':total}

def check(root):
    root=directory(root)
    raw=read_file(root,'MATERIALIZATION.json',2*1024*1024)
    require(digest(raw) == MATERIALIZATION_SHA, 'canonical receipt identity mismatch')
    receipt=json.loads(raw)
    require(receipt['schema'] == 'surface.foundation-materialization.v1', 'unsupported receipt')
    result=check_files(root,receipt['files'])
    return {**result, 'receipt_sha256':digest(raw),
            'tolerance':'pinned immutable receipt, exact file census, SHA-256 and byte length; zero mismatches'}

def materialize(output):
    output=unlinked(output)
    require(not output.exists(), 'output already exists; use --check or a new destination')
    manifest=json.loads(read_file(REPO,'lineage/cosmos-continuation-parts/manifest.json'))
    raw=read_chunks(REPO, manifest); require(digest(raw) == COSMOS_SHA, 'unrecognized original commission')
    output.parent.mkdir(parents=True, exist_ok=True)
    unlinked(output)
    stage=Path(tempfile.mkdtemp(prefix='.foundation-', dir=output.parent))
    archives=[]
    def extract(data, expected, label):
        require(digest(data) == expected, 'nested archive digest mismatch '+label)
        unpack(data,stage)
        archives.append({'archive':label,'bytes':len(data),'sha256':expected})
    try:
        extract(raw,COSMOS_SHA,manifest['logical_path'])
        cosmos=stage/'SURFACE_PHYSICAL_COSMOS_V1'
        v3=(cosmos/'upstream/QUANTUM_ORACLE_PHANTOM_V3_N_ATLAS.zip').read_bytes()
        extract(v3,V3_SHA,'QUANTUM_ORACLE_PHANTOM_V3_N_ATLAS.zip')
        v3root=stage/'QUANTUM_ORACLE_V3_EXTENSION'
        v2=(v3root/'upstream/QUANTUM_ORACLE_PHANTOM_V2_HANDOFF.zip').read_bytes()
        v3manifest=json.loads((v3root/'MANIFEST.json').read_bytes())
        # Its nested identity is additionally sealed by the pinned outer V3 ZIP.
        extract(v2,digest(v2),'QUANTUM_ORACLE_PHANTOM_V2_HANDOFF.zip')
        v2root=stage/'QUANTUM_ORACLE_V2_COMMISSION'
        inputs=json.loads((v2root/'INPUTS_MANIFEST.json').read_bytes())['inputs']
        for entry in inputs:
            data=(v2root/str(relative(entry['path']))).read_bytes()
            require(len(data) == entry['bytes'], 'nested input length mismatch')
            extract(data,entry['sha256'],entry['name'])
        constitution=(cosmos/'upstream/PHANTOM_COMPOSER_SURFACE_CONSTITUTION_v1.zip').read_bytes()
        extract(constitution,digest(constitution),'PHANTOM_COMPOSER_SURFACE_CONSTITUTION_v1.zip')
        files=[]
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                data=path.read_bytes();files.append({'path':path.relative_to(stage).as_posix(),'bytes':len(data),'sha256':digest(data)})
        require(len(files) <= MAX_FILES and sum(x['bytes'] for x in files) <= MAX_TOTAL, 'aggregate foundation budget')
        receipt={'schema':'surface.foundation-materialization.v1','archives':archives,'files':files,'execution':'None: input extraction and exact-byte verification only','read_only_files':True}
        with (stage/'MATERIALIZATION.json').open('x',encoding='utf-8') as stream:
            stream.write(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
        result=check(stage)
        os.rename(stage,output)
        return {**result,'output':str(output),'archives':archives}
    finally:
        if stage.exists(): shutil.rmtree(stage)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=REPO/'build/foundation')
    p.add_argument('--check',action='store_true')
    a=p.parse_args(); root=a.output.absolute()
    try: result=check(root) if a.check else materialize(root)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as e:
        p.exit(1,'foundation materialization refused: '+str(e)+'\n')
    print(json.dumps(result,indent=2))

if __name__ == '__main__': main()
