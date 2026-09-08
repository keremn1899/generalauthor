/**
 * The schema graph — a World's vocabulary as a picture.
 *
 * This is §7.1, and it is the only whole-World view the spec allows: a schema
 * is a dozen relations no matter how many tuples they hold, so it is safe to
 * draw entire where an extension never is. It answers the first question a
 * person has — *what kind of world is this?* — before they have anything to
 * search for.
 *
 * The same projection rule runs here as at instance level, which is what makes
 * the zoom feel like zoom rather than like four different applications: two
 * referent roles collapse onto a filament with the relation's chip on it, three
 * or more stand the chip on the field with a spoke per role, and a scalar role
 * never becomes a node at all. `projectionOf` decides, once, for both.
 *
 * Layout is deterministic and computed here rather than forced. The graph is
 * five kind discs and twenty chips; a force pass would settle somewhere
 * different on every load, and a schema that rearranges itself when you reopen
 * it is a schema you cannot learn the shape of. Kinds sit on a ring, and each
 * relation sits at the centroid of the kinds it connects, pushed off along the
 * perpendicular when several relations share the same pair — which is what
 * keeps `listing_of` and `offered_by` from landing on top of each other.
 */

import type { WorldRelation } from "../api/world";
import {
  bondLabelLayout,
  bondLabelStep,
  chipNode,
  discNode,
  discRim,
  filamentEdge,
  plateRim,
  projectionOf,
  shelfNode,
  spokeEdge,
  spokeLabelStation,
  SPOKE_LABEL_ALONG_PX,
  type ChipKind,
  type MarkParams,
  type Paint,
} from "./marks";
import { unsettled } from "./show";

export type SchemaLayout = {
  /** Relations with no place on the canvas: scalar properties of one kind. */
  fields: Map<string, WorldRelation[]>;
  data: { nodes: unknown[]; edges: unknown[] };
};

type Point = { x: number; y: number };

const RING_MIN = 260;
const RING_PER_KIND = 42;
/** How far apart relations that connect the same kinds are pushed. */
const SIBLING_SPREAD = 46;
/** Clearance between a disc and the first relation hanging off it alone. */
const SATELLITE_GAP = 54;

function kindOf(role: { kinds?: string[] }): string | null {
  return role.kinds && role.kinds.length ? role.kinds[0] : null;
}

/** Construction origin decides the plate; derived still gets the shelf.
 *
 * A relation carries the origins of every tuple under it, so the test is
 * whether any of them was adjudicated, not whether all of them were: one human
 * verdict in a relation is the fact worth seeing from the schema, and reading
 * it as machine-made because its neighbours were is the error that matters.
 *
 * Exported because the reader header names the same fact in words, and a
 * panel that disagreed with the canvas beside it would be worse than either.
 */
export function chipKind(relation: WorldRelation): ChipKind {
  const origins = relation.origins ?? [];
  if (origins.includes("ADJUDICATED")) return "adjudicated";
  return origins.includes("SEMANTIC") ? "semantic" : "mechanical";
}

/**
 * The rules a chip carries: a shelf under a derivation, a crown over a human
 * verdict. Both can be true of one relation, and the two are the same shape
 * mirrored, so they are emitted from one place rather than tested twice.
 */
function furniture(
  relation: WorldRelation,
  kind: ChipKind,
  at: Point,
  paint: Paint,
  params: MarkParams,
): unknown[] {
  const marks: unknown[] = [];
  const plate = `rel:${relation.name}`;
  if (relation.mode === "DERIVED") {
    marks.push(
      shelfNode(`shelf:${plate}`, at.x, at.y, relation.name, paint, params),
    );
  }
  if (kind === "adjudicated") {
    marks.push(
      shelfNode(
        `crown:${plate}`,
        at.x,
        at.y,
        relation.name,
        paint,
        params,
        "over",
      ),
    );
  }
  return marks;
}

/** Every referent namespace the schema mentions, in a stable order. */
export function kindsIn(relations: WorldRelation[]): string[] {
  const seen = new Set<string>();
  for (const relation of relations) {
    for (const role of relation.roles) {
      const kind = kindOf(role);
      if (kind) seen.add(kind);
    }
  }
  return [...seen].sort();
}

function ringPositions(kinds: string[]): Map<string, Point> {
  const radius = Math.max(RING_MIN, RING_PER_KIND * kinds.length);
  return new Map(
    kinds.map((kind, index) => {
      // Starting at twelve o'clock so the first kind alphabetically is always
      // in the same place: the ring is a thing to learn, not to re-read.
      const angle = -Math.PI / 2 + (index * Math.PI * 2) / kinds.length;
      return [
        kind,
        { x: Math.round(Math.cos(angle) * radius), y: Math.round(Math.sin(angle) * radius) },
      ];
    }),
  );
}

function centroid(points: Point[]): Point {
  if (!points.length) return { x: 0, y: 0 };
  return {
    x: points.reduce((sum, p) => sum + p.x, 0) / points.length,
    y: points.reduce((sum, p) => sum + p.y, 0) / points.length,
  };
}

/**
 * Build the schema canvas.
 *
 * `stalePaint` is handed in rather than decided here: an unsettled relation
 * (stale, or a completeness receipt that is not COMPLETE) renders in that
 * palette, and which palette that is belongs to the theme, not to the
 * projection.
 */
/**
 * Which relations stand on each kind.
 *
 * Read off the same `kindOf` the layout uses, so a canvas asking "what is on
 * this disc" and the layout asking "where does this relation hang" cannot come
 * to different answers about the same role.
 */
export function relationsByKind(
  relations: WorldRelation[],
): Map<string, string[]> {
  const out = new Map<string, string[]>();
  for (const relation of relations) {
    for (const role of relation.roles) {
      if (!role.referent) continue;
      const kind = kindOf(role);
      if (!kind) continue;
      const standing = out.get(kind);
      if (standing) {
        if (!standing.includes(relation.name)) standing.push(relation.name);
      } else {
        out.set(kind, [relation.name]);
      }
    }
  }
  return out;
}

export function schemaLayout(
  relations: WorldRelation[],
  paint: Paint,
  stalePaint: Paint,
  params: MarkParams,
  options: {
    namedAtRest: boolean;
    focused: string | null;
    /**
     * Relations to name because a person is looking at something they are on.
     *
     * A binary relation is drawn as a name on a filament and nothing else, so
     * an unnamed bond is an invisible one — and the only way to name it was to
     * already have it selected, or to turn every name on at once. Hovering a
     * kind now names the bonds that touch it, which is what the field has
     * always done for a disc and its claims.
     */
    lit?: ReadonlySet<string>;
  },
): SchemaLayout {
  const kinds = kindsIn(relations);
  const positions = ringPositions(kinds);
  const nodes: unknown[] = [];
  const edges: unknown[] = [];
  const fields = new Map<string, WorldRelation[]>();

  for (const kind of kinds) {
    const at = positions.get(kind)!;
    nodes.push(discNode(`kind:${kind}`, at.x, at.y, kind, paint, params));
  }

  // Relations that connect the same kinds get pushed apart along the
  // perpendicular of the line between them, in the order they are declared.
  const occupancy = new Map<string, number>();

  for (const relation of relations) {
    const referentRoles = relation.roles.filter((role) => role.referent);
    const projection = projectionOf(relation.arity, relation.referent_arity);
    const roleKinds = referentRoles
      .map((role) => kindOf(role))
      .filter((kind): kind is string => Boolean(kind));

    if (projection === "field" || !roleKinds.length) {
      // §5.4: a scalar property of one kind is a card field, not a node. It is
      // still reported, so the panel can list what a kind carries — dropping it
      // silently would make the canvas look like the whole vocabulary.
      const owner = roleKinds[0] ?? "—";
      fields.set(owner, [...(fields.get(owner) ?? []), relation]);
      continue;
    }

    const anchors = roleKinds.map((kind) => positions.get(kind)!).filter(Boolean);
    const base = centroid(anchors);
    const key = [...roleKinds].sort().join("|");
    const index = occupancy.get(key) ?? 0;
    occupancy.set(key, index + 1);

    // Two *distinct* anchors make a line to hang the chip on. One anchor — or
    // two that resolve to the same disc, which is what `candidate_replacement`
    // (part→part) does — has no line, and placing the chip at the centroid puts
    // it inside the disc. Those hang outside it instead, on the ray pointing
    // away from the middle of the ring, so a kind's own relations gather beside
    // it rather than on it.
    const [first, second] = anchors;
    const spread = anchors.length >= 2 ? { x: second.x - first.x, y: second.y - first.y } : null;
    const distinct = spread && Math.hypot(spread.x, spread.y) > 1;

    let at: Point;
    if (distinct && spread) {
      const length = Math.hypot(spread.x, spread.y);
      // Alternate sides so a pair with several relations fans rather than
      // marching off in one direction.
      const step = Math.ceil(index / 2) * SIBLING_SPREAD * (index % 2 === 0 ? 1 : -1);
      at = {
        x: Math.round(base.x + (-spread.y / length) * step),
        y: Math.round(base.y + (spread.x / length) * step),
      };
    } else {
      const outward = Math.hypot(base.x, base.y) || 1;
      const distance =
        params.discDiameter / 2 + SATELLITE_GAP + index * SIBLING_SPREAD;
      at = {
        x: Math.round(base.x + (base.x / outward) * distance),
        y: Math.round(base.y + (base.y / outward) * distance),
      };
    }

    const chipPaint = unsettled(
      relation.stale,
      relation.completeness?.status ?? null,
    )
      ? stalePaint
      : paint;
    const named =
      options.namedAtRest ||
      options.focused === relation.name ||
      Boolean(options.lit?.has(relation.name));
    const kind = chipKind(relation);

    if (projection === "bond" && distinct) {
      // The chip rides the filament — unless the relation carries furniture,
      // because neither a shelf nor a crown can sit against an edge label. That
      // is the one exception, and it is why a derived or adjudicated binary is
      // legible at rest while a base one is not.
      if (relation.mode === "DERIVED" || kind === "adjudicated") {
        nodes.push(
          chipNode(
            `rel:${relation.name}`,
            at.x,
            at.y,
            relation.name,
            kind,
            chipPaint,
            params,
          ),
          ...furniture(relation, kind, at, chipPaint, params),
        );
        edges.push(
          filamentEdge(
            `${relation.name}:in`,
            `kind:${roleKinds[0]}`,
            `rel:${relation.name}`,
            chipPaint,
            params,
            { named: false },
          ),
          filamentEdge(
            `${relation.name}:out`,
            `rel:${relation.name}`,
            `kind:${roleKinds[1]}`,
            chipPaint,
            params,
            { named: false },
          ),
        );
        continue;
      }
      edges.push(
        filamentEdge(
          `${relation.name}`,
          `kind:${roleKinds[0]}`,
          `kind:${roleKinds[1]}`,
          chipPaint,
          params,
          { label: relation.name, named, kind },
        ),
      );
      continue;
    }

    // Three or more referents meeting, or one referent carrying a compound
    // value: either way the plate stands on the field with a spoke per role.
    nodes.push(
      chipNode(
        `rel:${relation.name}`,
        at.x,
        at.y,
        relation.name,
        kind,
        chipPaint,
        params,
      ),
    );
    nodes.push(...furniture(relation, kind, at, chipPaint, params));
    /**
     * Two roles filled by the same kind run the same route, so they stack.
     *
     * `serial_comparison_pair` takes `earlier_action` and `later_action` from
     * the same disc to the same chip. One station puts both names on the same
     * point, and what a reader saw was two of four role names — the other two
     * exactly underneath. This is the stack a filament already gives parallel
     * claims, centred the same way, for the same reason.
     */
    const sharing = new Map<string, number>();
    for (const role of referentRoles) {
      const kind = kindOf(role);
      if (kind) sharing.set(kind, (sharing.get(kind) ?? 0) + 1);
    }
    const step = bondLabelStep(params);
    const placed = new Map<string, number>();
    referentRoles.forEach((role, roleIndex) => {
      const kind = kindOf(role);
      if (!kind) return;
      const disc = positions.get(kind);
      const seat = placed.get(kind) ?? 0;
      placed.set(kind, seat + 1);
      const middle = ((sharing.get(kind) ?? 1) - 1) / 2;
      /**
       * The station, which this canvas was not asking for at all.
       *
       * With no `labelPlacement` every role name fell to `roleLabelAt` — the
       * midpoint — which is the ratio `SPOKE_LABEL_ALONG_PX` exists to avoid:
       * a name that slides along its own spoke as the marks it names move.
       * The far rim is the chip's, because a spoke ends on a plate.
       */
      const station = disc
        ? bondLabelLayout(
            disc,
            at,
            "source",
            { x: step.x * (seat - middle), y: step.y * (seat - middle) },
            params,
            discRim(params),
            plateRim(relation.name, params),
            SPOKE_LABEL_ALONG_PX,
            spokeLabelStation(role.name, params).halfPlate,
            spokeLabelStation(role.name, params).air,
          )
        : null;
      edges.push(
        spokeEdge(
          `${relation.name}:${role.name}:${roleIndex}`,
          `kind:${kind}`,
          `rel:${relation.name}`,
          chipPaint,
          params,
          {
            role: role.name,
            showRole: options.focused === relation.name,
            labelPlacement: station?.placement,
            labelOffsetX: station?.offsetX,
            labelOffsetY: station?.offsetY,
          },
        ),
      );
    });
  }

  return { fields, data: { nodes, edges } };
}
