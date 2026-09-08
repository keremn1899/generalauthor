/**
 * The TABLES dock's subject chrome.
 *
 * World and frontier are places in one panel, not extra surfaces. The handle
 * still says Tables; these buttons say which list you are in. A relation or
 * derivation is a subject you navigated to — named in the bar, not a third
 * tab — and world / frontier are how you leave it.
 */

import type { ReactNode } from "react";
import { PanelClose } from "./panelChrome";

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
            {/*
              * The list is of unresolved obligations, so the tab says
              * unresolved. "Frontier" is the right word for the *set* — it is
              * what moves as a world is built, and the docstrings keep it —
              * but as a tab beside `world` it named a concept rather than a
              * place, and a reader had to already know the theory to guess
              * what was behind it.
              */}
            unresolved
          </button>
        ) : null}
      </nav>
      {/*
        * The two of them in one box, and the box takes the free space rather
        * than the text's width. That is what makes the fade honest: the mask
        * eats the last stretch of the *box*, so a name that fits ends well
        * before it and only a name that has run out of room is faded away.
        */}
      {title || meta ? (
        <div className="table__said">
          {title ? <b>{title}</b> : null}
          {meta ? <span className="table__meta">{meta}</span> : null}
        </div>
      ) : null}
      <div className="table__actions">
        {children}
        <PanelClose onClose={chrome.onClose} />
      </div>
    </header>
  );
}

/** Search is local to the table subject, independent of the global finder. */
export function TableSearch({ value, onChange, label }: {
  value: string;
  onChange: (value: string) => void;
  label: string;
}) {
  return <div className="table__search">
    <input type="search" aria-label={label} placeholder={label} value={value}
      onChange={(event) => onChange(event.target.value)}
      onKeyDown={(event) => {
        if (event.key === "Escape" && value) {
          event.stopPropagation();
          onChange("");
        }
      }} />
    {value ? <button type="button" onClick={() => onChange("")}>clear search</button> : null}
  </div>;
}
