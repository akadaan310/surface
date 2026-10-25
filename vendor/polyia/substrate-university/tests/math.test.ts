import { describe, expect, it } from 'vitest';
import { SYSTEMS, ieeeRepresentation } from '../src/math/numberSystems';
import { Q } from '../src/math/rational';
import { analyse, apply, determinant, imageBasis, kernelBasis, mat, multiply, preimage, rank, vec } from '../src/math/matrix';
import { admissibleTransformation, applyTransformation, evaluateWord, INITIAL_BRIDGES } from '../src/math/bridgeGrammar';
import { digramCounts, foldAll, foldOnce, startFold, unfoldAll, unfoldOnce } from '../src/math/fold';
import { analyseInterval, frequency, orbit, orbitLength } from '../src/math/music';
import { bestCorrespondence, compare, levenshtein, normalize, quantizeTurn, signature, signedAngle, type Pt } from '../src/math/paths';
import { downstream, ruleTable, topologicalOrder, weave, WORLD_FACTS } from '../src/math/world';
import { compile } from '../src/math/addressCompiler';

describe('Arithmetic of Possibility', () => {
  it('1 + 1 depends on the structure', () => {
    expect(SYSTEMS.N.add('1', '1')).toBe('2');
    expect(SYSTEMS.Z.add('1', '1')).toBe('2');
    expect(SYSTEMS.Q.add('1', '1')).toBe('2');
    expect(SYSTEMS.F2.add('1', '1')).toBe('0');
    expect(SYSTEMS.Z6.add('5', '1')).toBe('0');
  });

  it('0 / 1 = 0 uniquely in every system', () => {
    for (const id of ['N', 'Z', 'Q', 'F2', 'Z6'] as const) {
      const r = SYSTEMS[id].divide('0', '1');
      expect(r.kind).toBe('unique');
      expect(r.quotient).toBe('0');
    }
  });

  it('1 / 0 is an image failure and 0 / 0 a kernel failure', () => {
    for (const id of ['N', 'Z', 'Q', 'F2', 'Z6'] as const) {
      const a = SYSTEMS[id].divide('1', '0');
      expect(a.kind).toBe('none');
      expect(a.failure).toBe('image');
      const b = SYSTEMS[id].divide('0', '0');
      expect(b.kind).toBe('many');
      expect(b.failure).toBe('kernel');
    }
    expect(SYSTEMS.F2.divide('0', '0').solutions).toEqual(['0', '1']);
  });

  it('distinguishes ring failures from field division', () => {
    expect(SYSTEMS.Z.divide('7', '2').failure).toBe('image');
    expect(SYSTEMS.Q.divide('7', '2').quotient).toBe('7/2');
    expect(SYSTEMS.N.divide('-4', '2').kind).toBe('none'); // -4 is not parsed as natural in UI; arithmetic still refuses
    // ℤ/6: 2·c = 4 has c ∈ {2, 5}: a coset of ker(c ↦ 2c) = {0, 3}
    const z = SYSTEMS.Z6.divide('4', '2');
    expect(z.kind).toBe('many');
    expect(z.solutions).toEqual(['2', '5']);
    expect(SYSTEMS.Z6.multiplicationMap('2').kernelSet).toEqual(['0', '3']);
    expect(SYSTEMS.Z6.divide('1', '2').failure).toBe('image');
    expect(SYSTEMS.Z6.divide('1', '5').quotient).toBe('5');
  });

  it('parses only members of the declared system', () => {
    expect(SYSTEMS.N.parse('-1')).toBeNull();
    expect(SYSTEMS.F2.parse('3')).toBe('1');
    expect(SYSTEMS.Q.parse('2/4')).toBe('1/2');
    expect(SYSTEMS.Q.parse('1/0')).toBeNull();
  });

  it('labels IEEE 754 results as encodings, not quotients', () => {
    expect(ieeeRepresentation(1, 0).value).toBe('Infinity');
    expect(ieeeRepresentation(0, 0).value).toBe('NaN');
    expect(ieeeRepresentation(0, 1).value).toBe('0');
  });

  it('exact rationals normalize', () => {
    expect(Q.of(2, -4).toString()).toBe('-1/2');
    expect(() => Q.one.div(Q.zero)).toThrow();
  });
});

describe('exact linear algebra', () => {
  it('multiplies and applies', () => {
    const A = mat([[1, 2], [3, 4]]);
    expect(multiply(A, A).map((r) => r.map(String))).toEqual([['7', '10'], ['15', '22']]);
    expect(apply(A, vec([1, 1])).map(String)).toEqual(['3', '7']);
    expect(determinant(A).toString()).toBe('-2');
  });

  it('computes rank, kernel and image of a singular matrix', () => {
    const A = mat([[1, 2], [2, 4]]);
    expect(rank(A)).toBe(1);
    expect(kernelBasis(A).map((v) => v.map(String))).toEqual([['-2', '1']]);
    expect(imageBasis(A).map((v) => v.map(String))).toEqual([['1', '2']]);
    const k = kernelBasis(A)[0]!;
    expect(apply(A, k).every((q) => q.isZero())).toBe(true);
  });

  it('satisfies rank–nullity for a projection', () => {
    const P = mat([[1, 0, 0], [0, 1, 0], [0, 0, 0]]);
    const a = analyse(P);
    expect(a.rank + a.nullity).toBe(3);
    expect(a.survives).toBe('a plane');
    expect(analyse(mat([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]])).survives).toBe('a 3-dimensional subspace');
  });

  it('classifies preimages', () => {
    const A = mat([[1, 2], [2, 4]]);
    expect(preimage(A, vec([1, 3])).kind).toBe('empty');
    const p = preimage(A, vec([3, 6]));
    expect(p.kind).toBe('affine');
    const I = mat([[2, 0], [0, 3]]);
    const q = preimage(I, vec([1, 1]));
    expect(q.kind).toBe('point');
    if (q.kind === 'point') expect(q.x.map(String)).toEqual(['1/2', '1/3']);
  });
});

describe('bridge grammar', () => {
  it('separates admissibility from realizability', () => {
    expect(evaluateWord('FRPG', INITIAL_BRIDGES).realizable).toBe(true);
    expect(evaluateWord('FRPG', INITIAL_BRIDGES).admissible).toBe(true);
    const r = evaluateWord('FP', INITIAL_BRIDGES);
    expect(r.realizable).toBe(false);
    expect(r.admissible).toBe(true);
    const added = applyTransformation(INITIAL_BRIDGES, { op: 'add', a: 'P', b: 'A', type: 'gold' });
    const w = evaluateWord('RPA', added);
    expect(w.realizable).toBe(true);
    expect(w.admissible).toBe(false);
  });

  it('enforces the typed predicate', () => {
    expect(admissibleTransformation(INITIAL_BRIDGES, { op: 'add', a: 'F', b: 'F', type: 'stone' }).passes).toBe(false);
    expect(admissibleTransformation(INITIAL_BRIDGES, { op: 'add', a: 'F', b: 'R', type: 'stone' }).passes).toBe(false);
    expect(admissibleTransformation(INITIAL_BRIDGES, { op: 'remove', a: 'F', b: 'R' }).passes).toBe(true);
    // gold forest: R–P and A–W are gold; joining P–A then R–W with gold would close a gold cycle R–P–A–W–R
    const b1 = applyTransformation(INITIAL_BRIDGES, { op: 'add', a: 'P', b: 'A', type: 'gold' });
    expect(admissibleTransformation(b1, { op: 'add', a: 'R', b: 'W', type: 'gold' }).passes).toBe(false);
    expect(admissibleTransformation(b1, { op: 'add', a: 'R', b: 'W', type: 'stone' }).passes).toBe(true);
    // connectivity: removing two ring bridges strands nothing only if still connected
    const b2 = applyTransformation(INITIAL_BRIDGES, { op: 'remove', a: 'F', b: 'R' });
    expect(admissibleTransformation(b2, { op: 'remove', a: 'P', b: 'G' }).passes).toBe(false);
  });
});

describe('Plicastratum folds', () => {
  it('folds NENENE into one glyph and unfolds exactly', () => {
    const f = foldAll(startFold('NENENE'));
    expect(f.current).toHaveLength(1);
    expect(f.rules.map((r) => `${r.glyph}${r.left}${r.right}`)).toEqual(['ΑNE', 'ΒΑΑ', 'ΓΒΑ']);
    expect(unfoldAll(f).join('')).toBe('NENENE');
  });

  it('round-trips arbitrary words', () => {
    for (const w of ['NNEESSWW', 'abracadabra', 'aaaa', 'x', 'NESWNESWNN']) {
      let st = foldAll(startFold(w));
      expect(unfoldAll(st).join('')).toBe(w);
      while (st.rules.length) st = unfoldOnce(st);
      expect(st.current.join('')).toBe(w);
    }
  });

  it('counts overlapping digrams non-overlappingly', () => {
    expect(digramCounts(['a', 'a', 'a']).get('a\u0000a')).toBe(1);
    expect(foldOnce(startFold('aaaa')).current.join('')).toBe('ΑΑ');
  });
});

describe('interval geometry', () => {
  it('computes orbits in ℤ/12', () => {
    expect(orbit(0, 7)).toEqual([0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5]);
    expect(orbitLength(4)).toBe(3);
    expect(orbitLength(6)).toBe(2);
    expect(orbitLength(0)).toBe(1);
    expect(analyseInterval(4).centsDeviation).toBeCloseTo(13.686, 2);
  });
  it('computes equal-tempered frequencies', () => {
    expect(frequency(69)).toBe(440);
    expect(frequency(60)).toBeCloseTo(261.6256, 3);
  });
});

describe('path signatures', () => {
  it('measures signed angles', () => {
    expect(signedAngle([1, 0], [0, 1])).toBeCloseTo(Math.PI / 2);
    expect(signedAngle([1, 0], [0, -1])).toBeCloseTo(-Math.PI / 2);
    expect(signedAngle([1, 0], [-1, 0])).toBeCloseTo(Math.PI);
    expect(quantizeTurn(Math.PI / 2)).toBe('L');
    expect(quantizeTurn(-0.5)).toBe('r');
    expect(quantizeTurn(0.1)).toBe('S');
  });

  it('builds turn words and normalizes', () => {
    const square: Pt[] = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]];
    const sig = signature(square);
    expect(sig.word.join('')).toBe('LLL');
    expect(sig.totalTurnDeg).toBeCloseTo(270);
    expect(normalize(['L', 'S', 'r'], 'reverse').join('')).toBe('lSR');
  });

  it('finds exact correspondences under reversal', () => {
    const a = signature([[0, 0], [1, 0], [1, 1], [1, 2]]); // L S
    const b = signature([[1, 2], [1, 1], [1, 0], [0, 0]]); // same path reversed: S R
    expect(b.word.join('')).toBe('SR');
    expect(compare(a, b, 'none').exact).toBe(false);
    expect(bestCorrespondence(a, b).exact).toBe(true);
    expect(levenshtein(['a', 'b'], ['a', 'c', 'b'])).toBe(1);
  });
});

describe('worlds', () => {
  it('weaves rule 90 as Pascal’s triangle mod 2', () => {
    const g = weave(90, 9, 4);
    expect(g[1]!.join('')).toBe('000101000');
    expect(g[2]!.join('')).toBe('001000100');
    expect(ruleTable(204).every((r) => r.out === Number(r.neighbourhood[1]))).toBe(true);
  });
  it('orders BORNE facts topologically', () => {
    const order = topologicalOrder(WORLD_FACTS)!;
    for (const [a, b] of WORLD_FACTS.edges) expect(order.indexOf(a)).toBeLessThan(order.indexOf(b));
    expect(downstream(WORLD_FACTS, 'well')).toEqual(['market', 'lantern-guild', 'night-route', 'festival']);
    expect(topologicalOrder({ nodes: ['a', 'b'], edges: [['a', 'b'], ['b', 'a']] })).toBeNull();
  });
});

describe('loom:// compiler', () => {
  it('compiles an admitted address to one matrix', () => {
    const r = compile('loom://plate/START/ROTATE:90/SCALE:2/SHIFT:1,0/COMMIT');
    expect(r.ok).toBe(true);
    expect(r.matrix!.map((row) => row.map(String))).toEqual([['0', '-2', '1'], ['2', '0', '0'], ['0', '0', '1']]);
  });
  it('decodes percent-encoded rational arguments', () => {
    const r = compile('loom://plate/START/SCALE:1%2F2,3/COMMIT');
    expect(r.ok).toBe(true);
    expect(r.matrix![0]![0]!.toString()).toBe('1/2');
    expect(compile('loom://plate/START/SCALE:1/2,3/COMMIT').ok).toBe(false);
  });
  it('rejects inadmissible programs with a reason', () => {
    expect(compile('loom://plate/COMMIT').ok).toBe(false);
    expect(compile('loom://plate/START/ROTATE:45/COMMIT').diagnostics[0]).toMatch(/multiple of 90/);
    expect(compile('loom://plate/START/SCALE:2').ok).toBe(false);
    expect(compile('https://example.org').ok).toBe(false);
    expect(compile('loom://plate/START/COMMIT').matrix!.map((r) => r.map(String))).toEqual([['1', '0', '0'], ['0', '1', '0'], ['0', '0', '1']]);
  });
});
