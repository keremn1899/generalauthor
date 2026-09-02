/**
 * The field, remembered between visits — in this browser, for this world.
 *
 * A field is not a view of the World. It is a subgraph a person built by
 * asking for things one expansion at a time, and then arranged by hand: the
 * expensive part is not the fetching, it is the reading and the dragging. Until
 * now a reload threw all of it away, which made the canvas a place you visited
 * rather than a place you kept work in.
 *
 * What is stored is display state, and only display state — which marks someone
 * put on the field and where they stand. **It cannot change a claim.** Every
 * tuple in here was read out of the compiled world and is re-read from it on
 * the next visit; nothing restored from this store is evidence of anything, and
 * the world is still the only thing that says what is true. That is also why it
 * lives in the browser rather than on the host, on the same argument as
 * `product/graphPrefs.ts`: this describes one screen, not one operator.
 *
 * Keyed by world **and revision**. A field is a set of assertion ids, and an
 * assertion id means something only within the revision it was read from — a
 * rebuild can retire a tuple, and restoring a mark for one would be the surface
 * asserting something the world no longer does. A new revision therefore starts
 * from an empty field rather than from a plausible-looking old one.
 */

import {
  emptySet,
  type FieldAssertion,
  type FieldBond,
  type FieldDemand,
  type FieldReferent,
  type Point,
  type WorkingSet,
} from "./workingSet";

const STORAGE_PREFIX = "worldir.field";

/** How the working set looks with its Maps and Sets flattened. */
type StoredField = {
  version: 1;
  world: string;
  revision: number;
  referents: [string, FieldReferent][];
  assertions: [string, FieldAssertion][];
  demands: [string, FieldDemand][];
  bonds: FieldBond[];
  positions: [string, Point][];
  expanded: string[];
};

function keyOf(world: string, revision: number): string {
  return `${STORAGE_PREFIX}:${world}:${revision}`;
}

/**
 * Put the field away.
 *
 * An empty field clears the slot rather than storing emptiness, so "take
 * everything off and go back to the vocabulary" is a thing that persists too —
 * otherwise the next visit would restore a field the person had just cleared.
 */
export function writeField(
  world: string,
  revision: number,
  set: WorkingSet,
): void {
  try {
    const key = keyOf(world, revision);
    if (!set.referents.size && !set.assertions.size && !set.demands.size) {
      window.localStorage.removeItem(key);
      return;
    }
    const stored: StoredField = {
      version: 1,
      world,
      revision,
      referents: [...set.referents],
      assertions: [...set.assertions],
      demands: [...set.demands],
      bonds: set.bonds,
      positions: [...set.positions],
      expanded: [...set.expanded],
    };
    window.localStorage.setItem(key, JSON.stringify(stored));
  } catch {
    // Private-mode browsers refuse writes, and a large field can exceed the
    // quota. Either way the field is still on screen; it just will not outlive
    // the tab.
  }
}

/**
 * Take the field back out, or nothing.
 *
 * Anything unreadable — absent, malformed, written by a version of this module
 * that stored a different shape — is nothing rather than a guess. A field
 * assembled from half-understood JSON would put marks on the canvas that no
 * longer mean what they claim to.
 */
export function readField(world: string, revision: number): WorkingSet | null {
  try {
    const raw = window.localStorage.getItem(keyOf(world, revision));
    if (!raw) return null;
    const stored = JSON.parse(raw) as Partial<StoredField>;
    if (
      stored.version !== 1 ||
      stored.world !== world ||
      stored.revision !== revision ||
      !Array.isArray(stored.referents) ||
      !Array.isArray(stored.assertions) ||
      !Array.isArray(stored.demands) ||
      !Array.isArray(stored.bonds) ||
      !Array.isArray(stored.positions) ||
      !Array.isArray(stored.expanded)
    ) {
      return null;
    }
    const set = emptySet();
    for (const [id, referent] of stored.referents) set.referents.set(id, referent);
    for (const [id, assertion] of stored.assertions) set.assertions.set(id, assertion);
    for (const [key, demand] of stored.demands) set.demands.set(key, demand);
    set.bonds = stored.bonds;
    for (const [id, at] of stored.positions) set.positions.set(id, at);
    for (const key of stored.expanded) set.expanded.add(key);
    return set.referents.size ? set : null;
  } catch {
    return null;
  }
}
