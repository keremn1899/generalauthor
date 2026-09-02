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

export type ShowLayer = "semantic" | "derived" | "mechanical" | "unresolved";

export type ShowState = Record<ShowLayer, boolean>;

export const SHOW_LAYERS: ShowLayer[] = [
  "semantic",
  "derived",
  "mechanical",
  "unresolved",
];

/** The spec's useful defaults. Mechanical is the one that starts off. */
export const SHOW_DEFAULT: ShowState = {
  semantic: true,
  derived: true,
  mechanical: false,
  unresolved: true,
};

export type CompletenessStatus = "COMPLETE" | "INCOMPLETE" | "UNKNOWN";

/**
 * One layer for one assertion. A tuple is not in two layers at once: origin
 * SEMANTIC is authored even if it later feeds a derivation, origin DERIVED
 * (or a derived relation whose origin was not recorded) is computed, and
 * everything else — MECHANICAL, UNKNOWN, an empty BASE — is mechanical.
 */
export function layerOf(origin: string, mode: string): ShowLayer {
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
 * SHOW hides what nobody asked for. Expanding a relation, or placing a row of
 * it, is asking — so the layer comes on rather than the marks landing in a
 * working set that draws nothing.
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
