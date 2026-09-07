"""Resumable Probe v1.1 campaign: B4-lite on GOLD+NEGATIVE B3 candidates, selective P5, C1."""

from __future__ import annotations

import json
import shutil
import sys
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.campaign import (
    isolation_leaks_from_events,
)
from research.semantic_integration.domains.npdes.prose_probe_v1.score import (
    FULL,
    MISS,
    PARTIAL,
    load_frozen,
    parse_disposition,
    score_b2_row,
)
from research.semantic_integration.domains.npdes.prose_probe_v1.workspaces import seed_b1
from research.semantic_integration.domains.npdes.prose_probe_v1_1.agent import (
    load_result_json,
    parse_json_from_stdout,
    run_probe_agent,
)
from research.semantic_integration.domains.npdes.prose_probe_v1_1.classify import (
    GOLD,
    NEGATIVE,
    dump_selected,
    load_selected,
)
from research.semantic_integration.domains.npdes.prose_probe_v1_1.isolation import (
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.npdes.prose_probe_v1_1.paths import (
    MODEL,
    RUNS,
    SEALED_V1_B0_FULL,
    SEALED_V1_B1_FULL,
    V1,
)
from research.semantic_integration.domains.npdes.prose_probe_v1_1.prompts import TIMEOUTS
from research.semantic_integration.domains.npdes.prose_probe_v1_1.score import (
    FULL_SPURIOUS,
    NO_RELEVANT,
    PARSE_FAIL,
    WEAK_SPURIOUS,
    best_grade,
    is_obligation,
    p5_negative_row,
    score_gold_payload,
    score_negative_payload,
)
from research.semantic_integration.domains.npdes.prose_probe_v1_1.workspaces import (
    seed_b4_lite,
    seed_p5,
)

UNSTABLE_SEAMS = ["S-FARM-REPORT-ONLY", "S-SOURCE-AUTHORITY"]
WORKERS = 6


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def done(path: Path) -> bool:
    return path.exists()


def slim_agent(record: dict) -> dict:
    stdout = record.get("stdout") or ""
    return {
        "adapter": record.get("adapter"),
        "model": record.get("model"),
        "reported_model": record.get("reported_model"),
        "returncode": record.get("returncode"),
        "timed_out": record.get("timed_out"),
        "usage": record.get("usage"),
        "tools": record.get("tools"),
        "timeout_seconds": record.get("timeout_seconds"),
        "stdout_tail": stdout[-20000:],
        "stderr_tail": (record.get("stderr") or "")[-4000:],
        "isolation_leaks": isolation_leaks_from_events(record.get("events") or []),
        "finished_at": now(),
    }


def run_isolated_prompt(condition: str, seed_fn, sealed: Path) -> dict:
    if done(sealed / "agent.json"):
        return json.loads((sealed / "agent.json").read_text(encoding="utf-8"))
    live = new_live_workspace()
    try:
        seed_fn(live)
        preflight = preflight_isolation(live)
        prompt = (
            "Read PASS_TASK.md and follow it exactly. "
            "Write the required JSON output file. Do not read files outside this workspace."
        )
        raw = run_probe_agent(workspace=live, prompt=prompt, timeout_seconds=TIMEOUTS[condition])
        result = load_result_json(live) or parse_json_from_stdout(raw.get("stdout") or "")
        if result is not None:
            dump(sealed / "result.json", result if isinstance(result, dict) else {"payload": result})
        agent = slim_agent(raw)
        agent["isolation_preflight"] = preflight
        agent["condition"] = condition
        dump(sealed / "agent.json", agent)
        if (live / "05_dispositions.json").exists():
            shutil.copy2(live / "05_dispositions.json", sealed / "05_dispositions.json")
        if raw.get("timed_out") or result is None:
            (sealed / "transcript.stdout.txt").write_text(
                (raw.get("stdout") or "")[-100000:], encoding="utf-8"
            )
        if agent["isolation_leaks"]:
            dump(sealed / "LEAK.json", {"leaks": agent["isolation_leaks"]})
            raise RuntimeError(f"isolation leak: {agent['isolation_leaks']}")
        if agent.get("reported_model") and "composer" not in str(agent["reported_model"]).lower():
            dump(sealed / "MODEL_FAIL.json", {"reported_model": agent.get("reported_model")})
            raise RuntimeError(f"non-Composer model {agent['reported_model']!r}")
        return agent
    finally:
        remove_live_workspace(live)


def public_candidate(row: dict) -> dict:
    """Strip evaluator labels before seeding a workspace."""
    return {
        "candidate_id": row["candidate_id"],
        "source": row.get("source"),
        "locator": row.get("locator"),
        "exact_span": row.get("exact_span"),
        "affected_purpose": row.get("affected_purpose"),
        "_segment_id": row.get("_segment_id"),
        "_page": row.get("_page"),
        "_document": row.get("_document"),
    }


def sealed_dir(row: dict) -> Path:
    return RUNS / "b4_lite" / f"R{row['rep']}" / f"c{row['merged_index']:04d}"


def p5_dir(row: dict) -> Path:
    return RUNS / "p5" / f"R{row['rep']}" / f"c{row['merged_index']:04d}"


def _b4_one(row: dict) -> None:
    sealed = sealed_dir(row)
    cand = public_candidate(row)
    print(f"B4-lite start {row['candidate_id']}", flush=True)
    try:
        run_isolated_prompt("b4_lite", lambda live, c=cand: seed_b4_lite(live, c), sealed)
        print(f"B4-lite done {row['candidate_id']}", flush=True)
    except Exception as exc:
        dump(sealed / "ERROR.json", {"error": repr(exc), "at": now()})
        print(f"B4-lite {row['candidate_id']} ERROR {exc!r}", flush=True)


def run_b4_lite(*, workers: int = WORKERS) -> dict:
    selected = load_selected()
    rows = selected["candidates"]
    pending = [row for row in rows if not (sealed_dir(row) / "agent.json").exists()]
    print(f"B4-lite: {len(rows)} selected, {len(pending)} remaining, workers={workers}", flush=True)
    print(f"B4-lite start {now()}", flush=True)
    if pending:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = [pool.submit(_b4_one, row) for row in pending]
            done_n = 0
            for fut in as_completed(futs):
                fut.result()
                done_n += 1
                if done_n % 10 == 0 or done_n == len(pending):
                    print(f"B4-lite completed {done_n}/{len(pending)}", flush=True)
    summary = score_b4_lite()
    return summary


def load_result(sealed: Path) -> Any:
    path = sealed / "result.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def score_b4_lite() -> dict:
    cards = {c["gold_id"]: c for c in load_frozen("semantic_cards.json")}
    gold_ids = list(cards)
    selected = load_selected()
    per_rep: dict[int, dict] = {}
    gold_rows = []
    neg_rows = []
    n_processed = 0
    n_obligations = 0
    n_no_relevant = 0
    n_full_gold_obligations = 0
    n_spurious_neg = 0
    for row in selected["candidates"]:
        sealed = sealed_dir(row)
        result = load_result(sealed)
        n_processed += 1
        obl = is_obligation(result)
        no_rel = (not obl) and (result is not None) and score_negative_payload(result) == NO_RELEVANT
        if obl:
            n_obligations += 1
        if no_rel:
            n_no_relevant += 1
        rep = row["rep"]
        per_rep.setdefault(
            rep,
            {
                "rep": rep,
                "seam_best": {gid: MISS for gid in gold_ids},
                "n_gold": 0,
                "n_neg": 0,
                "n_obl": 0,
                "n_no_relevant": 0,
            },
        )
        bucket = per_rep[rep]
        if row["label"] == GOLD:
            bucket["n_gold"] += 1
            grades = {}
            for gid in row["gold_ids"]:
                grade = score_gold_payload(result, cards[gid])
                grades[gid] = grade
                bucket["seam_best"][gid] = best_grade([bucket["seam_best"][gid], grade])
                if grade == FULL:
                    n_full_gold_obligations += 1
            scored = {
                "candidate_id": row["candidate_id"],
                "label": GOLD,
                "gold_ids": row["gold_ids"],
                "grades": grades,
                "kind": (result or {}).get("kind") if isinstance(result, dict) else None,
                "is_obligation": obl,
                "no_relevant": no_rel,
            }
            dump(sealed / "score.json", scored)
            gold_rows.append(scored)
        else:
            bucket["n_neg"] += 1
            neg_grade = score_negative_payload(result)
            if neg_grade in {FULL_SPURIOUS, WEAK_SPURIOUS}:
                n_spurious_neg += 1
            scored = {
                "candidate_id": row["candidate_id"],
                "label": NEGATIVE,
                "negative_ids": row["negative_ids"],
                "negative_grade": neg_grade,
                "kind": (result or {}).get("kind") if isinstance(result, dict) else None,
                "is_obligation": obl,
            }
            dump(sealed / "score.json", scored)
            neg_rows.append(scored)
        if obl:
            bucket["n_obl"] += 1
        if no_rel:
            bucket["n_no_relevant"] += 1

    replicate_metrics = []
    for rep in (1, 2, 3):
        bucket = per_rep[rep]
        full_n = sum(1 for gid in gold_ids if bucket["seam_best"][gid] == FULL)
        part_n = sum(1 for gid in gold_ids if bucket["seam_best"][gid] in {FULL, PARTIAL})
        loc_recall = next(
            r["locator_gold_nomination_recall"]
            for r in selected["replicate_metrics"]
            if r["rep"] == rep
        )
        replicate_metrics.append(
            {
                "rep": rep,
                "gold_passage_nomination_recall": loc_recall,
                "gold_obligation_full_recall": full_n / len(gold_ids),
                "gold_obligation_full_or_partial_recall": part_n / len(gold_ids),
                "per_seam_best": bucket["seam_best"],
                "n_gold_match": bucket["n_gold"],
                "n_negative_match": bucket["n_neg"],
                "n_generated_obligations": bucket["n_obl"],
                "n_no_relevant": bucket["n_no_relevant"],
            }
        )
    per_seam = {}
    for gid in gold_ids:
        grades = [r["per_seam_best"][gid] for r in replicate_metrics]
        per_seam[gid] = {
            "grades": grades,
            "full_over_3": f"{sum(g == FULL for g in grades)}/3",
            "full_recall": sum(g == FULL for g in grades) / 3,
            "full_or_partial_recall": sum(g != MISS for g in grades) / 3,
        }
    n_neg = len(neg_rows)
    n_neg_reject = sum(1 for r in neg_rows if r["negative_grade"] == NO_RELEVANT)
    mean_full = sum(r["gold_obligation_full_recall"] for r in replicate_metrics) / 3
    summary = {
        "condition": "B4-lite",
        "n_processed": n_processed,
        "n_generated_obligations": n_obligations,
        "n_no_relevant": n_no_relevant,
        "n_full_gold_obligations": n_full_gold_obligations,
        "n_spurious_negative_obligations": n_spurious_neg,
        "semantic_compression_ratio": n_obligations / n_processed if n_processed else None,
        "useful_obligation_yield": n_full_gold_obligations / n_obligations if n_obligations else None,
        "NEGATIVE_REJECTION_RATE": n_neg_reject / n_neg if n_neg else None,
        "spurious_obligation_rate": n_spurious_neg / n_neg if n_neg else None,
        "mean_full_recall": mean_full,
        "mean_full_or_partial_recall": sum(r["gold_obligation_full_or_partial_recall"] for r in replicate_metrics) / 3,
        "gain_over_b0": mean_full - SEALED_V1_B0_FULL,
        "b0_sealed": SEALED_V1_B0_FULL,
        "b1_sealed": SEALED_V1_B1_FULL,
        "replicates": replicate_metrics,
        "per_seam": per_seam,
        "negative_grade_counts": {
            NO_RELEVANT: sum(1 for r in neg_rows if r["negative_grade"] == NO_RELEVANT),
            WEAK_SPURIOUS: sum(1 for r in neg_rows if r["negative_grade"] == WEAK_SPURIOUS),
            FULL_SPURIOUS: sum(1 for r in neg_rows if r["negative_grade"] == FULL_SPURIOUS),
            PARSE_FAIL: sum(1 for r in neg_rows if r["negative_grade"] == PARSE_FAIL),
        },
    }
    dump(RUNS / "b4_lite" / "summary.json", summary)
    return summary


def _p5_needed(row: dict, result: Any, cards: dict) -> bool:
    if row["label"] == NEGATIVE:
        return is_obligation(result)
    if row["label"] != GOLD:
        return False
    if not is_obligation(result):
        return False
    for gid in row["gold_ids"]:
        if score_gold_payload(result, cards[gid]) in {FULL, PARTIAL}:
            return True
    return False


def _p5_one(row: dict, result: dict) -> None:
    sealed = p5_dir(row)
    cand = public_candidate(row)
    try:
        run_isolated_prompt("p5", lambda live, o=result, c=cand: seed_p5(live, o, c), sealed)
    except Exception as exc:
        dump(sealed / "ERROR.json", {"error": repr(exc), "at": now()})
        print(f"P5 {row['candidate_id']} ERROR {exc!r}", flush=True)


def run_p5(*, workers: int = WORKERS) -> dict:
    cards = {c["gold_id"]: c for c in load_frozen("semantic_cards.json")}
    expected = load_frozen("expected_b2.json")
    selected = load_selected()
    jobs = []
    for row in selected["candidates"]:
        result = load_result(sealed_dir(row))
        if _p5_needed(row, result, cards):
            jobs.append((row, result if isinstance(result, dict) else {"payload": result}))
    pending = [(row, result) for row, result in jobs if not (p5_dir(row) / "agent.json").exists()]
    print(f"P5: {len(jobs)} obligations, {len(pending)} remaining", flush=True)
    if pending:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = [pool.submit(_p5_one, row, result) for row, result in pending]
            done_n = 0
            for fut in as_completed(futs):
                fut.result()
                done_n += 1
                if done_n % 10 == 0 or done_n == len(pending):
                    print(f"P5 completed {done_n}/{len(pending)}", flush=True)
    gold_rows = []
    neg_rows = []
    n_unsupported = 0
    n_neg_propagated = 0
    n_gold_unsupported = 0
    for row, result in jobs:
        sealed = p5_dir(row)
        payload = None
        if (sealed / "05_dispositions.json").exists():
            payload = json.loads((sealed / "05_dispositions.json").read_text(encoding="utf-8"))
        elif (sealed / "result.json").exists():
            payload = json.loads((sealed / "result.json").read_text(encoding="utf-8"))
        parsed = parse_disposition(payload)
        if row["label"] == GOLD:
            gid = row["gold_ids"][0]
            scored = score_b2_row(gid, parsed, expected)
            scored["candidate_id"] = row["candidate_id"]
            scored["gold_ids"] = row["gold_ids"]
            dump(sealed / "score.json", scored)
            gold_rows.append(scored)
            if scored.get("unsupported_closure"):
                n_unsupported += 1
                n_gold_unsupported += 1
        else:
            scored = p5_negative_row(parsed)
            scored["candidate_id"] = row["candidate_id"]
            scored["negative_ids"] = row["negative_ids"]
            dump(sealed / "score.json", scored)
            neg_rows.append(scored)
            if scored.get("unsupported_closure"):
                n_unsupported += 1
            if scored.get("negative_propagated_closure"):
                n_neg_propagated += 1
    summary = {
        "condition": "P5-selective",
        "n_gold_obligations_judged": len(gold_rows),
        "n_negative_obligations_judged": len(neg_rows),
        "gold_dispositions": _count_disp(gold_rows),
        "negative_dispositions": _count_disp(neg_rows),
        "n_unsupported_closure": n_unsupported,
        "n_gold_unsupported_closure": n_gold_unsupported,
        "n_negative_unsupported_closure": sum(1 for r in neg_rows if r.get("unsupported_closure")),
        "n_negative_propagated_closure": n_neg_propagated,
        "unsupported_closure_rate": n_unsupported / len(jobs) if jobs else 0.0,
        "gold_safe_rate": (
            sum(1 for r in gold_rows if r.get("correct_or_legitimate_unresolved")) / len(gold_rows)
            if gold_rows
            else None
        ),
    }
    dump(RUNS / "p5" / "summary.json", summary)
    return summary


def _count_disp(rows: list[dict]) -> dict:
    out = {"ACCEPT": 0, "REJECT": 0, "UNRESOLVED": 0, "NONE": 0}
    for row in rows:
        d = row.get("disposition") or "NONE"
        out[d] = out.get(d, 0) + 1
    return out


def run_c1() -> dict:
    cards = {c["gold_id"]: c for c in load_frozen("semantic_cards.json")}
    out = {"condition": "C1", "per_seam": {}}
    for gid in UNSTABLE_SEAMS:
        grades = []
        for rep in range(1, 6):
            sealed = RUNS / "c1" / gid / f"R{rep}"
            try:
                run_isolated_prompt(
                    "c1",
                    lambda live, g=gid: seed_b1(live, g, span_only=True),
                    sealed,
                )
            except Exception as exc:
                dump(sealed / "ERROR.json", {"error": repr(exc), "at": now()})
            result = load_result(sealed)
            grade = score_gold_payload(result, cards[gid])
            dump(sealed / "score.json", {"gold_id": gid, "rep": rep, "grade": grade})
            grades.append(grade)
        out["per_seam"][gid] = {
            "c1": grades,
            "c1_full": sum(g == FULL for g in grades) / 5,
        }
    dump(RUNS / "c1" / "summary.json", out)
    return out


def reuse_c2() -> dict:
    """Reuse sealed v1 B1 first-5 (full local context) as C2. Do not duplicate."""
    b1 = json.loads((V1 / "runs" / "b1" / "summary.json").read_text(encoding="utf-8"))
    out = {"condition": "C2_reused_from_v1_B1", "per_seam": {}}
    for gid in UNSTABLE_SEAMS:
        row = b1["per_seam"][gid]
        grades = row["grades"][:5]
        out["per_seam"][gid] = {
            "c2": grades,
            "c2_full": sum(g == FULL for g in grades) / 5,
            "source": "v1 B1 R1–R5 full structural context",
            "extended_full_over_10": row.get("full_over_10"),
        }
    dump(RUNS / "c2" / "summary.json", out)
    return out


def main() -> dict:
    RUNS.mkdir(parents=True, exist_ok=True)
    selected = dump_selected()
    print(
        "classified",
        selected["n_selected"],
        "locator recalls",
        [r["locator_gold_nomination_recall"] for r in selected["replicate_metrics"]],
        flush=True,
    )
    c2 = reuse_c2()
    b4 = run_b4_lite(workers=WORKERS)
    print("B4-lite FULL", b4["mean_full_recall"], "neg reject", b4["NEGATIVE_REJECTION_RATE"], flush=True)
    p5 = run_p5(workers=WORKERS)
    print("P5 unsupported", p5["n_unsupported_closure"], "neg propagated", p5["n_negative_propagated_closure"], flush=True)
    c1 = run_c1()
    from research.semantic_integration.domains.npdes.prose_probe_v1_1.report import (
        interpret,
        main as write_reports,
    )

    write_reports()
    label = interpret(b4, p5)
    payload = {
        "experiment_id": "npdes-prose-probe-v1-1",
        "model": MODEL,
        "finished_at": now(),
        "n_selected": selected["n_selected"],
        "b4_lite_full_recall": b4["mean_full_recall"],
        "gain_over_b0": b4["gain_over_b0"],
        "negative_rejection_rate": b4["NEGATIVE_REJECTION_RATE"],
        "unsupported_closure": p5["n_unsupported_closure"],
        "label": label,
        "c1": {gid: c1["per_seam"][gid]["c1_full"] for gid in UNSTABLE_SEAMS},
        "c2": {gid: c2["per_seam"][gid]["c2_full"] for gid in UNSTABLE_SEAMS},
    }
    dump(RUNS / "campaign.json", payload)
    return payload


if __name__ == "__main__":
    try:
        print(json.dumps(main(), indent=2), flush=True)
    except Exception:
        import traceback

        traceback.print_exc()
        raise
