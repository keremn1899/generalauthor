/**
 * The only `flow` in the product.
 *
 * `flow` is for CONTINUES: unbounded, indeterminate, no honest midpoint to
 * draw. Retrieval and traversal do not call a model, so nothing on the read
 * plane qualifies — the world is already compiled and every answer is a
 * lookup. Recording a verdict is the exception. It is a write, it is bounded
 * but indeterminate, and it is the one moment a person is waiting on the
 * product rather than reading it.
 *
 * Geometry, not colour: a rule that sweeps. It says *still going*, and it
 * deliberately says nothing about how far along it is, because nothing here
 * knows that.
 */
export function Waiting({ label }: { label: string }) {
  return (
    <p className="waiting" role="status" aria-live="polite">
      <span className="waiting__rule" aria-hidden />
      <span className="waiting__label">{label}</span>
    </p>
  );
}
