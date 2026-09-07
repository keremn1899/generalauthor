/**
 * The show filters, as one component rather than three copies.
 *
 * Collapsed it is one cell, `filter`. Hover or click opens the keys above it
 * — the same geometry the marks are drawn with, so the legend and the field
 * agree without either naming a colour. The keys must not join the instrument
 * row: that row is centred, and growing it would move the cell out from under
 * the pointer.
 */

import { useEffect, useRef, useState } from "react";
import { SHOW_LAYERS, type ShowState } from "./show";

export type ShowBandProps = {
  show: ShowState;
  onShow: (next: (current: ShowState) => ShowState) => void;
  /**
   * The names toggle, where the surface offers one.
   *
   * Omitted on a field that is already naming everything, because a control
   * that reports a state it cannot change is worse than no control.
   */
  names?: { on: boolean; onToggle: () => void };
  /**
   * The spread toggle, where the surface offers one.
   *
   * It sits with the filters because it is the same kind of control — a
   * statement about what the field draws, not about what the world says — and
   * it is omitted on a surface with no field for it to act on.
   */
  spread?: { on: boolean; onToggle: () => void };
};

export function ShowBand({ show, onShow, names, spread }: ShowBandProps) {
  const [pinned, setPinned] = useState(false);
  const [hovered, setHovered] = useState(false);
  const suppressHover = useRef(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const open = pinned || hovered;

  useEffect(() => {
    if (!pinned) return;
    const close = (event: PointerEvent) => {
      if (rootRef.current?.contains(event.target as Node)) return;
      setPinned(false);
    };
    document.addEventListener("pointerdown", close, true);
    return () => document.removeEventListener("pointerdown", close, true);
  }, [pinned]);

  return (
    <div
      ref={rootRef}
      className={`world-filter${open ? " is-open" : ""}`}
      onMouseEnter={() => {
        if (suppressHover.current) return;
        setHovered(true);
      }}
      onMouseLeave={() => {
        suppressHover.current = false;
        setHovered(false);
      }}
    >
      <div className="instrument__group">
        <button
          type="button"
          className="world-filter__summary"
          aria-expanded={open}
          aria-haspopup="true"
          onClick={() => {
            if (pinned) {
              setPinned(false);
              suppressHover.current = true;
              setHovered(false);
              return;
            }
            setPinned(true);
          }}
        >
          filter
        </button>
      </div>
      <div className="world-filter__menu">
        <div className="instrument__group" role="group" aria-label="Filter">
          {SHOW_LAYERS.map((layer) => (
            <button
              key={layer}
              type="button"
              className="world-show__filter"
              data-layer={layer}
              aria-pressed={show[layer]}
              title={`${show[layer] ? "Hide" : "Show"} ${layer} assertions`}
              onClick={() =>
                onShow((current) => ({ ...current, [layer]: !current[layer] }))
              }
            >
              <span className="world-show__key" aria-hidden="true" />
              <span className="world-show__name">{layer}</span>
            </button>
          ))}
          {names ? (
            <button
              type="button"
              className="world-show__filter"
              data-layer="names"
              aria-pressed={names.on}
              title={names.on ? "Show names on focus only" : "Keep names visible"}
              onClick={names.onToggle}
            >
              <span className="world-show__key" aria-hidden="true" />
              <span className="world-show__name">names</span>
            </button>
          ) : null}
          {spread ? (
            <button
              type="button"
              className="world-show__filter"
              data-layer="spread"
              aria-pressed={spread.on}
              title={
                spread.on
                  ? "Keep a selected mark's filaments straight, names stacked"
                  : "Spread a selected mark's filaments so their names clear"
              }
              onClick={spread.onToggle}
            >
              <span className="world-show__key" aria-hidden="true" />
              <span className="world-show__name">spread</span>
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
