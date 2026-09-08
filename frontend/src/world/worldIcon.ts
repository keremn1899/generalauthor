/** A deterministic square mesh. Only the permanent world ID seeds the weave. */
export function worldIconSvg(worldId: string, mode: "light" | "dark" = "light"): string {
  let state = 2166136261;
  for (const byte of new TextEncoder().encode(`world-mesh-v3:${worldId}`)) {
    state = Math.imul(state ^ byte, 16777619) >>> 0;
  }
  const random = () => {
    state += 0x6d2b79f5;
    let n = Math.imul(state ^ (state >>> 15), 1 | state);
    n ^= n + Math.imul(n ^ (n >>> 7), 61 | n);
    return ((n ^ (n >>> 14)) >>> 0) / 4294967296;
  };

  // The 5 × 5 square lattice is shared by every world. Variation comes from
  // regional density: each 2 × 2 block receives zero, one, or two diagonals
  // per cell, so the silhouette stays geometric while the interior rhythm
  // changes.
  const points = Array.from({ length: 25 }, (_, index) => ({
    x: 3 + (index % 5) * 6.5,
    y: 3 + Math.floor(index / 5) * 6.5,
  }));
  const edges: [number, number][] = [];
  for (let index = 0; index < 25; index += 1) {
    if (index % 5 < 4) edges.push([index, index + 1]);
    if (index < 20) edges.push([index, index + 5]);
  }

  // Region levels are deliberately quantized. A hash chooses a density field,
  // not a cloud of independently jittered points.
  const regionLevels = Array.from({ length: 4 }, () => random());
  for (let row = 0; row < 4; row += 1) {
    for (let column = 0; column < 4; column += 1) {
      const level = regionLevels[Math.floor(row / 2) * 2 + Math.floor(column / 2)];
      const topLeft = row * 5 + column;
      const topRight = topLeft + 1;
      const bottomLeft = topLeft + 5;
      const bottomRight = bottomLeft + 1;
      const density = level + (random() - 0.5) * 0.18;
      if (density > 0.42) edges.push([topLeft, bottomRight]);
      if (density > 0.76) edges.push([topRight, bottomLeft]);
    }
  }

  const ink = mode === "dark" ? "#fff" : "#000";
  const paper = mode === "dark" ? "#000" : "#fff";
  const lines = edges
    .map(([from, to]) =>
      `<path d="M${points[from].x} ${points[from].y}L${points[to].x} ${points[to].y}"/>`,
    )
    .join("");
  const knots = points
    .map(({ x, y }) => `<circle cx="${x}" cy="${y}" r="0.82"/>`)
    .join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" fill="${paper}"/><g stroke="${ink}" stroke-width="1.05" stroke-linecap="round">${lines}</g><g fill="${ink}">${knots}</g></svg>`;
}

export function worldIconUrl(worldId: string, mode: "light" | "dark" = "light") {
  return `data:image/svg+xml,${encodeURIComponent(worldIconSvg(worldId, mode))}`;
}
