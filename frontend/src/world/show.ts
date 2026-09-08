/**
 * §9 SHOW, and the epistemic overlay that rides the same marks.
 *
 * Construction origin (who decided this) and derivation mode (how it is
 * maintained) are different questions, and SHOW is the first: four layers the
 * spec names, with mechanical off by default because it overwhelms the
 * semantic seams — at S100 that is not a preference, it is the difference
 * between a vocabulary and a pile.
 *
 * Completeness and staleness are not layers. They are a condition of a
 * relation, painted over whatever layer the mark already belongs to. A missing
 * receipt is not UNKNOWN: UNKNOWN is a declared status, and a BASE relation
 * that was never given a completeness claim is simply not in that vocabulary.
 */

import type { WorldRelation } from "../api/world";

export type ShowLayer =
  | "semantic"
  | "derived"
  | "mechanical"
  | "unresolved"
  | "adjudicated";

export type ShowState = Record<ShowLayer, boolean>;

export const SHOW_ORIGIN_LAYERS: ShowLayer[] = [
  "semantic",
  "adjudicated",
  "derived",
  "mechanical",
];

export const SHOW_LAYERS: ShowLayer[] = [
  ...SHOW_ORIGIN_LAYERS,
  "unresolved",
];

/**
 * The spec's useful defaults. Mechanical is the one that starts off.
 *
 * `adjudicated` is on and should stay on. A person must never have to opt in
 * to seeing which parts of a world a person decided — a hidden human judgment
 * reads as the machine's, which is the whole reason the origin exists.
 */
export const SHOW_DEFAULT: ShowState = {
  semantic: true,
  adjudicated: true,
  derived: true,
  mechanical: false,
  unresolved: true,
};

export type CompletenessStatus = "COMPLETE" | "INCOMPLETE" | "UNKNOWN";

/**
 * One layer for one assertion. A tuple is not in two layers at once: origin
 * ADJUDICATED is a person's, origin SEMANTIC is the constructor's even if it
 * later feeds a derivation, origin DERIVED (or a derived relation whose origin
 * was not recorded) is computed, and everything else — MECHANICAL, UNKNOWN, an
 * empty BASE — is mechanical.
 *
 * ADJUDICATED is tested before the derivation mode, unlike SEMANTIC, and the
 * asymmetry is deliberate: a human verdict that later feeds a derivation is
 * still a human verdict, and folding it into `derived` would hide the one fact
 * this axis exists to keep visible.
 */
export function layerOf(origin: string, mode: string): ShowLayer {
  if (origin === "ADJUDICATED") return "adjudicated";
  if (origin === "SEMANTIC") return "semantic";
  if (origin === "DERIVED" || mode === "DERIVED") return "derived";
  return "mechanical";
}

/** The layers a schema relation occupies, from the origins the adapter sampled. */
export function layersOfRelation(relation: WorldRelation): ShowLayer[] {
  if (relation.mode === "DERIVED") return ["derived"];
  const origins = relation.origins ?? [];
  if (!origins.length) return ["mechanical"];
  return [...new Set(origins.map((origin) => layerOf(origin, relation.mode)))];
}

export function relationShown(relation: WorldRelation, show: ShowState): boolean {
  return layersOfRelation(relation).some((layer) => show[layer]);
}

export function assertionShown(
  origin: string,
  mode: string,
  show: ShowState,
): boolean {
  return show[layerOf(origin, mode)];
}

/**
 * Turn on every layer a relation occupies.
 *
 * SHOW hides what nobody asked for, and asking for one thing is not asking for
 * a layer. Placing a named row, or opening a named relation, is a request for
 * *that mark* and nothing else would arrive, so the layer comes on. Expanding
 * through a relation is a request for a neighborhood: the referents land and
 * are drawn whatever the filter says, and the tuple that carried them stays
 * hidden until someone turns its layer back on. A filter that a side effect
 * can switch off is not a filter.
 */
export function reveal(relation: WorldRelation, show: ShowState): ShowState {
  const next = { ...show };
  for (const layer of layersOfRelation(relation)) next[layer] = true;
  return next;
}

/**
 * Whether a relation's matter should take the provisional palette.
 *
 * Stale: the derivation's inputs have moved since it last ran. Incomplete:
 * a completeness receipt exists and does not claim COMPLETE. The two are
 * different facts and the inspector names which; on the canvas they share
 * the palette the DNA already spent on "present, not settled".
 */
export function unsettled(
  stale: boolean,
  completeness: CompletenessStatus | null,
): boolean {
  return stale || (completeness !== null && completeness !== "COMPLETE");
}
