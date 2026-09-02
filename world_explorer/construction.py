"""The construction read plane — one frozen constructor run, read.

The companion of `adapter.py`. That one opens a compiled World and answers
questions about what is true; this one opens the *run that built it* and
answers questions about what was decided, by whom, on what evidence, and what
is still open. `constructor_frontend_spec.md` §12 is the contract.

**It cannot write.** There is no method here that opens a file for writing, and
none should be added: a verdict is recorded beside the run by the surface that
takes it (§14 step 3), never into a pass artifact and never into a compiled
world. The reader is the half of the boundary that is checkable by reading the
imports.

**It holds no state.** Every call reads through to the files on disk, for the
same reason the world adapter does: a cache is a second copy of the run with
its own staleness, and a run that is still being written — which is the normal
case in this repository — would be served from a snapshot that quietly stopped
being true. Artifacts are small (a hundred obligations, a hundred packets) and
the whole docket costs a few milliseconds.

A run that is mid-flight is read, not refused. A pass whose artifact is absent
or half-written is reported as absent or unreadable; it never becomes a 500 and
it never becomes an invented state.

**Pass state is not confected here.** §5's CERTIFIED / PROVISIONAL / FAILED /
STALE comes from the scorers, and the front end reports it rather than
conferring it. What this module reports about a pass is what the run itself
recorded: whether the artifact is there, and what the adapter's `agent.json`
said about the process that produced it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

#: Which artifact each pass is answerable for. A directory means the pass
#: writes a file per item; a file means one document. Nothing else in this
#: module knows a pass number, so a tenth pass is one row here.
PASS_ARTIFACTS: dict[str, str] = {
    "p0": "00_intention_contract.json",
    "p1": "01_vocabulary.json",
    "p2": "02_mechanical_report.json",
    "p3": "03_obligations.json",
    "p4": "04_packets",
    "p5": "05_dispositions.json",
    "p6": "06_admission.json",
    "p7": "07_derivations.json",
    "p8": "08_outputs",
}

PASSES: list[str] = list(PASS_ARTIFACTS)

#: Dispositions that close an obligation. Everything else leaves it open, and
#: `UNRESOLVED` is a decision the constructor made, not an absence of one.
CLOSING = frozenset({"SAME_ENTITY", "DISTINCT", "ACCEPT", "REJECT", "PRESENT", "ABSENT"})

#: A purpose output declares itself by its path, `purpose_ir/a/output.json`.
PURPOSE_OUTPUT_PREFIX = "purpose_ir/"


class ArtifactError(ValueError):
    """An artifact is present but could not be read as what it claims to be."""


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        # A run still being written is the normal case here, so a half-flushed
        # artifact is a fact about the run rather than a fault in the reader.
        raise ArtifactError(f"{path.name} is not readable JSON: {error}") from error


class ConstructionReader:
    """One constructor run: a directory holding `passes/p0` … `passes/p8`."""

    def __init__(self, run: Path | str) -> None:
        self.path = Path(run).resolve()
        if not (self.path / "passes").is_dir():
            hint = (
                " — name a trial inside it"
                if (self.path / "trials").is_dir()
                else ""
            )
            raise ValueError(f"{self.path} holds no passes/ directory{hint}")

    # -- reading through ----------------------------------------------------

    def _snapshot(self, pass_id: str) -> Path:
        """Where a pass left the workspace.

        Each pass snapshot is cumulative — p8's holds every artifact — so a
        pass is read from *its own* snapshot rather than the last one. That is
        what makes a mid-flight run legible: p5 is answerable for p5 whether or
        not p6 has run.
        """
        if pass_id not in PASS_ARTIFACTS:
            raise KeyError(f"no pass {pass_id!r} in this construction")
        return self.path / "passes" / pass_id / "workspace_snapshot"

    def _artifact_path(self, pass_id: str) -> Path:
        return self._snapshot(pass_id) / PASS_ARTIFACTS[pass_id]

    def _agent(self, pass_id: str) -> dict[str, Any] | None:
        record = self.path / "passes" / pass_id / "agent.json"
        if not record.exists():
            return None
        try:
            document = _load(record)
        except ArtifactError:
            return None
        # Deliberately narrow. `agent.json` also carries the transcript's tool
        # counts and the isolation preflight; §13 keeps narration off this
        # surface, and what is left is the account of the process, not of the
        # reasoning.
        return {
            "model": document.get("reported_model") or document.get("model"),
            "returncode": document.get("returncode"),
            "timed_out": document.get("timed_out"),
            "finished_at": document.get("finished_at"),
        }

    def _obligations(self) -> list[dict[str, Any]]:
        path = self._artifact_path("p3")
        if not path.exists():
            raise KeyError("this construction has no obligations yet (P3 has not run)")
        document = _load(path)
        if not isinstance(document, list):
            raise ArtifactError("03_obligations.json is not a list of obligations")
        return document

    def _dispositions(self) -> dict[str, dict[str, Any]]:
        """P5's judgments, by obligation. Empty rather than absent if P5 has
        not run — an obligation with no disposition is undecided, which is a
        true statement about a run that stopped at P4."""
        path = self._artifact_path("p5")
        if not path.exists():
            return {}
        document = _load(path)
        if not isinstance(document, list):
            raise ArtifactError("05_dispositions.json is not a list of dispositions")
        return {item["obligation_id"]: item for item in document if "obligation_id" in item}

    def _packet(self, obligation_id: str) -> dict[str, Any] | None:
        path = self._artifact_path("p4") / f"{obligation_id}.json"
        if not path.exists():
            return None
        return _load(path)

    # -- what an obligation blocks ------------------------------------------

    def _blocking(self) -> dict[str, dict[str, set[str]]]:
        """Which relations block which purposes, read from P7.

        P7 declares `blocking_unresolved_state` per derivation: sentences
        saying what an unresolved obligation prevents. They are prose, so the
        reading is a containment test — a relation blocks a derivation when
        the derivation says so by name.

        The prose is the seam and it is worth naming: if P7 ever stops writing
        relation names into those sentences, this ordering silently flattens
        rather than breaking, and the docket goes back to arrival order. That
        is why the docket reports `blocks` per row instead of only sorting by
        it — a reader can see the claim, not just its effect.
        """
        path = self._artifact_path("p7")
        empty: dict[str, dict[str, set[str]]] = {"purposes": {}, "relations": {}}
        if not path.exists():
            return empty
        document = _load(path)
        derivations = document.get("derivations") if isinstance(document, dict) else None
        if not isinstance(derivations, list):
            return empty

        purposes: dict[str, set[str]] = {}
        relations: dict[str, set[str]] = {}
        for derivation in derivations:
            output = str(derivation.get("output_relation", ""))
            sentences = derivation.get("blocking_unresolved_state") or []
            if not sentences:
                continue
            text = " ".join(str(sentence) for sentence in sentences)
            if output.startswith(PURPOSE_OUTPUT_PREFIX):
                # `purpose_ir/a/output.json` → "A", the name P3 uses in
                # `required_by`.
                name = output[len(PURPOSE_OUTPUT_PREFIX) :].split("/")[0].upper()
                purposes[name] = purposes.get(name, set()) | {text}
            else:
                relations[output] = relations.get(output, set()) | {text}
        return {"purposes": purposes, "relations": relations}

    @staticmethod
    def _named_in(relation: str, claims: set[str]) -> bool:
        return any(relation in claim for claim in claims)

    @staticmethod
    def _is_open(
        judgment: dict[str, Any] | None, verdict: dict[str, Any] | None = None
    ) -> bool:
        """An obligation with no disposition is open; so is one the
        constructor decided to leave `UNRESOLVED`. The two are different
        decisions and the docket shows both, but neither is closed.

        A standing human verdict decides it instead, and by the same rule —
        the burdens do not relax for a person (§6.1), so a verdict of
        `UNRESOLVED` upholds the decline and leaves the obligation open. That
        is a decision and the docket records it as one; it is simply not a
        closure.
        """
        decisive = verdict if verdict is not None else judgment
        if decisive is None:
            return True
        return str(decisive.get("disposition")) not in CLOSING

    def _blocks_for(
        self,
        obligation: dict[str, Any],
        blocking: dict[str, dict[str, set[str]]],
        *,
        open_: bool,
    ) -> dict[str, Any]:
        """What one obligation blocks.

        A purpose counts only when P7 names the obligation's relation as
        blocking *and* P3 recorded the obligation as required by that purpose.
        Either half alone overstates it: P7 speaks about relations, and a
        relation blocks a purpose the obligation was never demanded for.

        `blocking` is narrower still, and the artifact names the reason: the
        field is `blocking_unresolved_state`. A decided obligation blocks
        nothing, whatever its relation would block if it were left open. So the
        lists say what this obligation *would* hold up; the flag says whether
        it is holding it up now.
        """
        relation = str(obligation.get("relation", ""))
        required_by = {str(item) for item in obligation.get("required_by") or ()}
        purposes = sorted(
            name
            for name, claims in blocking["purposes"].items()
            if name in required_by and self._named_in(relation, claims)
        )
        relations = sorted(
            output
            for output, claims in blocking["relations"].items()
            if self._named_in(relation, claims)
        )
        return {
            "purposes": purposes,
            "relations": relations,
            "blocking": open_ and bool(purposes),
        }

    # -- §12 the routes -----------------------------------------------------

    def overview(self) -> dict[str, Any]:
        """The run: its passes, their artifacts, and the headline counts.

        No pass is called certified here. `ran`, `artifact` and `agent` are
        what the run recorded about itself; §5's state is the scorers' word and
        arrives with the spine.
        """
        passes: list[dict[str, Any]] = []
        for pass_id in PASSES:
            artifact = self._artifact_path(pass_id)
            entry: dict[str, Any] = {
                "pass": pass_id,
                "artifact": PASS_ARTIFACTS[pass_id],
                "present": artifact.exists(),
                "ran": (self.path / "passes" / pass_id).is_dir(),
                "agent": self._agent(pass_id),
            }
            if artifact.is_dir():
                entry["items"] = len(sorted(artifact.glob("*.json")))
            passes.append(entry)

        counts: dict[str, Any] = {}
        unreadable: list[str] = []
        try:
            obligations = self._obligations()
            counts["obligations"] = len(obligations)
        except (KeyError, ArtifactError) as error:
            obligations = []
            unreadable.append(str(error))
        try:
            dispositions = self._dispositions()
        except ArtifactError as error:
            dispositions = {}
            unreadable.append(str(error))

        by_disposition: dict[str, int] = {}
        for item in dispositions.values():
            name = str(item.get("disposition", "—"))
            by_disposition[name] = by_disposition.get(name, 0) + 1
        if dispositions:
            counts["dispositions"] = by_disposition
            counts["open"] = sum(
                1 for item in dispositions.values() if self._is_open(item)
            )
            counts["decided"] = len(dispositions) - counts["open"]

        blocking = self._blocking()
        counts["blocking"] = sum(
            1
            for obligation in obligations
            if self._blocks_for(
                obligation,
                blocking,
                open_=self._is_open(dispositions.get(str(obligation.get("obligation_id")))),
            )["blocking"]
        )

        return {
            "run": self.path.name,
            "path": str(self.path),
            "passes": passes,
            "counts": counts,
            "unreadable": unreadable,
        }

    def pass_artifact(self, pass_id: str) -> dict[str, Any]:
        """One pass's artifact, parsed. A directory comes back as a mapping
        from item name to document — 04_packets and 08_outputs are both small
        enough that paging them would be ceremony."""
        path = self._artifact_path(pass_id)
        if not path.exists():
            raise KeyError(f"pass {pass_id} has written no {PASS_ARTIFACTS[pass_id]}")
        if path.is_dir():
            return {
                "pass": pass_id,
                "artifact": PASS_ARTIFACTS[pass_id],
                "items": {item.stem: _load(item) for item in sorted(path.glob("*.json"))},
            }
        return {
            "pass": pass_id,
            "artifact": PASS_ARTIFACTS[pass_id],
            "document": _load(path),
        }

    def docket(self, verdicts: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        """§8.1 — every obligation, ordered by what it unblocks.

        `verdicts` are handed in rather than read here. The ledger is the write
        side (`verdicts.py`), and a reader that opened it would be a reader
        that knows where writes go — the separation is the guarantee.

        Not paginated: the frontier is human-scale by construction, and a
        docket that pages is a docket someone stops reaching the bottom of.
        The front end filters; the server decides the order, because the order
        is a claim about the world and not a view preference.
        """
        obligations = self._obligations()
        dispositions = self._dispositions()
        blocking = self._blocking()
        standing = verdicts or {}

        rows: list[dict[str, Any]] = []
        for obligation in obligations:
            obligation_id = str(obligation.get("obligation_id", ""))
            judgment = dispositions.get(obligation_id)
            verdict = standing.get(obligation_id)
            packet = self._packet(obligation_id)
            disposition = str(judgment.get("disposition")) if judgment else None
            open_ = self._is_open(judgment, verdict)
            rows.append(
                {
                    "obligation_id": obligation_id,
                    "relation": obligation.get("relation"),
                    "values": obligation.get("values"),
                    "why_demanded": obligation.get("why_demanded"),
                    "required_by": obligation.get("required_by") or [],
                    "state": obligation.get("current_epistemic_state"),
                    "disposition": disposition,
                    # The machine's own reason for declining is what makes a
                    # three-second decision possible (§8.1). It is a row field,
                    # not a detail behind a click.
                    "rationale": judgment.get("rationale") if judgment else None,
                    "verification": judgment.get("verification_result") if judgment else None,
                    "observations": len((packet or {}).get("selected_observations") or []),
                    "known_missing_information": (packet or {}).get(
                        "known_missing_information"
                    ),
                    # Both, always. §15: the machine's judgment remains
                    # readable beneath a human's, because the disagreement is
                    # the record worth keeping.
                    "verdict": verdict,
                    "open": open_,
                    "blocks": self._blocks_for(obligation, blocking, open_=open_),
                }
            )

        rows.sort(key=self._docket_order)
        return {
            "obligations": rows,
            "counts": {
                "total": len(rows),
                "open": sum(1 for row in rows if row["open"]),
                "decided": sum(1 for row in rows if not row["open"]),
                "blocking": sum(1 for row in rows if row["blocks"]["blocking"]),
            },
        }

    @staticmethod
    def _docket_order(row: dict[str, Any]) -> tuple:
        """Blocking first, then still-open, then by id. Never by arrival.

        Within blocking, more purposes blocked sorts higher — an obligation two
        purposes wait on is worth deciding before one that holds up a single
        derived relation.

        The weights are read as zero for a decided obligation, which is the
        whole of why this is four lines rather than one sort. A decided
        obligation's `blocks` lists stay populated — they say what it *would*
        hold up — and left in the key they would float a settled question above
        an open one that happens to block nothing.
        """
        purposes = len(row["blocks"]["purposes"]) if row["open"] else 0
        relations = len(row["blocks"]["relations"]) if row["open"] else 0
        return (-purposes, -relations, 0 if row["open"] else 1, row["obligation_id"])

    def obligation(
        self, obligation_id: str, verdict: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """§8.2 — one obligation, opened: proposition, packet, judgment.

        Three panes and no navigation between them, so all three are one read.
        `verdict` is handed in, never found here: a human verdict is recorded
        beside the run in the ledger, and nothing on the read plane produces
        one. The field is always present — null when nobody has adjudicated —
        so the shape of an adjudicated obligation is the shape of an
        un-adjudicated one and the surface has no reason to guess.
        """
        for obligation in self._obligations():
            if str(obligation.get("obligation_id")) == obligation_id:
                break
        else:
            raise KeyError(f"no obligation {obligation_id!r} in this construction")

        judgment = self._dispositions().get(obligation_id)
        packet = self._packet(obligation_id)
        return {
            "obligation_id": obligation_id,
            "proposition": {
                "relation": obligation.get("relation"),
                "values": obligation.get("values"),
                "why_demanded": obligation.get("why_demanded"),
                "required_by": obligation.get("required_by") or [],
                "state": obligation.get("current_epistemic_state"),
            },
            # Absent rather than empty when P4 wrote no packet: no evidence
            # gathered and evidence gathered that found nothing are different
            # facts, and only one of them is the constructor's failure.
            "packet": packet,
            "judgment": judgment,
            "blocks": self._blocks_for(
                obligation, self._blocking(), open_=self._is_open(judgment, verdict)
            ),
            "verdict": verdict,
        }
