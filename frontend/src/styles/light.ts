/**
 * Light — the second law of the field.
 *
 * `motion.ts` is gravity: `emit` is a body given exactly the escape impulse
 * gravity spends at its home, `absorb` is constant acceleration from rest,
 * `settle` is an analytic damped spring. Those are not metaphors, and this is
 * meant to be read beside them.
 *
 * A world is dark until someone looks at it. Pointing at a mark makes that
 * mark a source; light falls off from it through the field, and what is far
 * from what you are doing falls to ambient. So illumination is not decoration
 * layered on top of an interaction — **it is the interaction, drawn.** Nothing
 * is lit that a person did not light.
 *
 * Three commitments make it honest:
 *
 * **Distance is measured in the field, not on the screen.** Two marks a
 * thousand pixels apart but joined by one relation are neighbours; two marks
 * touching on screen and joined by nothing are not. The field is a graph, so
 * hops are what "near" means here. Zooming does not change what is lit.
 *
 * **Light is opacity, never colour.** Colour is for status only, and geometry
 * carries construction origin — a mark that changed hue under illumination
 * would be saying something about itself that is not true. Opacity is also
 * the physically correct variable: illumination falls off, matter does not
 * change what it is made of.
 *
 * **Nothing acted on means nothing dimmed.** With no source the field is
 * evenly lit and every mark is at 1, so the law changes nothing at rest. That
 * is the difference between a lamp and a vignette.
 */

export type LightField = {
  /**
   * The floor. Unlit matter is still there — a world does not stop existing
   * because you are looking elsewhere — so this is how much of it you can
   * still read, not zero.
   */
  ambient: number;
  /**
   * Falloff distance, in hops. Inverse square about a source one of these
   * away; larger reaches further.
   */
  falloff: number;
};

export const DEFAULT_LIGHT_FIELD: LightField = {
  ambient: 0.34,
  falloff: 1.6,
};

/**
 * Inverse square from a point source, over graph distance.
 *
 * `incident = 1 / (1 + d/k)²`, then lifted onto the ambient floor. The `1 +`
 * is what keeps a source finite at its own position rather than infinite:
 * a mark is one falloff-unit from its own surface, which is the usual cheap
 * approximation and is the whole of the physics here.
 *
 * `null` distance is a mark the source cannot reach at all — a separate
 * component of the field. It sits at ambient, which is correct: nothing that
 * happened over there reaches it.
 */
export function luminance(
  hops: number | null,
  field: LightField = DEFAULT_LIGHT_FIELD,
): number {
  if (hops === null) return field.ambient;
  const distance = Math.max(0, hops) / Math.max(0.01, field.falloff);
  const incident = 1 / (1 + distance) ** 2;
  return field.ambient + (1 - field.ambient) * incident;
}

/**
 * The brightness at which a mark says its own name.
 *
 * Defined as the light on a neighbour, not as a number: naming has always
 * meant *the mark you touched and the ones it is joined to*, and deriving the
 * cut from the law keeps that true when the law is retuned. Retune `falloff`
 * and the named set does not silently grow.
 */
export function namingCut(field: LightField = DEFAULT_LIGHT_FIELD): number {
  return luminance(1, field) - 1e-9;
}

/**
 * What a mark actually draws at: its own material, under this much light.
 *
 * Reflected, not replaced. A quiet filament authored at 0.4 stays quieter
 * than the disc beside it — illumination scales what a thing already is
 * rather than overwriting it.
 */
export function reflected(albedo: number, incident: number): number {
  return albedo * incident;
}

export function lightCssVariables(field: LightField = DEFAULT_LIGHT_FIELD) {
  return {
    "--light-ambient": String(field.ambient),
    "--light-falloff": String(field.falloff),
  } as const;
}
