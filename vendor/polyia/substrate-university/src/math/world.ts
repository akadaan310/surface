// Computational Worlds and Emergence.
//
// World Loom (house construction): a world is woven row by row. Each new row
// (a weft) is computed from the previous one by a local rule. With a radius-1
// binary rule this is exactly an elementary cellular automaton (Wolfram, Rev.
// Mod. Phys. 55, 601, 1983): rule number r ∈ [0, 255] maps the neighbourhood
// (left, centre, right), read as a 3-bit number k, to bit k of r.
// Boundaries are periodic (the loom is a cylinder).
//
// BORNE causal dependencies (house application term): world facts form a
// directed acyclic graph; a fact can be "born" only after everything it
// depends on. A valid birth order is a topological order (Kahn, CACM 5(11),
// 1962); removing a fact invalidates exactly the facts reachable from it.

export function stepRule(row: number[], rule: number): number[] {
  const n = row.length;
  return row.map((_, i) => {
    const k = (row[(i - 1 + n) % n]! << 2) | (row[i]! << 1) | row[(i + 1) % n]!;
    return (rule >> k) & 1;
  });
}

export function weave(rule: number, width: number, rows: number, seed: 'single' | number = 'single'): number[][] {
  if (!Number.isInteger(rule) || rule < 0 || rule > 255) throw new RangeError('rule must be an integer in [0, 255]');
  let row: number[];
  if (seed === 'single') {
    row = Array.from({ length: width }, (_, i) => (i === Math.floor(width / 2) ? 1 : 0));
  } else {
    const rnd = mulberry32(seed);
    row = Array.from({ length: width }, () => (rnd() < 0.5 ? 1 : 0));
  }
  const out = [row];
  for (let t = 1; t < rows; t++) {
    row = stepRule(row, rule);
    out.push(row);
  }
  return out;
}

export function density(grid: number[][]): number {
  let s = 0;
  let n = 0;
  for (const r of grid) for (const c of r) { s += c; n++; }
  return n ? s / n : 0;
}

/** Rule table as eight lines "111 → b". */
export function ruleTable(rule: number): { neighbourhood: string; out: number }[] {
  return [7, 6, 5, 4, 3, 2, 1, 0].map((k) => ({ neighbourhood: k.toString(2).padStart(3, '0'), out: (rule >> k) & 1 }));
}

/** Deterministic PRNG (mulberry32). */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function hashString(s: string): number {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
}

export interface CausalGraph {
  nodes: string[];
  /** [cause, effect] */
  edges: [string, string][];
}

export function topologicalOrder(g: CausalGraph): string[] | null {
  const indeg = new Map(g.nodes.map((n) => [n, 0]));
  for (const [, b] of g.edges) indeg.set(b, (indeg.get(b) ?? 0) + 1);
  const queue = g.nodes.filter((n) => indeg.get(n) === 0);
  const out: string[] = [];
  while (queue.length) {
    const u = queue.shift()!;
    out.push(u);
    for (const [a, b] of g.edges) {
      if (a !== u) continue;
      indeg.set(b, indeg.get(b)! - 1);
      if (indeg.get(b) === 0) queue.push(b);
    }
  }
  return out.length === g.nodes.length ? out : null;
}

/** Everything downstream of `n` (the facts that lose their cause if n is removed). */
export function downstream(g: CausalGraph, n: string): string[] {
  const seen = new Set<string>();
  const stack = [n];
  while (stack.length) {
    const u = stack.pop()!;
    for (const [a, b] of g.edges) if (a === u && !seen.has(b)) { seen.add(b); stack.push(b); }
  }
  return g.nodes.filter((x) => seen.has(x));
}

export const WORLD_FACTS: CausalGraph = {
  nodes: ['terrain', 'river', 'well', 'road', 'market', 'lantern-guild', 'night-route', 'festival'],
  edges: [
    ['terrain', 'river'],
    ['terrain', 'road'],
    ['river', 'well'],
    ['road', 'market'],
    ['well', 'market'],
    ['market', 'lantern-guild'],
    ['lantern-guild', 'night-route'],
    ['road', 'night-route'],
    ['night-route', 'festival'],
    ['market', 'festival'],
  ],
};
