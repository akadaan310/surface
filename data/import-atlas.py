#!/usr/bin/env python3
"""Reproduce gaia.bin solely from the preserved ESA CSV. No network required."""
import csv, hashlib, io, json, math, struct, zlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
raw=(HERE/'gaia-dr3-bright-source.csv').read_bytes()
if len(raw)>5_000_000: raise ValueError('bounded raw input exceeded')
records=[]
seen=set()
missing={'color':0,'parallax':0,'parallaxError':0}
def number(value):
    result=0.0 if value=='' else float(value)
    if not math.isfinite(result):raise ValueError('nonfinite data')
    return result
for row in csv.DictReader(io.StringIO(raw.decode('utf-8'))):
    sid=int(row['source_id'])
    if sid in seen or not 0<sid<2**64:raise ValueError('invalid source ID')
    seen.add(sid)
    if float(row['ref_epoch'])!=2016:raise ValueError('unexpected epoch')
    ra,dec,mag=map(number,(row['ra'],row['dec'],row['phot_g_mean_mag']))
    if not 0<=ra<360 or not -90<=dec<=90 or not -10<mag<7.5:raise ValueError('invalid coordinates/magnitude')
    flags=(1 if row['bp_rp'] else 0)|(2 if row['parallax'] else 0)|(4 if row['parallax_error'] else 0)
    for name,flag in [('color',1),('parallax',2),('parallaxError',4)]:missing[name]+=not bool(flags&flag)
    records.append(struct.pack('<QddffddII',sid,ra,dec,mag,number(row['bp_rp']),number(row['parallax']),number(row['parallax_error']),flags,0))
if len(records)!=10000:raise ValueError('pinned 10000-source count changed')
payload=b''.join(records)
header=struct.pack('<8sIIIId32sII',b'SGAIA001',1,72,56,len(records),2016.0,hashlib.sha256(raw).digest(),zlib.crc32(payload),0)
assert len(header)==72
binary=header+payload
(HERE/'gaia.bin').write_bytes(binary)
meta={
 'schema':'SURFACE-GAIA-BINARY/1','name':'Gaia DR3 bounded bright-source catalogue','count':len(records),
 'frame':'ICRS','epochJulianYear':2016.0,'retrievedUTC':'2026-10-25',
 'source':{'endpoint':'https://gea.esac.esa.int/tap-server/tap/sync','table':'gaiadr3.gaia_source',
   'query':'SELECT TOP 10000 source_id,ref_epoch,ra,dec,parallax,parallax_error,phot_g_mean_mag,bp_rp FROM gaiadr3.gaia_source WHERE phot_g_mean_mag < 7.5 ORDER BY phot_g_mean_mag ASC',
   'rawFile':'gaia-dr3-bright-source.csv','sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},
 'binary':{'file':'gaia.bin','sha256':hashlib.sha256(binary).hexdigest(),'bytes':len(binary),'byteOrder':'little',
   'headerBytes':72,'recordBytes':56,'payloadCRC32':f'{zlib.crc32(payload):08x}'},
 'units':{'ra':'degree','dec':'degree','mag':'Gaia G magnitude','colorIndex':'Gaia BP-RP magnitude','parallaxMas':'milliarcsecond','parallaxErrorMas':'milliarcsecond'},
 'storage':{'id':'uint64; never route via floating point','ra':'IEEE754 binary64','dec':'IEEE754 binary64','mag':'IEEE754 binary32','colorIndex':'IEEE754 binary32','parallaxMas':'IEEE754 binary64','parallaxErrorMas':'IEEE754 binary64','flags':'uint32, bit0=color, bit1=parallax, bit2=parallax error'},
 'missingCounts':missing,
 'distancePolicy':'No distance estimates. Missing fields store finite zero with presence flag unset, never an invented value or NaN. Negative source parallaxes are preserved.',
 'displayPolicy':'Unit-sphere direction projection, no inferred stellar distance. Halos and color mapping are display transforms, not measured extent or calibrated spectrum.',
 'limitations':['Exactly 10000 retained sources, with no completeness claim; Gaia can omit very bright stars.','Coordinates remain at epoch J2016.0, without proper-motion propagation, aberration, location or extinction correction.','No temperature is inferred from BP-RP. This catalogue does not represent the entire universe.'],
 'license':{'name':'CC BY-NC 3.0 IGO','source':'https://www.cosmos.esa.int/web/gaia-users/license','url':'https://creativecommons.org/licenses/by-nc/3.0/igo/'},
 'attribution':'ESA/Gaia/DPAC. Uses ESA Gaia mission data processed by the Gaia Data Processing and Analysis Consortium (DPAC). DPAC funding is supplied by national institutions participating in the Gaia Multilateral Agreement.',
 'references':['https://www.cosmos.esa.int/web/gaia/dr3','https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html','https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access','https://www.cosmos.esa.int/web/gaia-users/credits','https://doi.org/10.1051/0004-6361/202243940']}
(HERE/'gaia-provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps({'count':len(records),'bytes':len(binary),'sha256':meta['binary']['sha256'],'missing':missing}))
