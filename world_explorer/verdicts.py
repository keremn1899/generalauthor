"""Human construction proposals — appended beside a run, never into it.

This is the write half of the construction plane, and it is a separate module
from `construction.py` for the reason that module's docstring gives: the reader
can be shown to be read-only by grepping it, and that only stays true if the
writer lives somewhere else.

Three rules hold the shape:

**Append-only.** `§6.4` — an overturned disposition is *superseded*, never
overwritten. The machine's original judgment stays readable because the
disagreement is the most interesting record in the system. So this is a JSONL
ledger: recording is an append, reverting is an append, and nothing here opens
a file for anything but reading and appending.

**Outside the run.** A verdict is written to `data/verdicts/<run>.jsonl`, not
into `passes/05_dispositions.json` and not into a compiled world. A pass
artifact is what the constructor said; editing it would make the run a
transcript of a conversation that never happened. And the campaign directory is
user-owned — a surface that writes into someone's in-flight trial is a surface
that corrupts evidence.

**A proposal is an input to the next build.** Nothing here changes a world.
`THE ONLY PATH FROM A VERDICT TO A WORLD TUPLE IS A REBUILD`, and this ledger is
what the rebuild reads.

The burdens (§6.1) are enforced here rather than in the front end, because a
burden checked only in a form is a burden until someone uses curl.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

#: The verdicts a person may record. `UNRESOLVED` is on the list deliberately:
#: upholding the constructor's decline is a decision, and recording it as one
#: is how the docket shrinks without anything being closed that shouldn't be.
VERDICTS = frozenset(
    {"SAME_ENTITY", "DISTINCT", "ACCEPT", "REJECT", "PRESENT", "ABSENT", "UNRESOLVED"}
)

#: Verdicts that close an obligation, and therefore carry the burden. Kept
#: beside `construction.CLOSING` rather than imported from it: they agree today,
#: but one is about what the machine wrote and the other about what a person may
#: assert, and a shared constant would hide the day they diverge.
CLOSING = VERDICTS - {"UNRESOLVED"}

ADJUDICATION = "ADJUDICATION"
ADMISSION = "ADMISSION"
REVERT = "REVERT"


class BurdenNotMet(ValueError):
    """A verdict that would close an obligation without establishing it."""


def _citation(entry: Any) -> tuple[str, str]:
    if not isinstance(entry, dict):
        raise BurdenNotMet("a citation is a source_path and a location")
    source = str(entry.get("source_path", "")).strip()
    location = str(entry.get("location", "")).strip()
    if not source or not location:
        raise BurdenNotMet("a citation needs both a source_path and a location")
    return (source, location)


def citable(packet: dict[str, Any] | None) -> set[tuple[str, str]]:
    """Every location a verdict on this obligation may cite.

    §8.2: evidence is cited by selection, never retyped. The set is computed
    from the packet the constructor actually assembled, so a person cannot
    introduce evidence the constructor never saw — that is an amendment (§6.3),
    a different and much more expensive act.
    """
    observations = (packet or {}).get("selected_observations") or []
    allowed: set[tuple[str, str]] = set()
    for observation in observations:
        if isinstance(observation, dict):
            source = str(observation.get("source_path", "")).strip()
            location = str(observation.get("location", "")).strip()
            if source and location:
                allowed.add((source, location))
    return allowed


class VerdictLedger:
    """One run's human verdicts, in the order they were made."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    # -- reading ------------------------------------------------------------

    def entries(self) -> list[dict[str, Any]]:
        """Every record, oldest first. A malformed line is skipped rather than
        fatal: the ledger is the audit trail, and losing the whole trail to one
        bad line is the wrong failure."""
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
        return records

    def history(self, obligation_id: str) -> list[dict[str, Any]]:
        return [
            record
            for record in self.entries()
            if record.get("obligation_id") == obligation_id
        ]

    def current(self) -> dict[str, dict[str, Any]]:
        """The verdict standing for each obligation right now.

        A fold rather than a lookup, because the file is the history: the last
        record for an obligation wins, and a `REVERT` leaves nothing standing —
        the machine's disposition is current again, which is §15's revert case.
        """
        standing: dict[str, dict[str, Any]] = {}
        for record in self.entries():
            obligation_id = str(record.get("obligation_id", ""))
            if not obligation_id:
                continue
            if record.get("kind") == REVERT:
                standing.pop(obligation_id, None)
            else:
                standing[obligation_id] = record
        return standing

    def current_admissions(self) -> dict[str, dict[str, Any]]:
        """The latest proposed admission for each relation.

        Admission changes share this ledger because they have the same audit
        and ownership boundary as adjudications: append-only, beside the run,
        and inert until a rebuild. They do not share ``current()`` because an
        obligation id and a relation name are different namespaces and, more
        importantly, intervene at different passes.
        """
        standing: dict[str, dict[str, Any]] = {}
        for record in self.entries():
            relation = str(record.get("relation", ""))
            if record.get("kind") == ADMISSION and relation:
                standing[relation] = record
        return standing

    # -- writing ------------------------------------------------------------

    def _append(self, record: dict[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as ledger:
            ledger.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def record(
        self,
        obligation_id: str,
        disposition: str,
        *,
        allowed_citations: Iterable[tuple[str, str]],
        supporting_evidence: Iterable[dict[str, Any]] = (),
        support_claim: str = "",
        supersedes: str | None = None,
        actor: str = "",
    ) -> dict[str, Any]:
        """Record one adjudication, or refuse it.

        `allowed_citations` is required, not optional, and comes from the
        packet. There is deliberately no way to call this that skips it: an
        argument with a permissive default is a burden that evaporates at the
        first caller who forgets.
        """
        if disposition not in VERDICTS:
            raise ValueError(f"{disposition!r} is not a verdict a person may record")
        if not actor.strip():
            raise ValueError("a verdict is someone's; actor is required")

        allowed = set(allowed_citations)
        cited = [_citation(entry) for entry in supporting_evidence]
        outside = sorted({entry for entry in cited if entry not in allowed})
        if outside:
            # Not a burden failure but a category error: this is evidence the
            # constructor never assembled, and admitting it here would let the
            # cheap intervention quietly do the expensive one's job.
            named = ", ".join(f"{source}:{location}" for source, location in outside)
            raise BurdenNotMet(f"not in this obligation's packet: {named}")

        if disposition in CLOSING:
            # §6.1 — the burdens do not relax for a human. Absence still does
            # not establish distinctness, and a person who cannot cite a
            # location cannot close the obligation. The correct outcome of an
            # unclear packet is that it stays UNRESOLVED.
            if not cited:
                raise BurdenNotMet(
                    f"{disposition} needs at least one cited location from the packet"
                )
            if not support_claim.strip():
                raise BurdenNotMet(
                    f"{disposition} needs a support_claim: what the cited evidence establishes"
                )

        return self._append(
            {
                "kind": ADJUDICATION,
                "obligation_id": obligation_id,
                "disposition": disposition,
                "supporting_evidence": [
                    {"source_path": source, "location": location}
                    for source, location in cited
                ],
                "support_claim": support_claim.strip(),
                "supersedes": supersedes,
                "actor": actor.strip(),
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )

    def revert(self, obligation_id: str, *, actor: str = "") -> dict[str, Any]:
        """Withdraw the standing verdict. The machine's disposition is current
        again, and both the verdict and its withdrawal stay in the file."""
        if not actor.strip():
            raise ValueError("a revert is someone's; actor is required")
        standing = self.current().get(obligation_id)
        if standing is None:
            raise KeyError(f"no standing verdict on {obligation_id!r} to revert")
        return self._append(
            {
                "kind": REVERT,
                "obligation_id": obligation_id,
                "reverts": standing.get("disposition"),
                "actor": actor.strip(),
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )

    def admit(
        self,
        relation: str,
        admission: str,
        *,
        reason: str,
        purpose_independence_test: str,
        supersedes: str | None,
        actor: str,
    ) -> dict[str, Any]:
        """Stage one WORLD/PURPOSE admission change.

        This changes no artifact and no compiled World. The explanatory fields
        are mandatory because moving a card without the test would record a
        conclusion while dropping the argument §6.2 says the reviewer owns.
        """
        relation = relation.strip()
        admission = admission.strip().upper()
        if not relation:
            raise ValueError("relation is required")
        if admission not in {"WORLD", "PURPOSE"}:
            raise ValueError("admission must be WORLD or PURPOSE")
        if not reason.strip():
            raise ValueError("an admission change needs a reason")
        if not purpose_independence_test.strip():
            raise ValueError("an admission change needs a purpose_independence_test")
        if not actor.strip():
            raise ValueError("an admission change is someone's; actor is required")
        if supersedes == admission:
            raise ValueError(f"{relation} is already admitted {admission}")
        return self._append(
            {
                "kind": ADMISSION,
                "relation": relation,
                "admission": admission,
                "reason": reason.strip(),
                "purpose_independence_test": purpose_independence_test.strip(),
                "supersedes": supersedes,
                "actor": actor.strip(),
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )
