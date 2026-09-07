/**
 * The world's filament — a straight stroke whose held end will fan out.
 *
 * G6's `line` draws source to target and nothing else, which is right at rest:
 * a filament is a claim that two referents are joined, and a curve for its own
 * sake would be decoration on a structural mark.
 *
 * What it cannot do is make room. Every bond and spoke a mark carries stations
 * its plate a fixed 44px out from that mark's rim, so two neighbours sitting a
 * few degrees apart put two names on top of each other — and the moment
 * someone selects a mark is exactly the moment every one of those names is
 * revealed at once. The names are the answer; overlapping, they are not
 * readable.
 *
 * So the filament carries one optional elbow near the held end. Off, the path
 * is the chord it has always been — the same two commands, so nothing about
 * the resting field changes. On, the stroke leaves the mark on a spread angle,
 * reaches its plate's station, and runs straight to the far end from there.
 * The plates travel with their strokes, so what was a pile of names becomes a
 * fan of them; the far end never moves, so nothing about what is joined to
 * what changes.
 *
 * The elbow is renderer state, deliberately not graph data. Where a stroke
 * leaves a mark so its name can be read is presentation — nothing about the
 * world changed — and writing it into the data would make every fan a change
 * to the drawing everyone else reads back.
 *
 * Ported from the product canvas's selection fan; `spread.ts` is the geometry
 * that decides the angles.
 */

import {
  ExtensionCategory,
  Line,
  register,
  type BaseEdgeStyleProps,
  type Graph,
} from "@antv/g6";
import type { Group } from "@antv/g";
import type { PathArray } from "@antv/util";
import type { LabelStyleProps } from "@antv/g6";

export const WORLD_FILAMENT_EDGE = "world-filament";

export type FilamentFan = {
  /** 0 on the chord, 1 fully spread. */
  amount: number;
  /** The spread direction, from the held mark's centre. */
  angle: number;
  /** How far past the held mark's rim the elbow — and its plate — sits. */
  along: number;
  /** Which end is held. The other end does not move. */
  fromSource: boolean;
};

type Vec = [number, number];

function mix(from: number, to: number, amount: number) {
  return from + (to - from) * amount;
}

function mixPoint(from: Vec, to: Vec, amount: number): Vec {
  return [mix(from[0], to[0], amount), mix(from[1], to[1], amount)];
}

/**
 * The plate's resting station: `along` px from the held end, down the chord.
 *
 * `along` unconditionally, capped only at the midpoint — the same rule
 * `bondLabelAlong` holds. A `len * 0.45` cap here would put the fan's elbow at
 * a percentage while the chord it interpolates from is at a distance, so a
 * half-spread plate would sit somewhere neither station named.
 */
function stationOnChord(held: Vec, far: Vec, along: number): Vec {
  const dx = far[0] - held[0];
  const dy = far[1] - held[1];
  const len = Math.hypot(dx, dy);
  if (!(len > 1)) return held;
  const u = Math.min(along, len / 2) / len;
  return [held[0] + dx * u, held[1] + dy * u];
}

/**
 * Live instances, keyed without retaining destroyed graphs.
 *
 * A fan is applied through the renderer rather than `graph.updateEdgeData()`
 * so only the strokes that actually move are touched and G6 is not asked to
 * re-run every style mapper on the field for a presentation change.
 */
const rendered = new WeakMap<Graph, Map<string, WorldFilament>>();

class WorldFilament extends Line {
  private fan: FilamentFan | null = null;

  constructor(options: ConstructorParameters<typeof Line>[0]) {
    super(options);
    const graph = this.context.graph;
    const edges = rendered.get(graph) ?? new Map<string, WorldFilament>();
    edges.set(this.elementId(), this);
    rendered.set(graph, edges);
  }

  public destroy() {
    rendered.get(this.context.graph)?.delete(this.elementId());
    super.destroy();
  }

  private elementId() {
    return String((this as unknown as { id: string }).id);
  }

  public hasFan(next: FilamentFan | null) {
    if (!this.fan && !next) return true;
    if (!this.fan || !next) return false;
    return (
      this.fan.fromSource === next.fromSource &&
      Math.abs(this.fan.amount - next.amount) < 0.012 &&
      Math.abs(this.fan.angle - next.angle) < 0.01 &&
      Math.abs(this.fan.along - next.along) < 0.15
    );
  }

  public setFan(next: FilamentFan | null) {
    const fan = next && next.amount > 0.01 ? next : null;
    if (this.hasFan(fan)) return;
    this.fan = fan;
    this.resync();
  }

  /**
   * Re-read live endpoints into the current fan.
   *
   * The angle is relative to the held mark, not a frozen world point, so a
   * mark that moves takes its fan with it — but G6 moving a node does not by
   * itself ask a custom path to recompute.
   *
   * Not while an end is still nucleating. A body part-way into its arrival has
   * no position yet, `getEndpoints` throws on the nulls, and the throw lands in
   * the spread field's own `requestAnimationFrame` where nothing catches it —
   * so selecting a mark while its neighbours were still arriving took the fan
   * down with it. Skipping is free: the arrival ends in a draw, and the draw
   * asks for this path again.
   */
  public resync() {
    if (!this.placed()) return;
    try {
      // Same attributes, new path: `update` is what makes G6 ask for the key
      // path again. Nothing about the stroke's material is being restated.
      super.update({ ...this.attributes });
    } catch {
      // `placed()` asks the graph where the ends are; G6 resolves them against
      // the node *elements*, and the two disagree for a frame around a draw.
      // The fan is a rest pose — losing one frame of it costs nothing, and the
      // next draw restates it.
    }
  }

  /** Whether both ends have a position the path can actually be drawn between. */
  private placed(): boolean {
    try {
      const graph = this.context.graph;
      const edge = graph?.getEdgeData(this.elementId());
      if (!edge) return false;
      for (const end of [String(edge.source), String(edge.target)]) {
        const at = graph.getElementPosition(end);
        if (!at || !Number.isFinite(at[0]) || !Number.isFinite(at[1])) return false;
      }
      return true;
    } catch {
      return false;
    }
  }

  /**
   * The held mark's centre, and how far its rim sits from it.
   *
   * Read from the graph rather than stored, because the endpoint G6 hands the
   * path is already clipped to whatever shape the mark is — a disc's radius, a
   * plate's edge — and the fan has to leave from that same rim or the stroke
   * would start inside the mark it belongs to.
   */
  private origin(held: Vec): { x: number; y: number; radius: number } | null {
    try {
      const graph = this.context.graph;
      const edge = graph?.getEdgeData(this.elementId());
      if (!edge || !this.fan) return null;
      const heldId =
        this.fan.fromSource === true ? String(edge.source) : String(edge.target);
      const [x, y] = graph.getElementPosition(heldId);
      if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
      const radius = Math.hypot(held[0] - x, held[1] - y);
      return { x, y, radius: radius > 1 ? radius : 12 };
    } catch {
      return null;
    }
  }

  /**
   * Where G6 says this stroke's two ends are, or nothing.
   *
   * `getEndpoints` resolves the endpoint against the *node element*, not
   * against stored data, and it throws outright — "Vectors could not operate
   * due to different dimensions" — whenever that element cannot answer: a body
   * still nucleating, or one being replaced by the draw currently running.
   *
   * Thrown from `getKeyPath` it took down whatever asked for the path: a whole
   * `transitionCanvasData` frame, or the spread field's own
   * `requestAnimationFrame`, where nothing catches it and the fan simply
   * stopped. A stroke whose ends are unknown for one frame is not an error —
   * it is a stroke with nothing to draw yet, and the draw that places those
   * ends will ask again.
   */
  private endpoints(
    attributes: Required<BaseEdgeStyleProps>,
  ): [Vec, Vec] | null {
    let ends: [Vec, Vec] | null = null;
    try {
      ends = this.getEndpoints(attributes) as [Vec, Vec];
    } catch {
      ends = null;
    }
    const usable = (point: Vec | undefined | null): point is Vec =>
      Boolean(point) && Number.isFinite(point![0]) && Number.isFinite(point![1]);
    if (ends && usable(ends[0]) && usable(ends[1])) return ends;
    /**
     * The clipped end failed; the mark's own centre has not.
     *
     * `getConnectionPoint` resolves against the node *element*'s bounds, and
     * those can be empty for a frame — around a draw, or while a body is still
     * nucleating — even though the graph knows exactly where the mark is. Seen
     * directly: `getEndpoints` answering `[[null, null, null], [363, -6, 0]]`
     * for an edge whose source `getElementPosition` reports at
     * `[156.1, 143.6, 0]`.
     *
     * Falling back to the centre draws the chord a little long — it starts at
     * the middle of the disc rather than its rim — which is visibly a stroke
     * in roughly the right place, and self-corrects the moment the bounds come
     * back. Drawing nothing would be a filament silently missing from a claim
     * that exists, and throwing took the whole frame down.
     */
    const graph = this.context.graph;
    const edge = graph?.getEdgeData(this.elementId());
    if (!edge) return null;
    const centre = (id: string): Vec | null => {
      try {
        const at = graph.getElementPosition(id);
        return usable(at as unknown as Vec) ? ([at[0], at[1]] as Vec) : null;
      } catch {
        return null;
      }
    };
    const from = usable(ends?.[0]) ? ends![0] : centre(String(edge.source));
    const to = usable(ends?.[1]) ? ends![1] : centre(String(edge.target));
    return from && to ? [from, to] : null;
  }

  /** The three points the fanned stroke runs through, or null when it is straight. */
  private vertices(
    attributes: Required<BaseEdgeStyleProps>,
  ): { src: Vec; elbow: Vec; tgt: Vec } | null {
    const fan = this.fan;
    if (!fan || fan.amount < 0.01) return null;
    const ends = this.endpoints(attributes);
    if (!ends) return null;
    const [source, target] = ends;
    const held = fan.fromSource ? source : target;
    const far = fan.fromSource ? target : source;
    const origin = this.origin(held);
    if (!origin) return null;
    const ux = Math.cos(fan.angle);
    const uy = Math.sin(fan.angle);
    const rim = mixPoint(
      held,
      [origin.x + ux * origin.radius, origin.y + uy * origin.radius],
      fan.amount,
    );
    const elbow = mixPoint(
      stationOnChord(held, far, fan.along),
      [
        origin.x + ux * (origin.radius + fan.along),
        origin.y + uy * (origin.radius + fan.along),
      ],
      fan.amount,
    );
    return fan.fromSource
      ? { src: rim, elbow, tgt: target }
      : { src: source, elbow, tgt: rim };
  }

  protected getKeyPath(attributes: Required<BaseEdgeStyleProps>): PathArray {
    const ends = this.endpoints(attributes);
    // A lone move-to draws nothing — not even the dot a zero-length line with
    // a round cap would leave behind.
    if (!ends) return [["M", 0, 0]] as PathArray;
    const [source, target] = ends;
    const points = this.vertices(attributes);
    if (!points) {
      return [
        ["M", source[0], source[1]],
        ["L", target[0], target[1]],
      ];
    }
    return [
      ["M", points.src[0], points.src[1]],
      ["L", points.elbow[0], points.elbow[1]],
      ["L", points.tgt[0], points.tgt[1]],
    ];
  }

  protected getKeyStyle(attributes: Required<BaseEdgeStyleProps>) {
    const style = super.getKeyStyle(attributes);
    // The stroke must not steal the pointer from discs or from a label sitting
    // beside it. The edge element stays in the picker tree; only the key path
    // opts out — see `getLabelStyle`.
    return { ...style, pointerEvents: "none" as const };
  }

  protected getLabelStyle(
    attributes: Required<BaseEdgeStyleProps>,
  ): false | LabelStyleProps {
    const attrs = this.placedLabel(attributes) as Record<string, unknown>;
    const style = super.getLabelStyle(attrs as Required<BaseEdgeStyleProps>);
    if (!style) return false;

    const shown = Number(attrs.labelOpacity ?? 0) > 0.01;
    let next: LabelStyleProps = style;
    if (typeof attrs.labelFill === "string") {
      next = { ...next, fill: attrs.labelFill };
    }

    if (!shown) return next;

    // Same contract as AmbientLinkageEdge: the stroke refuses the pointer,
    // so any label that is actually drawn must take it.
    return {
      ...next,
      pointerEvents: "auto" as const,
      cursor: "pointer" as const,
    };
  }

  protected drawLabelShape(
    attributes: Required<BaseEdgeStyleProps>,
    container: Group,
  ) {
    super.drawLabelShape(attributes, container);
    this.paintBundleInk(attributes);
  }

  public update(attributes: Record<string, unknown>) {
    super.update(attributes);
    this.paintBundleInk(attributes as Required<BaseEdgeStyleProps>);
  }

  /** G6's edge theme paints bond ink; furniture must stay lens ink. */
  private paintBundleInk(attributes: Required<BaseEdgeStyleProps>) {
    if (!this.elementId().startsWith("bundle:")) return;
    const fill = (attributes as Record<string, unknown>).labelFill;
    const label = this.shapeMap.label as
      | { getShape?: (name: string) => { attr: (style: Record<string, unknown>) => void } }
      | undefined;
    const text = label?.getShape?.("text");
    if (typeof fill === "string" && text) text.attr({ fill });
  }

  /**
   * Keep the plate on the elbow it was fanned to.
   *
   * `labelPlacement` is a ratio of the *whole* path, and the path just grew a
   * corner, so the ratio the mark authored — a fixed distance expressed
   * against a straight chord — no longer lands on the station. Restating it as
   * the elbow's own share of the path is what makes the name travel with the
   * stroke instead of sliding down it.
   *
   * Only when the plate is on the held side. A bond whose name is stationed at
   * the *other* end — the pointer is on that disc while this one is selected —
   * is not what the fan moved, and dragging its name to this end would be the
   * canvas answering a question nobody asked. The offsets are left alone
   * either way: they are the stack that keeps parallel claims apart.
   */
  private placedLabel(attributes: Required<BaseEdgeStyleProps>) {
    const fan = this.fan;
    const points = this.vertices(attributes);
    if (!fan || !points) return attributes;
    const authored = Number(attributes.labelPlacement);
    if (!Number.isFinite(authored)) return attributes;
    const onHeldSide = fan.fromSource ? authored < 0.5 : authored > 0.5;
    if (!onHeldSide) return attributes;
    const first = Math.hypot(
      points.elbow[0] - points.src[0],
      points.elbow[1] - points.src[1],
    );
    const second = Math.hypot(
      points.tgt[0] - points.elbow[0],
      points.tgt[1] - points.elbow[1],
    );
    const total = first + second;
    if (!(total > 1)) return attributes;
    return { ...attributes, labelPlacement: first / total };
  }
}

export type FilamentFanPatch = FilamentFan & { id: string };

/** Apply the frame's fans. Strokes G6 has already retained are not touched. */
export function updateFilamentFans(graph: Graph, patches: FilamentFanPatch[]) {
  const edges = rendered.get(graph);
  if (!edges) return 0;
  let updated = 0;
  for (const patch of patches) {
    const edge = edges.get(patch.id);
    if (!edge || edge.destroyed) continue;
    const next =
      patch.amount > 0.01
        ? {
            amount: patch.amount,
            angle: patch.angle,
            along: patch.along,
            fromSource: patch.fromSource,
          }
        : null;
    if (edge.hasFan(next)) continue;
    edge.setFan(next);
    updated += 1;
  }
  return updated;
}

/** Put every stroke back on its chord, without waiting out an animation. */
export function clearFilamentFans(graph: Graph) {
  const edges = rendered.get(graph);
  if (!edges) return 0;
  let cleared = 0;
  for (const edge of edges.values()) {
    if (edge.destroyed) continue;
    if (edge.hasFan(null)) continue;
    edge.setFan(null);
    cleared += 1;
  }
  return cleared;
}

let registered = false;

export function ensureWorldFilamentRegistered() {
  if (registered) return;
  register(ExtensionCategory.EDGE, WORLD_FILAMENT_EDGE, WorldFilament);
  registered = true;
}
