/**
 * Bundle labels are furniture on a custom edge type. G6's picker often never
 * delivers pointer events for them even when `labelPointerEvents` is set,
 * because the stroke opts out and the label group does not always participate
 * in the same hit-test path as the product canvas's AmbientLinkageEdge.
 *
 * So the count is found in canvas space: the label the renderer already drew is
 * the authority for where "3 assertions" lives.
 *
 * This runs once per click. It used to run on every `pointermove`, scanning the
 * whole edge list against the pointer, because the count opened on hover —
 * which is the interaction that went away.
 */

import type { Graph } from "@antv/g6";

type Bounds = {
  min: [number, number, number];
  max: [number, number, number];
};

function pointInBounds(x: number, y: number, bounds: Bounds, pad = 4) {
  return (
    x >= bounds.min[0] - pad &&
    x <= bounds.max[0] + pad &&
    y >= bounds.min[1] - pad &&
    y <= bounds.max[1] + pad
  );
}

/** The bundle count under the pointer, if any. */
export function bundleUnderPointer(
  graph: Graph,
  clientX: number,
  clientY: number,
): string | null {
  const [x, y] = graph.getCanvasByClient([clientX, clientY]);
  for (const edge of graph.getEdgeData()) {
    const id = String(edge.id);
    if (!id.startsWith("bundle:")) continue;
    const style = graph.getElementRenderStyle(id);
    if (Number(style.labelOpacity ?? 0) < 0.5) continue;
    const element = (
      graph as unknown as {
        context?: { element?: { getElement: (id: string) => unknown } };
      }
    ).context?.element?.getElement(id);
    if (!element || typeof element !== "object") continue;
    const label = (element as { shapeMap?: { label?: { getRenderBounds: () => Bounds } } })
      .shapeMap?.label;
    if (!label) continue;
    const bounds = label.getRenderBounds();
    if (pointInBounds(x, y, bounds)) return id;
  }
  return null;
}
