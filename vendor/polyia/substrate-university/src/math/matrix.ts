// Exact linear algebra over ℚ for the Imagistratum exhibits and the gate.
// A matrix A (m×n) is the linear map x ↦ Ax from ℚⁿ to ℚᵐ.
//   image  im A = column space = { Ax : x ∈ ℚⁿ }       (what is reachable)
//   kernel ker A = null space  = { x : Ax = 0 }         (what is lost)
//   rank–nullity: rank A + dim ker A = n                (Axler, LADR, 3.22)

import { Q } from './rational';

export type Mat = Q[][];
export type Vec = Q[];

export function mat(rows: (number | string)[][]): Mat {
  return rows.map((r) => r.map(toQ));
}

export function vec(xs: (number | string)[]): Vec {
  return xs.map(toQ);
}

function toQ(x: number | string): Q {
  if (typeof x === 'number') {
    if (!Number.isInteger(x)) throw new RangeError('mat: use integers or "p/q" strings for exact entries');
    return Q.of(x);
  }
  const [p, q] = x.split('/');
  return Q.of(BigInt(p!.trim()), BigInt((q ?? '1').trim()));
}

export function dims(a: Mat): [number, number] {
  return [a.length, a[0]?.length ?? 0];
}

export function multiply(a: Mat, b: Mat): Mat {
  const [m, k] = dims(a);
  const [k2, n] = dims(b);
  if (k !== k2) throw new RangeError(`multiply: ${m}×${k} by ${k2}×${n} is not defined`);
  return Array.from({ length: m }, (_, i) =>
    Array.from({ length: n }, (_, j) => {
      let s = Q.zero;
      for (let t = 0; t < k; t++) s = s.add(a[i]![t]!.mul(b[t]![j]!));
      return s;
    }),
  );
}

export function apply(a: Mat, x: Vec): Vec {
  return multiply(a, x.map((v) => [v])).map((r) => r[0]!);
}

export function identity(n: number): Mat {
  return Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => (i === j ? Q.one : Q.zero)));
}

/** Reduced row echelon form and pivot columns. */
export function rref(a: Mat): { r: Mat; pivots: number[] } {
  const r = a.map((row) => row.slice());
  const [m, n] = dims(r);
  const pivots: number[] = [];
  let row = 0;
  for (let col = 0; col < n && row < m; col++) {
    let p = -1;
    for (let i = row; i < m; i++) if (!r[i]![col]!.isZero()) { p = i; break; }
    if (p < 0) continue;
    [r[row], r[p]] = [r[p]!, r[row]!];
    const inv = Q.one.div(r[row]![col]!);
    r[row] = r[row]!.map((v) => v.mul(inv));
    for (let i = 0; i < m; i++) {
      if (i === row || r[i]![col]!.isZero()) continue;
      const f = r[i]![col]!;
      r[i] = r[i]!.map((v, j) => v.sub(f.mul(r[row]![j]!)));
    }
    pivots.push(col);
    row++;
  }
  return { r, pivots };
}

export function rank(a: Mat): number {
  return rref(a).pivots.length;
}

/** A basis of ker A (one vector per free column). */
export function kernelBasis(a: Mat): Vec[] {
  const [, n] = dims(a);
  const { r, pivots } = rref(a);
  const free = Array.from({ length: n }, (_, j) => j).filter((j) => !pivots.includes(j));
  return free.map((f) => {
    const v: Vec = Array.from({ length: n }, () => Q.zero);
    v[f] = Q.one;
    pivots.forEach((pc, i) => {
      v[pc] = r[i]![f]!.neg();
    });
    return v;
  });
}

/** A basis of im A: the pivot columns of A itself. */
export function imageBasis(a: Mat): Vec[] {
  const { pivots } = rref(a);
  return pivots.map((j) => a.map((row) => row[j]!));
}

export function determinant(a: Mat): Q {
  const [m, n] = dims(a);
  if (m !== n) throw new RangeError('determinant: matrix is not square');
  const r = a.map((row) => row.slice());
  let det = Q.one;
  for (let c = 0; c < n; c++) {
    let p = -1;
    for (let i = c; i < n; i++) if (!r[i]![c]!.isZero()) { p = i; break; }
    if (p < 0) return Q.zero;
    if (p !== c) {
      [r[c], r[p]] = [r[p]!, r[c]!];
      det = det.neg();
    }
    det = det.mul(r[c]![c]!);
    for (let i = c + 1; i < n; i++) {
      const f = r[i]![c]!.div(r[c]![c]!);
      r[i] = r[i]!.map((v, j) => v.sub(f.mul(r[c]![j]!)));
    }
  }
  return det;
}

export type Preimage =
  | { kind: 'empty'; explanation: string }
  | { kind: 'point'; x: Vec; explanation: string }
  | { kind: 'affine'; x: Vec; directions: Vec[]; explanation: string };

/** The preimage A⁻¹(b) = { x : Ax = b }: empty, a single point, or x₀ + ker A. */
export function preimage(a: Mat, b: Vec): Preimage {
  const [m, n] = dims(a);
  const aug = a.map((row, i) => [...row, b[i]!]);
  const { r, pivots } = rref(aug);
  if (pivots.includes(n)) {
    return { kind: 'empty', explanation: `b = (${fmtVec(b)}) is not in the image of A; no input reaches it.` };
  }
  const x: Vec = Array.from({ length: n }, () => Q.zero);
  pivots.forEach((pc, i) => {
    x[pc] = r[i]![n]!;
  });
  const ker = kernelBasis(a);
  void m;
  if (ker.length === 0) return { kind: 'point', x, explanation: `Exactly one input reaches b: x = (${fmtVec(x)}).` };
  return {
    kind: 'affine',
    x,
    directions: ker,
    explanation: `Infinitely many inputs reach b: x = (${fmtVec(x)}) + span{${ker.map((k) => `(${fmtVec(k)})`).join(', ')}}. Moving along the kernel changes the input but not the output.`,
  };
}

export function fmtVec(v: Vec): string {
  return v.map((q) => q.toString()).join(', ');
}

export function fmtMat(a: Mat): string {
  return a.map((r) => `[${r.map((q) => q.toString()).join(' ')}]`).join(' ');
}

export function toFloat(a: Mat): number[][] {
  return a.map((r) => r.map((q) => q.toNumber()));
}

export interface MapAnalysis {
  rank: number;
  nullity: number;
  determinant: string | null;
  image: Vec[];
  kernel: Vec[];
  survives: string;
  summary: string;
}

export function analyse(a: Mat): MapAnalysis {
  const [m, n] = dims(a);
  const rk = rank(a);
  const ker = kernelBasis(a);
  const img = imageBasis(a);
  const det = m === n ? determinant(a).toString() : null;
  const survives = rk === n ? 'everything' : rk === 0 ? 'only the origin' : rk === 1 ? 'a line' : rk === 2 ? 'a plane' : `a ${rk}-dimensional subspace`;
  const summary =
    rk === n
      ? `rank ${rk} = n: the kernel is {0}, so no two inputs collide and every input can be recovered from its output.`
      : `rank ${rk} < ${n}: a ${n - rk}-dimensional kernel is collapsed to 0. The image is ${img.length === 0 ? 'the origin alone' : `${rk}-dimensional`}, and inputs that differ by a kernel vector become indistinguishable.`;
  return { rank: rk, nullity: n - rk, determinant: det, image: img, kernel: ker, survives, summary };
}
