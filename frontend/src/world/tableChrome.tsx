/**
 * The TABLES dock's subject chrome.
 *
 * World and frontier are places in one panel, not extra surfaces. The handle
 * still says Tables; these buttons say which list you are in. A relation or
 * derivation is a subject you navigated to — named in the bar, not a third
 * tab — and world / frontier are how you leave it.
 */

import type { ReactNode } from "react";

export type TableSubject = "world" | "frontier" | "other";

export type TableChrome = {
  current: TableSubject;
  hasFrontier: boolean;
  onWorld: () => void;
  onFrontier: () => void;
  onClose: () => void;
};

export function TableBar({
  chrome,
  title,
  meta,
  children,
}: {
  chrome: TableChrome;
  title?: string;
  meta?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <header className="table__bar">
      <nav className="table__subjects" aria-label="Table subject">
        <button
          type="button"
          aria-pressed={chrome.current === "world"}
          onClick={chrome.onWorld}
        >
          world
        </button>
        {chrome.hasFrontier ? (
          <button
            type="button"
            aria-pressed={chrome.current === "frontier"}
            onClick={chrome.onFrontier}
          >
            frontier
          </button>
        ) : null}
      </nav>
      {title ? <b>{title}</b> : null}
      {meta ? <span className="table__meta">{meta}</span> : null}
      <div className="table__actions">
        {children}
        <button type="button" onClick={chrome.onClose}>
          close
        </button>
      </div>
    </header>
  );
}
