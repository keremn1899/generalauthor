/**
 * The vocabulary canvas — §7.1.
 *
 * Lifted out of `WorldPage` when the field arrived beside it: two canvases in
 * one component is how one of them ends up with the other's behaviours. This
 * one is read, not arranged — its layout is computed and stable on purpose, so
 * nothing here drags.
 */

import { useEffect, useMemo, useRef } from "react";
import { Graph } from "@antv/g6";
import type { WorldRelation } from "../api/world";
import {
  GRAPH_DNA_PROVISIONAL_THEME,
  GRAPH_DNA_THEME,
  type ThemeMode,
} from "../styles/graphDna";
import { MARK_DEFAULTS, paintOf } from "./marks";
import { schemaLayout } from "./schemaGraph";

export function SchemaCanvas({
  relations,
  mode,
  namedAtRest,
  focused,
  onFocus,
}: {
  relations: WorldRelation[];
  mode: ThemeMode;
  namedAtRest: boolean;
  focused: string | null;
  onFocus: (relation: string | null) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);

  const paint = useMemo(() => paintOf(GRAPH_DNA_THEME[mode]), [mode]);
  const stalePaint = useMemo(
    () => paintOf(GRAPH_DNA_PROVISIONAL_THEME[mode]),
    [mode],
  );
  const layout = useMemo(
    () =>
      schemaLayout(relations, paint, stalePaint, MARK_DEFAULTS, {
        namedAtRest,
        focused,
      }),
    [relations, paint, stalePaint, namedAtRest, focused],
  );

  useEffect(() => {
    const host = hostRef.current;
    if (!host || !relations.length) return;
    const graph = new Graph({
      container: host,
      data: layout.data as never,
      animation: false,
      autoFit: { type: "view", options: { direction: "both" } },
      padding: 48,
      background: paint.canvas,
      // Pan and zoom, no drag. A vocabulary you can rearrange is one you cannot
      // learn the shape of.
      behaviors: ["zoom-canvas", "drag-canvas"],
    });

    const idOf = (event: unknown): string | null => {
      const target = (event as { target?: { id?: unknown } } | undefined)?.target;
      return typeof target?.id === "string" ? target.id : null;
    };
    graph.on("node:pointerenter", (event) => {
      const id = idOf(event);
      onFocus(id && id.startsWith("rel:") ? id.slice(4) : null);
    });
    graph.on("edge:pointerenter", (event) => {
      const id = idOf(event);
      if (id) onFocus(id.split(":")[0]);
    });
    graph.on("canvas:click", () => onFocus(null));

    void graph.render();
    return () => graph.destroy();
  }, [layout, paint.canvas, relations.length, onFocus]);

  return <div className="world__stage" ref={hostRef} style={{ background: paint.canvas }} />;
}
