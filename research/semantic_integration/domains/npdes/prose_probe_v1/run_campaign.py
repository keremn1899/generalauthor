"""Resumable prose-probe campaign. Frozen prompts. Composer 2.5 only."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.campaign import (
    isolation_leaks_from_events,
)
from research.semantic_integration.domains.npdes.prose_probe_v1.agent import (
    load_result_json,
    parse_json_from_stdout,
    run_probe_agent,
)
from research.semantic_integration.domains.npdes.prose_probe_v1.isolation import (
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
)
from research.semantic_integration.domains.npdes.prose_probe_v1.paths import FROZEN, MODEL, REPO, RUNS
from research.semantic_integration.domains.npdes.prose_probe_v1.prompts import PROMPTS, TIMEOUTS
from research.semantic_integration.domains.npdes.prose_probe_v1.score import (
    FULL,
    MISS,
    candidate_matches_gold,
    candidate_matches_negative,
    load_frozen,
    parse_disposition,
    score_b0,
    score_b2_row,
    score_obligation_output,
)
from research.semantic_integration.domains.npdes.prose_probe_v1.workspaces import (
    seed_b1,
    seed_b2,
    seed_b3,
    seed_b4,
    seed_b4_p5,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump(path: Path, payload: dict) -> None:
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
        return json.loads((sealed / "agent.json").read_text())
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
            dump(live / "result.json", result if isinstance(result, dict) else {"payload": result})
        agent = slim_agent(raw)
        agent["isolation_preflight"] = preflight
        agent["condition"] = condition
        dump(sealed / "agent.json", agent)
        if (live / "05_dispositions.json").exists():
            shutil.copy2(live / "05_dispositions.json", sealed / "05_dispositions.json")
        if raw.get("timed_out") or result is None:
            (sealed / "transcript.stdout.txt").write_text((raw.get("stdout") or "")[-100000:], encoding="utf-8")
        if agent["isolation_leaks"]:
            dump(sealed / "LEAK.json", {"leaks": agent["isolation_leaks"]})
            raise RuntimeError(f"isolation leak: {agent['isolation_leaks']}")
        if agent.get("reported_model") and "composer" not in str(agent["reported_model"]).lower():
            dump(sealed / "MODEL_FAIL.json", {"reported_model": agent.get("reported_model")})
            raise RuntimeError(f"non-Composer model {agent['reported_model']!r}")
        return agent
    finally:
        remove_live_workspace(live)


def establishable_ids() -> list[str]:
    return [row["gold_id"] for row in load_frozen("evidence_sufficiency.json") if row["classification"].startswith("ESTABLISHABLE")]


def run_b0() -> dict:
    path = RUNS / "b0" / "score.json"
    if done(path):
        return json.loads(path.read_text())
    payload = score_b0()
    dump(path, payload)
    return payload


def run_b1(*, extra: bool = False) -> dict:
    cards = {c["gold_id"]: c for c in load_frozen("semantic_cards.json")}
    ids = establishable_ids()
    n_reps = 10 if extra else 5
    summary = {"condition": "B1", "per_seam": {}, "replicates": []}
    for gid in ids:
        grades = []
        for rep in range(1, n_reps + 1):
            sealed = RUNS / "b1" / gid / f"R{rep}"
            if extra and rep <= 5 and not (sealed / "agent.json").exists():
                continue
            if extra and rep <= 5:
                result = json.loads((sealed / "result.json").read_text()) if (sealed / "result.json").exists() else None
                grade = score_obligation_output(result, cards[gid])
                grades.append(grade)
                continue
            run_isolated_prompt("b1", lambda live, g=gid: seed_b1(live, g), sealed)
            result = json.loads((sealed / "result.json").read_text()) if (sealed / "result.json").exists() else None
            grade = score_obligation_output(result, cards[gid])
            dump(sealed / "score.json", {"gold_id": gid, "rep": rep, "grade": grade})
            grades.append(grade)
        full_n = sum(g == FULL for g in grades[:5])
        summary["per_seam"][gid] = {
            "grades": grades,
            "full_over_first5": f"{full_n}/5",
            "full_recall_first5": full_n / 5 if grades else None,
        }
    first5 = [summary["per_seam"][g]["full_recall_first5"] or 0 for g in ids]
    summary["PURPOSE_RELEVANT_OBLIGATION_RECALL"] = sum(first5) / len(first5) if first5 else None
    summary["stability"] = _stability_hist([summary["per_seam"][g]["full_over_first5"] for g in ids])
    dump(RUNS / "b1" / "summary.json", summary)
    return summary


def _stability_hist(labels: list[str]) -> dict:
    hist = {f"{i}/5": 0 for i in range(6)}
    for lab in labels:
        hist[lab] = hist.get(lab, 0) + 1
    return hist


def ambiguous(full_over_first5: str) -> bool:
    return full_over_first5 in {"2/5", "3/5"}


def maybe_extend_b1(summary: dict) -> dict:
    cards = {c["gold_id"]: c for c in load_frozen("semantic_cards.json")}
    for gid, row in summary["per_seam"].items():
        if not ambiguous(row["full_over_first5"]):
            continue
        grades = list(row["grades"])
        for rep in range(6, 11):
            sealed = RUNS / "b1" / gid / f"R{rep}"
            run_isolated_prompt("b1", lambda live, g=gid: seed_b1(live, g), sealed)
            result = json.loads((sealed / "result.json").read_text()) if (sealed / "result.json").exists() else None
            grade = score_obligation_output(result, cards[gid])
            dump(sealed / "score.json", {"gold_id": gid, "rep": rep, "grade": grade, "extension": True})
            grades.append(grade)
        row["grades"] = grades
        row["extended"] = True
        row["full_over_10"] = f"{sum(g == FULL for g in grades)}/10"
    dump(RUNS / "b1" / "summary.json", summary)
    return summary


def run_b2() -> dict:
    expected = load_frozen("expected_b2.json")
    ids = establishable_ids()
    summary = {"condition": "B2", "per_seam": {}}
    for gid in ids:
        rows = []
        for rep in range(1, 6):
            sealed = RUNS / "b2" / gid / f"R{rep}"
            run_isolated_prompt("b2", lambda live, g=gid: seed_b2(live, g), sealed)
            payload = None
            if (sealed / "05_dispositions.json").exists():
                payload = json.loads((sealed / "05_dispositions.json").read_text())
            elif (sealed / "result.json").exists():
                payload = json.loads((sealed / "result.json").read_text())
            parsed = parse_disposition(payload)
            scored = score_b2_row(gid, parsed, expected)
            scored["rep"] = rep
            dump(sealed / "score.json", scored)
            rows.append(scored)
        n_safe = sum(1 for r in rows if r["correct_or_legitimate_unresolved"])
        n_unresolved = sum(1 for r in rows if r["disposition"] == "UNRESOLVED")
        n_unsupported = sum(1 for r in rows if r["unsupported_closure"])
        summary["per_seam"][gid] = {
            "rows": rows,
            "safe_over_5": f"{n_safe}/5",
            "safe_recall": n_safe / 5,
            "unresolved_over_5": f"{n_unresolved}/5",
            "unsupported_over_5": f"{n_unsupported}/5",
        }
    ids_l = list(summary["per_seam"])
    summary["B2_correct_or_legitimate_UNRESOLVED"] = sum(summary["per_seam"][g]["safe_recall"] for g in ids_l) / len(ids_l)
    summary["unsupported_closure_rate"] = sum(
        int(summary["per_seam"][g]["unsupported_over_5"].split("/")[0]) for g in ids_l
    ) / (5 * len(ids_l))
    dump(RUNS / "b2" / "summary.json", summary)
    return summary


def maybe_extend_b2(summary: dict) -> dict:
    expected = load_frozen("expected_b2.json")
    for gid, row in summary["per_seam"].items():
        n_safe = int(row["safe_over_5"].split("/")[0])
        if n_safe not in {2, 3}:
            continue
        rows = list(row["rows"])
        for rep in range(6, 11):
            sealed = RUNS / "b2" / gid / f"R{rep}"
            run_isolated_prompt("b2", lambda live, g=gid: seed_b2(live, g), sealed)
            payload = None
            if (sealed / "05_dispositions.json").exists():
                payload = json.loads((sealed / "05_dispositions.json").read_text())
            elif (sealed / "result.json").exists():
                payload = json.loads((sealed / "result.json").read_text())
            parsed = parse_disposition(payload)
            scored = score_b2_row(gid, parsed, expected)
            scored["rep"] = rep
            scored["extension"] = True
            dump(sealed / "score.json", scored)
            rows.append(scored)
        row["rows"] = rows
        row["extended"] = True
        n_safe10 = sum(1 for r in rows if r["correct_or_legitimate_unresolved"])
        row["safe_over_10"] = f"{n_safe10}/10"
    dump(RUNS / "b2" / "summary.json", summary)
    return summary


def run_b3() -> dict:
    pages = json.loads((FROZEN / "segmentation_pages.json").read_text())
    pas = load_frozen("passages.json")
    ids = establishable_ids()
    summary = {"condition": "B3", "replicates": []}
    for rep in range(1, 6):
        nominees = []
        n_calls = 0
        n_skipped = 0
        n_new = 0
        print(f"B3 R{rep} starting {len(pages)} segments", flush=True)
        for segment in pages:
            sealed = RUNS / "b3" / f"R{rep}" / segment["segment_id"].replace("/", "__")
            if segment.get("n_chars", 0) < 80 and segment.get("section") == "blank":
                dump(sealed / "result.json", {"candidates": [], "skipped_empty": True})
                n_skipped += 1
                continue
            already = (sealed / "agent.json").exists()
            try:
                run_isolated_prompt(
                    "b3",
                    lambda live, seg=segment: seed_b3(live, seg),
                    sealed,
                )
            except Exception as exc:
                dump(sealed / "ERROR.json", {"error": repr(exc), "at": now()})
                print(f"B3 R{rep} {segment['segment_id']} ERROR {exc!r}", flush=True)
            n_calls += 1
            if not already:
                n_new += 1
                if n_new % 5 == 0:
                    print(f"B3 R{rep} new_calls={n_new} segment={segment['segment_id']}", flush=True)
            result = json.loads((sealed / "result.json").read_text()) if (sealed / "result.json").exists() else {}
            cands = result.get("candidates") if isinstance(result, dict) else None
            if not isinstance(cands, list):
                cands = []
            for cand in cands:
                cand = dict(cand)
                cand["_segment_id"] = segment["segment_id"]
                cand["_page"] = segment["page"]
                cand["_document"] = segment["document"]
                nominees.append(cand)
        # exact duplicate merge within replicate
        merged = []
        seen = set()
        for cand in nominees:
            key = (
                str(cand.get("source") or cand.get("_document")),
                str(cand.get("locator") or cand.get("_page")),
                str(cand.get("exact_span") or "").strip(),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(cand)
        gold_hits = {gid: False for gid in ids}
        neg_hits = {gid: 0 for gid in ids}
        n_neg_controls = sum(len(pas["negatives"].get(gid) or []) for gid in ids)
        for cand in merged:
            for gid in ids:
                if candidate_matches_gold(cand, gid, pas):
                    gold_hits[gid] = True
                if candidate_matches_negative(cand, gid, pas):
                    neg_hits[gid] += 1
        rec = sum(1 for gid in ids if gold_hits[gid]) / len(ids)
        n_neg_nominated = sum(1 for gid in ids if neg_hits[gid] > 0)
        rep_row = {
            "rep": rep,
            "n_segments": len(pages),
            "n_model_calls": n_calls,
            "n_skipped_empty": n_skipped,
            "n_raw_nominations": len(nominees),
            "n_merged": len(merged),
            "gold_hits": gold_hits,
            "gold_recall": rec,
            "negative_control_hits": neg_hits,
            "negative_control_nomination_rate": n_neg_nominated / n_neg_controls if n_neg_controls else None,
            "candidates_per_segment": len(merged) / len(pages) if pages else None,
        }
        dump(RUNS / "b3" / f"R{rep}" / "merged.json", {"candidates": merged, "metrics": rep_row})
        summary["replicates"].append(rep_row)
        print(
            f"B3 R{rep} done gold_recall={rec} merged={len(merged)} new_calls={n_new} skipped_empty={n_skipped}",
            flush=True,
        )
    summary["mean_gold_recall"] = sum(r["gold_recall"] for r in summary["replicates"]) / 5
    summary["mean_negative_control_rate"] = sum(r["negative_control_nomination_rate"] or 0 for r in summary["replicates"]) / 5
    summary["mean_candidate_count"] = sum(r["n_merged"] for r in summary["replicates"]) / 5
    dump(RUNS / "b3" / "summary.json", summary)
    return summary


def _b4_one(rep: int, i: int, cand: dict, pages: dict) -> None:
    sealed = RUNS / "b4" / f"R{rep}" / f"c{i:04d}"
    seg = pages.get(cand.get("_segment_id") or "")
    try:
        run_isolated_prompt("b4", lambda live, c=cand, s=seg: seed_b4(live, c, s), sealed)
    except Exception as exc:
        dump(sealed / "ERROR.json", {"error": repr(exc), "at": now()})
        print(f"B4 R{rep} c{i:04d} ERROR {exc!r}", flush=True)


def run_b4(*, workers: int = 4) -> dict:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    cards = {c["gold_id"]: c for c in load_frozen("semantic_cards.json")}
    pages = {s["segment_id"]: s for s in json.loads((FROZEN / "segmentation_pages.json").read_text())}
    ids = establishable_ids()
    expected = load_frozen("expected_b2.json")
    rank = {MISS: 0, "PARTIAL_OBLIGATION": 1, FULL: 2}
    summary = {"condition": "B4", "workers": workers, "replicates": []}
    for rep in range(1, 6):
        merged_path = RUNS / "b3" / f"R{rep}" / "merged.json"
        merged = json.loads(merged_path.read_text())["candidates"]
        pending = []
        for i, cand in enumerate(merged):
            sealed = RUNS / "b4" / f"R{rep}" / f"c{i:04d}"
            if not (sealed / "agent.json").exists():
                pending.append((i, cand))
        print(f"B4 R{rep}: {len(merged)} candidates, {len(pending)} remaining", flush=True)
        if pending:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futs = [pool.submit(_b4_one, rep, i, cand, pages) for i, cand in pending]
                done_n = 0
                for fut in as_completed(futs):
                    fut.result()
                    done_n += 1
                    if done_n % 25 == 0:
                        print(f"B4 R{rep} completed {done_n}/{len(pending)}", flush=True)
        seam_best = {gid: MISS for gid in ids}
        n_obl = 0
        n_downstream = 0
        n_unsupported = 0
        for i, cand in enumerate(merged):
            sealed = RUNS / "b4" / f"R{rep}" / f"c{i:04d}"
            result = json.loads((sealed / "result.json").read_text()) if (sealed / "result.json").exists() else None
            n_obl += 1
            matched = []
            for gid in ids:
                grade = score_obligation_output(result, cards[gid])
                if grade != MISS:
                    matched.append(gid)
                    if rank[grade] > rank[seam_best[gid]]:
                        seam_best[gid] = grade
            dump(
                sealed / "score.json",
                {
                    "candidate_index": i,
                    "matched_gold": matched,
                    "grades": {gid: score_obligation_output(result, cards[gid]) for gid in ids},
                    "result_kind": (result or {}).get("kind") if isinstance(result, dict) else None,
                },
            )
            full_hits = [gid for gid in matched if score_obligation_output(result, cards[gid]) == FULL]
            if full_hits and isinstance(result, dict) and result.get("kind") == "OBLIGATION":
                dsealed = RUNS / "b4_p5" / f"R{rep}" / f"c{i:04d}"
                run_isolated_prompt("b4_p5", lambda live, o=result, c=cand: seed_b4_p5(live, o, c), dsealed)
                payload = None
                if (dsealed / "05_dispositions.json").exists():
                    payload = json.loads((dsealed / "05_dispositions.json").read_text())
                parsed = parse_disposition(payload)
                scored = score_b2_row(full_hits[0], parsed, expected)
                dump(dsealed / "score.json", scored)
                n_downstream += 1
                if scored["unsupported_closure"]:
                    n_unsupported += 1
        full_n = sum(1 for gid in ids if seam_best[gid] == FULL)
        rec = full_n / len(ids)
        print(f"B4 R{rep} full_recall={rec} best={seam_best}", flush=True)
        summary["replicates"].append(
            {
                "rep": rep,
                "n_candidates": len(merged),
                "n_obligation_calls": n_obl,
                "per_seam_best": seam_best,
                "full_recall": rec,
                "n_downstream_p5": n_downstream,
                "n_unsupported_closure": n_unsupported,
            }
        )
    mean_b4 = sum(r["full_recall"] for r in summary["replicates"]) / 5
    summary["mean_full_recall"] = mean_b4
    dump(RUNS / "b4" / "summary.json", summary)
    return summary


def run_c_ablation(b1: dict) -> dict | None:
    """Only if B1 propositionization is unexpectedly weak or unstable."""
    recall = b1.get("PURPOSE_RELEVANT_OBLIGATION_RECALL") or 0
    unstable = any(v["full_over_first5"] in {"2/5", "3/5"} for v in b1["per_seam"].values())
    weak = recall < 0.70
    if not (weak or unstable):
        dump(RUNS / "c_ablation" / "skipped.json", {"skipped": True, "reason": "B1 not unexpectedly weak/unstable", "recall": recall})
        return None
    cards = {c["gold_id"]: c for c in load_frozen("semantic_cards.json")}
    affected = [
        gid
        for gid, row in b1["per_seam"].items()
        if (row["full_recall_first5"] or 0) < 0.85
    ]
    out = {"condition": "C1_C2", "affected": affected, "per_seam": {}}
    for gid in affected:
        c1 = []
        c2 = []
        for rep in range(1, 6):
            s1 = RUNS / "c1" / gid / f"R{rep}"
            run_isolated_prompt("c1", lambda live, g=gid: seed_b1(live, g, span_only=True), s1)
            r1 = json.loads((s1 / "result.json").read_text()) if (s1 / "result.json").exists() else None
            g1 = score_obligation_output(r1, cards[gid])
            c1.append(g1)
            s2 = RUNS / "c2" / gid / f"R{rep}"
            run_isolated_prompt("c2", lambda live, g=gid: seed_b1(live, g, span_only=False), s2)
            r2 = json.loads((s2 / "result.json").read_text()) if (s2 / "result.json").exists() else None
            g2 = score_obligation_output(r2, cards[gid])
            c2.append(g2)
        out["per_seam"][gid] = {
            "c1_full": sum(g == FULL for g in c1) / 5,
            "c2_full": sum(g == FULL for g in c2) / 5,
            "c1": c1,
            "c2": c2,
        }
    dump(RUNS / "c_ablation" / "summary.json", out)
    return out


def main() -> dict:
    RUNS.mkdir(parents=True, exist_ok=True)
    b0 = run_b0()
    print("B0 mean full recall", b0["mean_full_recall"], flush=True)
    b1 = run_b1()
    print("B1 recall", b1["PURPOSE_RELEVANT_OBLIGATION_RECALL"], flush=True)
    b1 = maybe_extend_b1(b1)
    b2 = run_b2()
    print("B2 safe", b2["B2_correct_or_legitimate_UNRESOLVED"], flush=True)
    b2 = maybe_extend_b2(b2)
    b3 = run_b3()
    print("B3 gold recall", b3["mean_gold_recall"], flush=True)
    b4 = run_b4(workers=6)
    print("B4 recall", b4["mean_full_recall"], flush=True)
    c = run_c_ablation(b1)
    from research.semantic_integration.domains.npdes.prose_probe_v1.report import main as write_reports

    write_reports()
    payload = {
        "experiment_id": "npdes-prose-probe-v1",
        "model": MODEL,
        "finished_at": now(),
        "b0": {"mean_full_recall": b0["mean_full_recall"]},
        "b1": {"PURPOSE_RELEVANT_OBLIGATION_RECALL": b1["PURPOSE_RELEVANT_OBLIGATION_RECALL"]},
        "b2": {"safe": b2["B2_correct_or_legitimate_UNRESOLVED"]},
        "b3": {"mean_gold_recall": b3["mean_gold_recall"]},
        "b4": {"mean_full_recall": b4["mean_full_recall"]},
        "c_ablation": bool(c),
    }
    dump(RUNS / "campaign.json", payload)
    return payload


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
