/**
 * The lab's form controls.
 *
 * Fourteen native inputs were doing this before: pill tracks, round thumbs,
 * an `accent-color` and a browser tick, inside a product whose whole language
 * is a sharp corner and one weight of Jost. They were the loudest un-designed
 * thing on the page, and every one of them was written out longhand at its
 * call site, so they were also fourteen chances to drift apart.
 *
 * These live in the lab and only in the lab. The product has no sliders yet,
 * and it should not acquire them by having a nice one available.
 *
 * Two notes on where they sit relative to the laws:
 *
 * - A thumb tracks the pointer and must never tween — a control that lags the
 *   finger dragging it is a control lying about where the value is. The only
 *   motion here is `hold` on the press, which is the spine's shortest plan and
 *   is caused by the person pressing.
 * - The focus ring appears instantly: `focusIsWhereYouAre` in `motion.ts`.
 */
import type { ReactNode } from "react";

/**
 * The filled portion, as a percentage, handed to CSS.
 *
 * A range input cannot paint how far along it is on its own — the track is
 * one shape and the browser will not tell a stylesheet where the thumb got
 * to. So the fill is computed here and passed down as a custom property,
 * which is the only reason this needs to be a component at all.
 */
function fillPercent(value: number, min: number, max: number) {
  if (max === min) return 0;
  return ((value - min) / (max - min)) * 100;
}

export function LabRange({
  label,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: ReactNode;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="ctrl-range">
      <span>{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        style={{ "--ctrl-fill": `${fillPercent(value, min, max)}%` } as React.CSSProperties}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}

export function LabToggle({
  label,
  checked,
  onChange,
}: {
  label: ReactNode;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="ctrl-toggle">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span>{label}</span>
    </label>
  );
}
