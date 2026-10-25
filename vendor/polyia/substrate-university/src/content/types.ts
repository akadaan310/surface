// The university registry schema. Browser-readable, typed and extensible.

export type DivisionId = 'foundations' | 'relational' | 'languages' | 'geometry' | 'acoustic' | 'worlds';

/**
 * Epistemic label carried by every definition and topic.
 *  established   externally established mathematics, with a citation
 *  house         a Substrate University / co-founder construction: defined here, not externally established
 *  conjecture    a stated but unproven claim
 *  application   an application or project in development
 *  mythology     campus fiction: architecture, characters and portals that stage the mathematics
 */
export type Epistemic = 'established' | 'house' | 'conjecture' | 'application' | 'mythology';

export type SourceStatus =
  | 'published-book' // a public manuscript with stable URL
  | 'public-repository' // a public research repository
  | 'textbook' // an external standard reference
  | 'paper' // an external paper
  | 'defined-here' // no public source yet; this site is the first statement
  | 'in-development'; // an application without public material yet

export interface Source {
  title: string;
  authors: string;
  year?: number;
  url?: string;
  status: SourceStatus;
  locator?: string;
}

export interface Definition {
  term: string;
  text: string;
  status: Epistemic;
}

export interface Example {
  title: string;
  body: string;
  /** Optional computation reference, e.g. 'numbers:divide:Z:0:0'. */
  compute?: string;
}

export interface Topic {
  id: string;
  division: DivisionId;
  subject: string;
  title: string;
  level: 'entry' | 'intermediate' | 'advanced';
  status: Epistemic;
  summary: string;
  definitions: Definition[];
  constraints: string[];
  examples: Example[];
  prerequisites: string[];
  transformations: string[];
  visualLesson: string;
  challenge: { prompt: string; hint: string; answer: string };
  sources: Source[];
  sourceStatus: SourceStatus;
  /** Which exhibit adapter renders this topic's computation. */
  domainAdapter: ExhibitId | null;
  glossary: string[];
}

export type ExhibitId = 'bridge-grammar' | 'fold' | 'address-compiler' | 'image-sculpture' | 'interval-ring' | 'world-loom';

export interface Division {
  id: DivisionId;
  numeral: string;
  door: string; // the in-world name of the door
  name: string;
  motto: string;
  glyph: string;
  accent: string;
  description: string;
  exhibit: ExhibitId;
  exhibitTitle: string;
  curriculum: string[]; // topic ids in suggested order
}
