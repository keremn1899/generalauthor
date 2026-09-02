/**
 * The local planes, spoken to.
 *
 * Two servers answer this front end — `/world` reads a compiled World, and
 * `/construction` reads one constructor run and appends verdicts to a ledger.
 * They share a process, a bearer and an error envelope, so they share this.
 *
 * `read` and `send` are separate exports rather than one function with a
 * method argument, and that is the point of the file: `world.ts` imports
 * `read` and nothing else, so its claim to have no write path is visible in
 * its import list rather than asserted in its docstring.
 */

/**
 * The token, read from the URL the way the rest of the product reads it.
 *
 * `#/world?apiToken=devtoken` — same habit as the operator plane, so one dev
 * server and one bookmark serve both while both exist.
 */
export function tokenFromLocation(): string | null {
  const hash = window.location.hash;
  const query = hash.includes("?") ? hash.slice(hash.indexOf("?") + 1) : "";
  const params = new URLSearchParams(query || window.location.search);
  return params.get("apiToken");
}

async function unwrap<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `${response.status}`;
    try {
      detail = ((await response.json()) as { error?: string }).error ?? detail;
    } catch {
      /* a body that is not JSON is still a failure worth reporting */
    }
    // The server's sentence, not ours. A refused verdict says why it was
    // refused — "SAME_ENTITY needs at least one cited location from the
    // packet" — and rewriting that into "Request failed" would throw away the
    // only part a person can act on.
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export async function read<T>(path: string): Promise<T> {
  const token = tokenFromLocation();
  return unwrap<T>(
    await fetch(path, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    }),
  );
}

export async function send<T>(path: string, body: unknown): Promise<T> {
  const token = tokenFromLocation();
  return unwrap<T>(
    await fetch(path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    }),
  );
}
