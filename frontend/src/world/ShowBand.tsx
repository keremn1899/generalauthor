/**
 * The show filters, as one component rather than three copies.
 *
 * This markup was written out in `WorldPage` once and in `WorldLabPage` twice,
 * and the copies had already drifted: the lab's had lost the titles that say
 * what each key does, and the rule that the names toggle only appears where
 * names are not already the default. A design surface reporting a band the
 * product does not have is the failure mode the lab exists to prevent.
 *
 * The key is a filled or hollow rectangle — the same geometry the mark it
 * filters is drawn with, so the legend and the field agree without either
 * naming a colour.
 */

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
};

export function ShowBand({ show, onShow, names }: ShowBandProps) {
  return (
    <div className="instrument__group" role="group" aria-label="Show">
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
          <span>{layer}</span>
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
          <span>names</span>
        </button>
      ) : null}
    </div>
  );
}
