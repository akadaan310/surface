// Programmable addresses compiled to transformations.
//
// Teaching scheme `loom://` (deliberately not `purl://` or `seurl://`, which
// belong to their own projects and are never minted here). An address is a
// word of typed operations, e.g.
//     loom://plate/START/ROTATE:90/SCALE:2/SHIFT:1,0/COMMIT
// The protocol layer is a typed machine (a statechart in the sense of Harel,
// 1987, reduced to a finite-state machine):
//     idle --START--> open --(ROTATE|SCALE|SHIFT|SHEAR|REFLECT)*--> open --COMMIT--> committed
// Opcodes and the START/COMMIT discipline follow the SEURL finite protocol
// (github.com/akadaan310/seurl: START SWITCH WRITE COMMIT BUILD TALK PERTURB);
// the geometric opcodes are a house extension for this exhibit.
//
// Matrix Loom (house construction): each geometric opcode denotes a 3×3
// homogeneous matrix, and an admitted address compiles to the product of its
// operations in order — the transition-monoid compilation of CGT-DEF-007 /
// GIN-DEF-008: a word of any length becomes one constant-size operation.

import { Q } from './rational';
import { identity, multiply, type Mat } from './matrix';

export type OpCode = 'START' | 'ROTATE' | 'SCALE' | 'SHIFT' | 'SHEAR' | 'REFLECT' | 'COMMIT';

export interface Token {
  raw: string;
  op: OpCode | null;
  arg: string | null;
  type: 'control' | 'geometric' | 'unknown';
  error: string | null;
}

export interface CompileResult {
  ok: boolean;
  resource: string | null;
  tokens: Token[];
  states: string[];
  matrix: Mat | null;
  diagnostics: string[];
}

const GEOMETRIC = new Set<OpCode>(['ROTATE', 'SCALE', 'SHIFT', 'SHEAR', 'REFLECT']);

/** Exact rotation matrices exist for multiples of 90°; other angles are rejected rather than approximated. */
function rotation(deg: number): Mat | null {
  const k = ((deg % 360) + 360) % 360;
  const table: Record<number, [number, number]> = { 0: [1, 0], 90: [0, 1], 180: [-1, 0], 270: [0, -1] };
  const cs = table[k];
  if (!cs) return null;
  const [c, s] = cs;
  return [
    [Q.of(c), Q.of(-s), Q.zero],
    [Q.of(s), Q.of(c), Q.zero],
    [Q.zero, Q.zero, Q.one],
  ];
}

function num(s: string): Q | null {
  const m = /^(-?\d{1,6})(?:\/(\d{1,6}))?$/.exec(s.trim());
  if (!m) return null;
  const d = m[2] ? BigInt(m[2]) : 1n;
  if (d === 0n) return null;
  return Q.of(BigInt(m[1]!), d);
}

export function opMatrix(op: OpCode, arg: string | null): { m: Mat | null; error: string | null } {
  const I = identity(3);
  switch (op) {
    case 'ROTATE': {
      const d = arg === null ? NaN : Number(arg);
      const m = Number.isInteger(d) ? rotation(d) : null;
      return m ? { m, error: null } : { m: null, error: 'ROTATE takes a multiple of 90 degrees (exact matrices only)' };
    }
    case 'SCALE': {
      const parts = (arg ?? '').split(',');
      const sx = num(parts[0] ?? '');
      const sy = parts[1] !== undefined ? num(parts[1]) : sx;
      if (!sx || !sy) return { m: null, error: 'SCALE takes a rational factor, or sx,sy' };
      return { m: [[sx, Q.zero, Q.zero], [Q.zero, sy, Q.zero], [Q.zero, Q.zero, Q.one]], error: null };
    }
    case 'SHIFT': {
      const [a, b] = (arg ?? '').split(',');
      const tx = num(a ?? '');
      const ty = num(b ?? '');
      if (!tx || !ty) return { m: null, error: 'SHIFT takes tx,ty' };
      return { m: [[Q.one, Q.zero, tx], [Q.zero, Q.one, ty], [Q.zero, Q.zero, Q.one]], error: null };
    }
    case 'SHEAR': {
      const k = num(arg ?? '');
      if (!k) return { m: null, error: 'SHEAR takes a rational factor' };
      return { m: [[Q.one, k, Q.zero], [Q.zero, Q.one, Q.zero], [Q.zero, Q.zero, Q.one]], error: null };
    }
    case 'REFLECT': {
      if (arg === 'x') return { m: [[Q.one, Q.zero, Q.zero], [Q.zero, Q.of(-1), Q.zero], [Q.zero, Q.zero, Q.one]], error: null };
      if (arg === 'y') return { m: [[Q.of(-1), Q.zero, Q.zero], [Q.zero, Q.one, Q.zero], [Q.zero, Q.zero, Q.one]], error: null };
      return { m: null, error: 'REFLECT takes x or y' };
    }
    default:
      return { m: I, error: null };
  }
}

export function tokenize(address: string): { resource: string | null; tokens: Token[]; error: string | null } {
  const m = /^loom:\/\/([a-z0-9-]{1,32})((?:\/[^/\s]+)*)\/?$/i.exec(address.trim());
  if (!m) return { resource: null, tokens: [], error: 'An address has the form loom://<resource>/<OP>[:<arg>]/…' };
  const parts = (m[2] ?? '').split('/').filter(Boolean);
  const tokens = parts.map<Token>((raw) => {
    const i = raw.indexOf(':');
    const name = i < 0 ? raw : raw.slice(0, i);
    let arg: string | undefined = i < 0 ? undefined : raw.slice(i + 1);
    // A literal "/" would end the path segment (RFC 3986 §3.3), so rationals are percent-encoded: 1%2F2.
    try {
      if (arg !== undefined) arg = decodeURIComponent(arg);
    } catch {
      /* leave malformed encodings as written; opMatrix will reject them */
    }
    const op = name.toUpperCase() as OpCode;
    const known = op === 'START' || op === 'COMMIT' || GEOMETRIC.has(op);
    return {
      raw,
      op: known ? op : null,
      arg: arg ?? null,
      type: !known ? 'unknown' : GEOMETRIC.has(op) ? 'geometric' : 'control',
      error: known ? null : `unknown operation "${name}"`,
    };
  });
  return { resource: m[1]!, tokens, error: null };
}

export function compile(address: string): CompileResult {
  const { resource, tokens, error } = tokenize(address);
  const diagnostics: string[] = [];
  if (error) return { ok: false, resource: null, tokens: [], states: [], matrix: null, diagnostics: [error] };
  let state = 'idle' as 'idle' | 'open' | 'committed' | 'rejected';
  const states: string[] = [state];
  let M: Mat = identity(3);
  for (const [i, t] of tokens.entries()) {
    if (state === 'rejected') break;
    if (!t.op) {
      t.error = t.error ?? 'unknown operation';
      diagnostics.push(`step ${i + 1}: ${t.error}`);
      state = 'rejected';
    } else if (t.op === 'START') {
      if (state !== 'idle') { t.error = 'START is admissible only in state idle'; diagnostics.push(`step ${i + 1}: ${t.error}`); state = 'rejected'; }
      else state = 'open';
    } else if (t.op === 'COMMIT') {
      if (state !== 'open') { t.error = 'COMMIT is admissible only in state open'; diagnostics.push(`step ${i + 1}: ${t.error}`); state = 'rejected'; }
      else state = 'committed';
    } else {
      if (state !== 'open') {
        t.error = `${t.op} is a geometric operation; it is admissible only after START and before COMMIT`;
        diagnostics.push(`step ${i + 1}: ${t.error}`);
        state = 'rejected';
      } else {
        const { m, error: e } = opMatrix(t.op, t.arg);
        if (!m) { t.error = e; diagnostics.push(`step ${i + 1}: ${e}`); state = 'rejected'; }
        else M = multiply(m, M); // later operations act after earlier ones
      }
    }
    states.push(state);
  }
  if (state === 'open') diagnostics.push('the address never COMMITs: the machine halts in state open, so nothing is applied');
  if (state === 'idle') diagnostics.push('the address never STARTs');
  const ok = state === 'committed';
  if (ok) diagnostics.push(`admitted: ${tokens.filter((t) => t.type === 'geometric').length} operations compiled to one 3×3 matrix`);
  return { ok, resource, tokens, states, matrix: ok ? M : null, diagnostics };
}

export function applyHomogeneous(m: Mat, x: number, y: number): [number, number] {
  const f = m.map((r) => r.map((q) => q.toNumber()));
  return [f[0]![0]! * x + f[0]![1]! * y + f[0]![2]!, f[1]![0]! * x + f[1]![1]! * y + f[1]![2]!];
}
