"""Pure bounded adaptation of ASTRA 0.2 geometry and ATOM 0.1 evidence.

This module performs no I/O. A returned event is a proposal for the caller's
durable ledger, not a committed receipt. See docs/ASTRA_ADAPTER_IMPLEMENTATION.md.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any, Literal, TypedDict

ADAPTER_VERSION = 'POLYIA-ASTRA/0.1'
SOURCE_VERSION = 'ASTRA/0.2'
PROTOCOL = 'ATOM-HANDOFF/0.1'
PHASES = ('OBSERVE', 'PROPOSE', 'ADMIT', 'EXECUTE', 'VERIFY', 'CHECKPOINT', 'HOLD')
SOURCE_ROOT = ('sources/expanded/ASTRA_CELESTIAL_SHELLS_ATOM_CODEX_GOD_SEED_V02/'
               'ASTRA_CELESTIAL_SHELLS_V02/')
_PINS = (
    ('sources/recovered/ASTRA_CELESTIAL_SHELLS_ATOM_CODEX_GOD_SEED_V02.zip',
     '09f631d03503dd7b7b0f44010f6d9f4a9af5c37fab28d79e57c3bba5cb3380ed', 'archive root ASTRA_CELESTIAL_SHELLS_V02'),
    (SOURCE_ROOT + 'docs/FORMAL_CONSTITUTION.md',
     'f9a5aaa75812d0c887b8e4aa75adb677903885f293e329127afecabaf78e670e', 'Definition of a transition atom; Immutability and versioning'),
    (SOURCE_ROOT + 'docs/SCIENTIFIC_AND_AUDIO_CONTRACT.md',
     'c539c84b53acb24122f882ac58678ba3f10654d2100893f64b7a870204f7c5bc', 'Geometry; Provenance; Tests and blockers'),
    (SOURCE_ROOT + 'handoff/ATOM_AGENT_PROTOCOL.json',
     '2d266d815c268dcd5d12a15b2866b80b88fa5500559111ba62a6e3aaaf0a5794', 'phase_order; required_report_fields; rules'),
    (SOURCE_ROOT + 'atom/core.py',
     '243e27d8c6a7448dfe626d764b140b0b756db265fe0dcaf8428a91487c808ad7', 'Universe.advance; Universe._check; Universe._evaluate; Universe._verify_output'),
    (SOURCE_ROOT + 'web/sky.js',
     'fb363a05365eaaabb3e1efabe6054c0a1c579422fff1df9b44927b572f46db57', 'vec; rotate; project'),
)
LIMITS = (
    'Pure kernel: no durable commit, source-object archive, HTTP authorization or external dispatch.',
    'Checkpoint persistence, crash recovery, HOLD and resume are unavailable in this kernel.',
    'State digests and same-handler replay are integrity/self-consistency checks, not authentication or independent proof.',
    'Only the inherited evidence atom is adapted; no arbitrary execution or cross-project effects.',
    'Geometry is an ICRS-oriented direction visualization, not an observer transform or orbital solver.',
    'Catalog provenance is caller asserted; no catalog, Gaia, ephemeris, WebGL or audio validation is performed.',
    'Display radii and proximity do not establish semantic relations or astronomical distances.',
    'Full Astra HTTP/storage acceptance and cross-project adapters remain open; mission NOT_COMMISSIONED.',
)


class EvidenceParameters(TypedDict):
    artifact: str
    content: str


class EvidenceOutput(TypedDict):
    artifact: str
    sha256: str
    source: Literal['caller-provided']


class Refusal(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _refuse(code: str, message: str) -> None:
    raise Refusal(code, message)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _json_guard(value: Any) -> None:
    """Bound work before copying, hashing, or traversing caller-owned objects."""
    count, string_bytes = 0, 0

    def visit(item: Any, depth: int) -> None:
        nonlocal count, string_bytes
        count += 1
        if depth > 16 or count > 20000:
            _refuse('RESOURCE_LIMIT', 'JSON depth or node limit exceeded')
        if type(item) is str:
            if len(item) > 32768:
                _refuse('RESOURCE_LIMIT', 'String length limit exceeded')
            try:
                string_bytes += len(item.encode('utf-8'))
            except UnicodeEncodeError:
                _refuse('INVALID_UNICODE', 'Strings must encode as UTF-8')
            if string_bytes > 262144:
                _refuse('RESOURCE_LIMIT', 'Total string byte limit exceeded')
        elif type(item) is dict:
            if len(item) > 1024:
                _refuse('RESOURCE_LIMIT', 'Object field limit exceeded')
            for key, child in item.items():
                if type(key) is not str:
                    _refuse('SCHEMA', 'Object keys must be strings')
                visit(key, depth + 1)
                visit(child, depth + 1)
        elif type(item) is list:
            if len(item) > 1024:
                _refuse('RESOURCE_LIMIT', 'Array length limit exceeded')
            for child in item:
                visit(child, depth + 1)
        elif type(item) is float:
            if not math.isfinite(item):
                _refuse('NONFINITE', 'Numbers must be finite')
        elif type(item) is int:
            if item.bit_length() > 256:
                _refuse('RESOURCE_LIMIT', 'Integer magnitude limit exceeded')
        elif item is not None and type(item) is not bool:
            _refuse('SCHEMA', 'Only JSON values are accepted')

    visit(value, 0)


def _object(value: Any, required: set[str], optional: set[str] | None = None) -> dict:
    if type(value) is not dict:
        _refuse('SCHEMA', 'Expected an object')
    if required - value.keys() or value.keys() - required - (optional or set()):
        _refuse('SCHEMA', 'Missing or unsupported fields')
    return value


def _number(value: Any, low: float, high: float, *, low_open: bool = False,
            high_open: bool = False) -> float:
    if type(value) not in (int, float):
        _refuse('DOMAIN', 'Expected a finite number, not a boolean or string')
    if not (low <= value <= high) or (low_open and value == low) or (high_open and value == high):
        _refuse('DOMAIN', 'Number is outside the declared domain')
    return float(value)


def _text(value: Any, maximum: int = 120) -> str:
    if type(value) is not str or not 1 <= len(value) <= maximum:
        _refuse('SCHEMA', 'Expected a bounded nonempty string')
    return value


def _base() -> dict:
    return {'ok': True, 'status': 'PASS', 'adapter_version': ADAPTER_VERSION,
            'llm_required': False, 'effect_class': 'pure', 'checks': [],
            'identity': {'source_id': 'SRC-ASTRA', 'source_version': SOURCE_VERSION,
                         'atom_version': 'ATOM/0.1', 'protocol': PROTOCOL,
                         'handler_version': 'polyia.astra.evidence/0.1',
                         'sources': [{'path': p, 'sha256': s, 'anchor': a} for p, s, a in _PINS],
                         'source_verification': 'PINNED_REFERENCE_NOT_RUNTIME_FILE_CHECK'},
            'limitations': list(LIMITS)}


def _geometry(parameters: dict) -> dict:
    payload = _object(parameters, {'observer', 'points', 'view'})
    if payload['observer'] != 'ICRS-direction-only':
        _refuse('UNSUPPORTED_OBSERVER', 'Only ICRS directions with no observer transform are supported')
    view = _object(payload['view'], {'width', 'height', 'distance', 'yaw_rad', 'pitch_rad'}, {'selected'})
    width = _number(view['width'], 0, 16384, low_open=True)
    height = _number(view['height'], 0, 16384, low_open=True)
    distance = _number(view['distance'], 0, 1000000, low_open=True)
    yaw = _number(view['yaw_rad'], -math.tau, math.tau)
    pitch = _number(view['pitch_rad'], -math.pi, math.pi)
    points = payload['points']
    if type(points) is not list:
        _refuse('SCHEMA', 'points must be an array')
    if len(points) > 256:
        _refuse('RESOURCE_LIMIT', 'At most 256 points are supported')
    semantics, projection, seen = [], [], set()
    for item in points:
        item = _object(item, {'id', 'ra_deg', 'dec_deg', 'provenance'}, {'radius'})
        name = _text(item['id'])
        if name in seen:
            _refuse('DUPLICATE_ID', 'Point IDs must be unique')
        seen.add(name)
        provenance = _object(item['provenance'], {'kind', 'source_id'})
        if provenance['kind'] not in ('catalog', 'synthetic', 'illustrative'):
            _refuse('PROVENANCE', 'Supported provenance kinds: catalog, synthetic, illustrative')
        _text(provenance['source_id'], 240)
        ra = _number(item['ra_deg'], 0, 360, high_open=True)
        dec = _number(item['dec_deg'], -90, 90)
        radius = _number(item.get('radius', 1), 0, 1000000, low_open=True)
        a, d = math.radians(ra), math.radians(dec)
        vector = [math.cos(d)*math.sin(a), math.sin(d), math.cos(d)*math.cos(a)]
        x, y, z = [v*radius for v in vector]
        # Exact order and signs of the retained sky.js rotate function.
        horizontal = x*math.cos(yaw) - z*math.sin(yaw)
        depth = x*math.sin(yaw) + z*math.cos(yaw)
        camera = [horizontal, y*math.cos(pitch) - depth*math.sin(pitch),
                  y*math.sin(pitch) + depth*math.cos(pitch)]
        separation = distance - camera[2]
        clipped = separation < .4
        screen = None
        if not clipped:
            scale = min(width, height)*1.43 / separation
            screen = {'x': width*.5 + camera[0]*scale,
                      'y': height*.51 - camera[1]*scale,
                      'depth': camera[2], 'scale': scale}
        semantics.append({'id': name, 'ra_deg': ra, 'dec_deg': dec,
                          'frame': 'ICRS-direction-only', 'provenance': copy.deepcopy(provenance)})
        projection.append({'id': name, 'unit_vector': vector, 'radius': radius,
                           'radius_kind': 'authored-display-scale', 'camera_vector': camera,
                           'clipped': clipped, 'screen': screen})
    if view.get('selected') is not None and (type(view['selected']) is not str or view['selected'] not in seen):
        _refuse('DOMAIN', 'Selection must refer to an existing point ID')
    return {'semantic_objects': semantics, 'semantic_digest': _digest(semantics),
            'projection': {'convention': 'ASTRA/0.2:web/sky.js', 'near_plane': .4, 'points': projection},
            'view_state': copy.deepcopy(view),
            'provenance_verification': 'CALLER_ASSERTED_NOT_CATALOG_VERIFIED',
            'checks': [{'name': 'input_domain', 'verdict': 'PASS', 'evidence_class': 'SCHEMA_CHECK'},
                       {'name': 'projection', 'verdict': 'PASS', 'evidence_class': 'NUMERICAL_EVALUATION',
                        'independent': False, 'scope': 'finite bounded points; clipped points are explicit'}]}


def _initial_state() -> dict:
    return {'schema': 'POLYIA-ASTRA-STATE/0.1', 'source_version': SOURCE_VERSION,
            'protocol': 'ATOM/0.1', 'tick': 0, 'phase': 'OBSERVE',
            'active': None, 'pending': None, 'events': []}


def _evidence_parameters(value: dict) -> EvidenceParameters:
    _object(value, set(), {'artifact', 'content'})
    artifact, content = value.get('artifact', 'fixture'), value.get('content', 'prototype evidence')
    if type(artifact) is not str or len(artifact) > 120 or type(content) is not str or len(content) > 10000:
        _refuse('GUARD', 'Evidence requires artifact <=120 and content <=10000 characters')
    return {'artifact': artifact, 'content': content}


def _evaluate_evidence(parameters: EvidenceParameters) -> EvidenceOutput:
    return {'artifact': parameters['artifact'],
            'sha256': hashlib.sha256(parameters['content'].encode('utf-8')).hexdigest(),
            'source': 'caller-provided'}


def _transition(state: dict, parameters: dict) -> dict:
    """Return one successor. Outputs live in pending.output, preserving delta:QxI->Q."""
    phase = state['phase']
    if phase == 'CHECKPOINT':
        _refuse('PERSISTENCE_REQUIRED', 'No checkpoint claim without saved, verified source objects and durable state')
    if phase != 'OBSERVE' and parameters:
        _refuse('SCHEMA', 'Parameters may only be selected in OBSERVE')
    successor = copy.deepcopy(state)
    pending = successor['pending']
    if phase == 'OBSERVE':
        successor['active'] = 'evidence'
        successor['pending'] = {'params': copy.deepcopy(parameters), 'decision': None,
                                'output': None, 'evaluation': None}
        verb = 'SELECT'
    elif phase == 'PROPOSE':
        # Source fixed maximin table: VERIFY min=4; OPTIMIZE=2, HOLD=1, EXPLORE=-3.
        pending['decision'] = {'action': 'VERIFY', 'worst_case_utility': 4, 'nominal': 4}
        verb = 'PROPOSE'
    elif phase == 'ADMIT':
        _evidence_parameters(pending['params'])
        verb = 'ADMIT'
    elif phase == 'EXECUTE':
        pending['output'] = _evaluate_evidence(_evidence_parameters(pending['params']))
        verb = 'EXECUTE'
    elif phase == 'VERIFY':
        expected = _evaluate_evidence(_evidence_parameters(pending['params']))
        if pending['output'] != expected:
            _refuse('STATE_INTEGRITY', 'Evidence output does not match declared handler')
        pending['evaluation'] = {'verdict': 'PASS', 'evidence_class': 'HANDLER_SELF_CONSISTENCY',
                                 'independent': False, 'output_hash': _digest(expected)}
        verb = 'VERIFY'
    else:
        _refuse('PHASE', 'Phase is not supported by the pure adapter')
    successor['phase'] = PHASES[PHASES.index(phase) + 1]
    successor['tick'] += 1
    event = {'tick': successor['tick'], 'verb': verb, 'from_phase': phase,
             'to_phase': successor['phase'], 'input': copy.deepcopy(parameters),
             'previous': state['events'][-1]['hash'] if state['events'] else '0'*64}
    event['hash'] = _digest(event)
    successor['events'].append(event)
    return successor


def _validated_state(value: Any) -> dict:
    _object(value, set(_initial_state()))
    if value['phase'] not in PHASES:
        _refuse('PHASE', 'Unknown ATOM phase')
    if value['schema'] != 'POLYIA-ASTRA-STATE/0.1' or value['source_version'] != SOURCE_VERSION or value['protocol'] != 'ATOM/0.1':
        _refuse('VERSION', 'Unknown state schema or source version')
    if type(value['tick']) is not int or type(value['events']) is not list or not 0 <= value['tick'] <= 5 or len(value['events']) != value['tick']:
        _refuse('STATE_INTEGRITY', 'Invalid bounded adapter clock or history')
    reconstructed = _initial_state()
    for event in value['events']:
        _object(event, {'tick', 'verb', 'from_phase', 'to_phase', 'input', 'previous', 'hash'})
        if type(event['input']) is not dict:
            _refuse('SCHEMA', 'Event input must be an object')
        reconstructed = _transition(reconstructed, event['input'])
        if _canonical(event) != _canonical(reconstructed['events'][-1]):
            _refuse('STATE_INTEGRITY', 'Event history does not reconstruct')
    if _canonical(value) != _canonical(reconstructed):
        _refuse('STATE_INTEGRITY', 'State does not equal its bounded transition history')
    return reconstructed


def _report(state: dict) -> dict:
    evaluation = state['pending']['evaluation'] if state['pending'] else None
    return {'protocol': PROTOCOL, 'state_digest': _digest(state), 'tick': state['tick'],
            'clock': 'adapter-domain-tick; separate from PolyIA revision and source Universe tick',
            'phase': state['phase'], 'active': state['active'], 'checkpoint_head': None,
            'recent': [{'event_digest': e['hash'], 'tick': e['tick'], 'verb': e['verb']}
                       for e in state['events'][-5:]],
            'verification': evaluation or {'verdict': 'NOT_RUN', 'evidence_class': 'HANDLER_SELF_CONSISTENCY',
                                            'independent': False},
            'next_action': {'operation': 'atom.advance', 'available': state['phase'] != 'CHECKPOINT',
                            'grants_authority': False},
            'digest_scheme': 'sha256/json-sort_keys-utf8-compact-no_nan/0.1',
            'limits': list(LIMITS)}


def run_adapter(parameters: dict) -> dict:
    """Return a structured PASS/REFUSED result; never perform or authorize effects.

    Supported operations: geometry.project, atom.initialize, atom.advance,
    atom.report. Every request must pin adapter_version, source_version, protocol.
    Atom advances require state, expected_state_digest and an input object.
    """
    result = _base()
    accepted_state = None
    try:
        _json_guard(parameters)
        envelope = {'adapter_version', 'source_version', 'protocol', 'operation'}
        _object(parameters, envelope, {'input', 'state', 'expected_state_digest'})
        if (parameters['adapter_version'] != ADAPTER_VERSION or
                parameters['source_version'] != SOURCE_VERSION or parameters['protocol'] != PROTOCOL):
            _refuse('VERSION', 'Explicit supported adapter, source and handoff versions are required')
        operation = parameters['operation']
        required = {'geometry.project': {'input'}, 'atom.initialize': set(),
                    'atom.report': {'state'}, 'atom.advance': {'state', 'expected_state_digest', 'input'}}
        if type(operation) is not str or operation not in required:
            _refuse('UNKNOWN_OPERATION', 'Operation is not registered')
        _object(parameters, envelope | required[operation])
        if operation == 'geometry.project':
            result.update(_geometry(parameters['input']))
        else:
            accepted_state = _initial_state() if operation == 'atom.initialize' else _validated_state(parameters['state'])
            if operation == 'atom.advance':
                if parameters['expected_state_digest'] != _digest(accepted_state):
                    _refuse('STALE_STATE', 'Expected state digest does not match supplied state')
                if type(parameters['input']) is not dict:
                    _refuse('SCHEMA', 'Atom input must be an object')
                accepted_state = _transition(accepted_state, parameters['input'])
            result.update({'state': accepted_state, 'report': _report(accepted_state),
                           'checks': [{'name': 'bounded_state_reconstruction', 'verdict': 'PASS',
                                       'evidence_class': 'HANDLER_SELF_CONSISTENCY', 'independent': False}]})
            if operation == 'atom.advance':
                result['event'] = copy.deepcopy(accepted_state['events'][-1])
                result['event_persistence'] = 'NOT_COMMITTED_BY_KERNEL'
        return result
    except Refusal as exc:
        result.update({'ok': False, 'status': 'REFUSED', 'error': {'code': exc.code, 'message': str(exc)},
                       'checks': [{'name': 'admission', 'verdict': 'REFUSED', 'code': exc.code}]})
        if accepted_state is not None:
            result.update({'state': accepted_state, 'report': _report(accepted_state)})
        return result
