import { describe, expect, it } from 'vitest';
import { DIVISIONS, TOPICS, topic, topicsOf } from '../src/content/registry';
import { BRIDGES, TERMS, findTerm } from '../src/content/glossary';

describe('university registry', () => {
  it('seeds all six divisions with at least eight substantive topics', () => {
    expect(DIVISIONS).toHaveLength(6);
    for (const d of DIVISIONS) {
      const ts = topicsOf(d.id);
      expect(ts.length, d.id).toBeGreaterThanOrEqual(8);
      expect(ts.every((t) => t.division === d.id)).toBe(true);
      // one executable mini-lesson per division
      expect(ts.some((t) => t.domainAdapter === d.exhibit), d.id).toBe(true);
    }
  });

  it('has unique ids and complete fields', () => {
    const ids = new Set<string>();
    for (const t of TOPICS) {
      expect(ids.has(t.id), t.id).toBe(false);
      ids.add(t.id);
      expect(t.summary.length, t.id).toBeGreaterThan(80);
      expect(t.definitions.length, t.id).toBeGreaterThan(0);
      expect(t.examples.length, t.id).toBeGreaterThan(0);
      expect(t.sources.length, t.id).toBeGreaterThan(0);
      expect(t.challenge.answer.length, t.id).toBeGreaterThan(0);
      expect(t.visualLesson.length, t.id).toBeGreaterThan(0);
    }
  });

  it('every curriculum entry, prerequisite and glossary term resolves', () => {
    for (const d of DIVISIONS) for (const id of d.curriculum) expect(topic(id), id).toBeDefined();
    for (const t of TOPICS) {
      for (const p of t.prerequisites) expect(topic(p), `${t.id} → ${p}`).toBeDefined();
      for (const g of t.glossary) expect(findTerm(g), `${t.id} glossary ${g}`).toBeDefined();
    }
    for (const term of TERMS) {
      for (const r of term.related) expect(findTerm(r), `${term.id} → ${r}`).toBeDefined();
      for (const s of term.senses) if (s.topic) expect(topic(s.topic), `${term.id} sense → ${s.topic}`).toBeDefined();
      for (const b of term.bridges ?? []) expect(BRIDGES.find((x) => x.id === b), b).toBeDefined();
    }
  });

  it('labels house terms as constructions, not established mathematics', () => {
    for (const id of ['plicastratum', 'ingrammatica', 'imagistratum', 'matrix-loom', 'constructive-admission', 'phonogrammatica', 'world-loom', 'alphabet-towers', 'relational-generativity']) {
      const t = topic(id)!;
      expect(t.status, id).toBe('house');
      expect(t.definitions.some((d) => d.status === 'house'), id).toBe(true);
    }
    expect(topic('homeless-dark')!.status).toBe('application');
    expect(topic('invisible-sensing')!.status).toBe('application');
  });

  it('runs every glossary bridge on its default input', () => {
    for (const b of BRIDGES) {
      const out = b.run(b.defaultInput);
      expect(out.length, b.id).toBeGreaterThan(0);
      expect(out.join(' '), b.id).not.toMatch(/undefined|NaN/);
    }
  });

  it('teaches no excluded subject matter', () => {
    const text = JSON.stringify([TOPICS, TERMS, DIVISIONS]).toLowerCase();
    for (const banned of ['quran', 'qur', 'surah', 'scripture', 'hadith', 'religio', 'arabic', 'continuity of identity', 'acsp', 'session continuity']) {
      expect(text.includes(banned), banned).toBe(false);
    }
  });
});
