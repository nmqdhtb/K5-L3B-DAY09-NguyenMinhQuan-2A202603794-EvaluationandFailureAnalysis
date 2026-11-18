"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item
from lab9.graders import GRADERS


def _ratchet(spec: dict, base_spec: dict) -> list[str]:
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return []
    problems = []
    for section, key in (("metrics", lambda m: m["id"]),
                         ("slices", lambda s: (s["name"], s["metric"]))):
        current = {key(entry): entry for entry in spec.get(section, [])}
        for previous in base_spec.get(section, []):
            name = key(previous)
            entry = current.get(name)
            if entry is None:
                problems.append(f"ratchet: removed {section} entry {name}")
                continue
            if previous.get("blocking") and not entry.get("blocking"):
                problems.append(f"ratchet: disabled blocking for {name}")
            old = previous.get("threshold", {}) if section == "metrics" else previous
            new = entry.get("threshold", {}) if section == "metrics" else entry
            for bound in ("min", "max", "max_increase"):
                if bound not in old:
                    continue
                value = new.get(bound)
                if value is None or (value < old[bound] if bound == "min" else value > old[bound]):
                    problems.append(f"ratchet: loosened {bound} for {name}")
            if old.get("no_significant_drop") and not new.get("no_significant_drop"):
                problems.append(f"ratchet: removed no_significant_drop for {name}")
    return problems


def _report_keys(report: dict, name: str, graded: set[str], problems: list[str]) -> dict:
    manifest = report["manifest"]
    seeds = set(manifest["seeds"])
    rows = report["rows"]
    if report.get("evaluator_failures"):
        problems.append(f"{name}: evaluator failures")
    if len(rows) != manifest["items"] * len(manifest["seeds"]):
        problems.append(f"{name}: row count differs from manifest")
    for metric, value in report["metrics"].items():
        if isinstance(value, float) and not math.isfinite(value):
            problems.append(f"{name}: {metric} is not finite")

    keys, item_seeds, missing = {}, {}, set()
    for row in rows:
        item, seed = row["item_id"], row["seed"]
        pair = (item, seed)
        keys[pair] = frozenset(row.get("slices") or [])
        item_seeds.setdefault(item, set()).add(seed)
        for metric in graded:
            if type(row.get(metric)) is not bool:
                missing.add(metric)
    if len(keys) != len(rows):
        problems.append(f"{name}: duplicate (item_id, seed) rows")
    if len(seeds) != len(manifest["seeds"]) or len(item_seeds) != manifest["items"] or any(
        actual != seeds for actual in item_seeds.values()
    ):
        problems.append(f"{name}: rows do not cover the manifest item × seed grid")
    if missing:
        problems.append(f"{name}: missing or invalid grader scores: {', '.join(sorted(missing))}")
    return keys


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []
    graded = {metric["id"] for metric in spec["metrics"] if metric["id"] in GRADERS}
    pr_keys = _report_keys(pr, "PR", graded, problems)
    # A baseline can predate a newly added grader, so validate its row scores
    # against the spec that generated it when available.
    baseline_metrics = base_spec["metrics"] if base_spec is not None else spec["metrics"]
    base_graded = {metric["id"] for metric in baseline_metrics if metric["id"] in GRADERS
                   and (base_spec is not None or metric["id"] in base["metrics"])}
    base_keys = _report_keys(base, "baseline", base_graded, problems)
    if pr_keys.keys() != base_keys.keys():
        problems.append("PR and baseline have different (item_id, seed) sets")
    elif pr_keys != base_keys:
        problems.append("PR and baseline have different slice tags")
    if base_spec is not None:
        problems.extend(_ratchet(spec, base_spec))
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bootstrap = spec.get("bootstrap", {})
    for section in spec.get("slices", []):
        name, metric = section["name"], section["metric"]
        slice_id = f"slice:{name}/{metric}"
        scores = per_item(pr, metric, slice_name=name)
        value = mean(scores.values()) if scores else None
        note = ""
        if value is None or not math.isfinite(value):
            failed, note = True, "missing or non-finite slice scores"
        else:
            floor = section.get("min")
            failed = floor is not None and value < floor
            if failed:
                note = f"below floor {floor:.3f}"
            if section.get("no_significant_drop"):
                reference = per_item(base, metric, slice_name=name)
                if scores.keys() != reference.keys() or not all(map(math.isfinite, reference.values())):
                    failed = True
                    note = "slice items or scores do not match a valid baseline"
                else:
                    keys = sorted(scores)
                    delta, lo, hi = stats.paired_bootstrap(
                        [scores[key] for key in keys], [reference[key] for key in keys],
                        n_resamples=bootstrap.get("n_resamples", 1000),
                        rng=bootstrap.get("rng", 2027),
                        confidence=bootstrap.get("confidence", 0.95),
                    )
                    interval = f"Δ {delta:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                    note = f"{note} · {interval}" if note else interval
                    failed = failed or hi < 0
        verdict = "ok"
        if failed:
            verdict = "BLOCK" if section.get("blocking") else "warn"
            if section.get("blocking"):
                blocked.append(slice_id)
        display_value = f"{value:.4f}" if value is not None else "missing"
        lines.append(f"  {slice_id} {display_value} {note} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                                               confidence=bs.get("confidence", 0.95))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
