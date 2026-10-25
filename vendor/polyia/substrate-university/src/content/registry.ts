import type { Division, DivisionId, Topic } from './types';
import { foundations } from './topics/foundations';
import { relational } from './topics/relational';
import { languages } from './topics/languages';
import { geometry } from './topics/geometry';
import { acoustic } from './topics/acoustic';
import { worlds } from './topics/worlds';

export const DIVISIONS: Division[] = [
  {
    id: 'foundations',
    numeral: 'I',
    door: 'The Door of Transitions',
    name: 'Foundations of Computation',
    motto: 'Every computation is a walk through states.',
    glyph: '⟶',
    accent: '#d6ac62',
    description:
      'Transition systems, automata, Computational Grammar Theory, numerical grammars, perturbation, equivalence, graphs and the cost of resolution. The division where a word becomes a walk, and a walk is checked twice: once for admissibility, once for realizability.',
    exhibit: 'bridge-grammar',
    exhibitTitle: 'The Bridge Grammar',
    curriculum: ['transition-systems', 'graph-theory', 'finite-automata', 'equivalence-classes', 'operational-grammar', 'admissibility', 'numerical-grammars', 'perturbation', 'substrate-theory', 'complexity'],
  },
  {
    id: 'relational',
    numeral: 'II',
    door: 'The Door of Folds',
    name: 'Relational and Generative Mathematics',
    motto: 'What is folded is not lost.',
    glyph: '⊗',
    accent: '#c9a3d8',
    description:
      'Alphabets, words, generative grammars, Plicastratum folds, alphabet towers, Ingrammatica, constructive admission, relational generativity, cycles and compositional forms. The division where structure is grown from seeds and rules.',
    exhibit: 'fold',
    exhibitTitle: 'The Plicastratum Walkway',
    curriculum: ['alphabets-words', 'generative-grammars', 'recursive-folds', 'plicastratum', 'alphabet-towers', 'modal-cyclic', 'relational-generativity', 'constructive-admission', 'ingrammatica', 'compositional-forms'],
  },
  {
    id: 'languages',
    numeral: 'III',
    door: 'The Door of Addresses',
    name: 'Programmable Computational Languages',
    motto: 'An address can be a program.',
    glyph: '⌘',
    accent: '#7fc1c4',
    description:
      'URIs as words, PURL programmable addresses, SEURL operation channels, typed machines, types as admissibility, compilation, Matrix Loom, addressable forms, parsing and composition. The division where a line of text becomes a machine that can refuse you.',
    exhibit: 'address-compiler',
    exhibitTitle: 'The loom:// Compiler',
    curriculum: ['uri-grammar', 'typed-machines', 'symbolic-composition', 'types-as-admissibility', 'grammars-as-programs', 'compilation', 'matrix-loom', 'purl', 'seurl', 'addressable-forms'],
  },
  {
    id: 'geometry',
    numeral: 'IV',
    door: 'The Door of Images',
    name: 'Geometry, Physics, and Representation',
    motto: 'The image is what can be reached.',
    glyph: '◬',
    accent: '#f1d79c',
    description:
      'Image, kernel and preimage; Imagistratum; rank and projection loss; cameras, topology, curvature, frames, photography, celestial coordinates, charts and rendering. The division that asks of every representation: what survives?',
    exhibit: 'image-sculpture',
    exhibitTitle: 'The Image Sculpture',
    curriculum: ['image-kernel', 'rank-nullity', 'imagistratum', 'projective-camera', 'spatial-tensors', 'topology', 'curvature', 'chart-correspondences', 'celestial-geometry', 'computational-photography', 'rendering-mathematics', 'invisible-sensing'],
  },
  {
    id: 'acoustic',
    numeral: 'V',
    door: 'The Door of Intervals',
    name: 'Acoustic and Generative Sciences',
    motto: 'Twelve steps, and the circle closes.',
    glyph: '♮',
    accent: '#e08a7a',
    description:
      'Sampling, pitch, interval geometry, tuning, spectra, time–frequency, synthesis, phase, Phonogrammatica and generative composition. The division where modular arithmetic becomes light and sound.',
    exhibit: 'interval-ring',
    exhibitTitle: 'The Interval Ring',
    curriculum: ['sound-signals', 'pitch-frequency', 'interval-geometry', 'tuning', 'fourier', 'phase', 'synthesis', 'time-frequency', 'generative-composition', 'phonogrammatica'],
  },
  {
    id: 'worlds',
    numeral: 'VI',
    door: 'The Door of Worlds',
    name: 'Computational Worlds and Emergence',
    motto: 'A world is woven one row at a time.',
    glyph: '▦',
    accent: '#9fc58a',
    description:
      'Cellular automata, the World Loom, agent grammars, procedural environments, world models, GLMs and LGMs, BORNE dependencies, maps, populations and the HOMELESS / Dark application. The division where rules become places.',
    exhibit: 'world-loom',
    exhibitTitle: 'The World Loom',
    curriculum: ['cellular-automata', 'world-loom', 'procedural-environments', 'agent-grammars', 'maps-navigation', 'borne', 'simulated-populations', 'world-models', 'glm-lgm', 'homeless-dark'],
  },
];

export const TOPICS: Topic[] = [...foundations, ...relational, ...languages, ...geometry, ...acoustic, ...worlds];

const byId = new Map(TOPICS.map((t) => [t.id, t]));
const divById = new Map(DIVISIONS.map((d) => [d.id, d]));

export function topic(id: string): Topic | undefined {
  return byId.get(id);
}

export function division(id: string): Division | undefined {
  return divById.get(id as DivisionId);
}

export function topicsOf(id: DivisionId): Topic[] {
  const d = divById.get(id)!;
  return d.curriculum.map((t) => byId.get(t)!).filter(Boolean);
}

export const EPISTEMIC_LABELS: Record<Topic['status'], { label: string; description: string }> = {
  established: { label: 'Established mathematics', description: 'Externally established and cited to standard references.' },
  house: { label: 'House construction', description: 'Defined by the co-founders or on this site. Not externally established; read the definition, not the name.' },
  conjecture: { label: 'Conjecture', description: 'Stated but not proved.' },
  application: { label: 'Application in development', description: 'A project by the co-founders; only its general mathematics is taught here.' },
  mythology: { label: 'Campus mythology', description: 'Fiction that stages the mathematics: architecture, residents, portals.' },
};
