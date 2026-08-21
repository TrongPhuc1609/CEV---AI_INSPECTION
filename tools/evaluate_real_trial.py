"""Evaluate labelled real-image predictions and emit JSON + HTML evidence.

Usage:
  python tools/evaluate_real_trial.py \
    data/physical_trial/manifest.jsonl \
    --predictions data/physical_trial/results/predictions.jsonl

The runtime's normalized Status enum uses FAIL; the trial report presents that
as NG because NG is the product-level inspection terminology.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

VALID_PREDICTIONS = {"PASS", "FAIL", "NG", "UNCERTAIN"}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"JSON line {line_no} must contain an object")
        rows.append(row)
    return rows


def normalize_prediction(value: str) -> str:
    if value not in VALID_PREDICTIONS:
        raise ValueError(f"Invalid prediction: {value}")
    return "NG" if value == "FAIL" else value


def _metric_counts(rows: list[dict]) -> dict:
    counts = {"GOOD": {"PASS": 0, "NG": 0, "UNCERTAIN": 0}, "NG": {"PASS": 0, "NG": 0, "UNCERTAIN": 0}}
    for row in rows:
        counts[row["ground_truth"]][row["prediction"]] += 1
    total = len(rows)
    good = sum(counts["GOOD"].values())
    ng = sum(counts["NG"].values())
    correct = counts["GOOD"]["PASS"] + counts["NG"]["NG"]
    false_accepts = counts["NG"]["PASS"]
    false_rejects = counts["GOOD"]["NG"]
    uncertain = counts["GOOD"]["UNCERTAIN"] + counts["NG"]["UNCERTAIN"]
    return {
        "total": total,
        "good_samples": good,
        "ng_samples": ng,
        "accuracy_excluding_uncertain": (correct / (total - uncertain)) if total != uncertain else None,
        "false_accept_rate": (false_accepts / ng) if ng else None,
        "false_reject_rate": (false_rejects / good) if good else None,
        "uncertain_rate": uncertain / total if total else None,
        "coverage_rate": (total - uncertain) / total if total else None,
        "false_accepts": false_accepts,
        "false_rejects": false_rejects,
        "uncertain": uncertain,
        "counts": counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a labelled real-image trial")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data/physical_trial/results"))
    args = parser.parse_args()

    manifest_rows = load_jsonl(args.manifest)
    manifest: dict[str, dict] = {}
    for row in manifest_rows:
        sample_id = row.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id.strip():
            raise ValueError("Manifest contains an invalid sample_id")
        if sample_id in manifest:
            raise ValueError(f"Duplicate sample_id in manifest: {sample_id}")
        if row.get("ground_truth") not in {"GOOD", "NG"}:
            raise ValueError(f"Invalid ground_truth for sample_id: {sample_id}")
        manifest[sample_id] = row

    predictions = load_jsonl(args.predictions)
    if not predictions:
        raise ValueError("No predictions supplied")

    seen_predictions: set[str] = set()
    details: list[dict] = []
    for row in predictions:
        sample_id = row.get("sample_id")
        if sample_id in seen_predictions:
            raise ValueError(f"Duplicate prediction sample_id: {sample_id}")
        if sample_id not in manifest:
            raise ValueError(f"Prediction has unknown sample_id: {sample_id}")
        seen_predictions.add(sample_id)
        gt = manifest[sample_id]["ground_truth"]
        pred = normalize_prediction(row.get("prediction"))
        details.append({
            "sample_id": sample_id,
            "ground_truth": gt,
            "prediction": pred,
            "defect_type": manifest[sample_id].get("defect_type", "") or "UNSPECIFIED",
            "image": manifest[sample_id]["image"],
        })

    missing = sorted(set(manifest) - seen_predictions)
    if missing:
        preview = ", ".join(missing[:10])
        suffix = "..." if len(missing) > 10 else ""
        raise ValueError(
            f"Predictions do not cover the complete manifest: missing {len(missing)} sample(s): {preview}{suffix}"
        )

    metrics = _metric_counts(details)
    by_defect: dict[str, dict] = {}
    for defect_type in sorted({row["defect_type"] for row in details}):
        by_defect[defect_type] = _metric_counts([row for row in details if row["defect_type"] == defect_type])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"metrics": metrics, "by_defect_type": by_defect, "samples": details}
    (args.output_dir / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    def pct(value: float | None) -> str:
        return "N/A" if value is None else f"{value * 100:.2f}%"

    rows_html = "".join(
        f"<tr><td>{html.escape(d['sample_id'])}</td><td>{d['ground_truth']}</td><td>{d['prediction']}</td><td>{html.escape(d['defect_type'])}</td><td>{html.escape(d['image'])}</td></tr>"
        for d in details
    )
    defect_rows_html = "".join(
        f"<tr><td>{html.escape(defect)}</td><td>{m['total']}</td><td>{pct(m['false_accept_rate'])}</td><td>{pct(m['false_reject_rate'])}</td><td>{pct(m['uncertain_rate'])}</td><td>{pct(m['coverage_rate'])}</td></tr>"
        for defect, m in by_defect.items()
    )
    report_html = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Real Trial Evaluation</title>
<style>body{{font-family:Arial,sans-serif;margin:2rem}}table{{border-collapse:collapse;width:100%;margin-bottom:1.5rem}}th,td{{border:1px solid #ccc;padding:.4rem;text-align:left}}th{{background:#eee}}.metric{{margin:.3rem 0}}</style>
</head><body><h1>Real-World Trial Evaluation</h1>
<div class='metric'>Samples: <b>{metrics['total']}</b></div>
<div class='metric'>Accuracy excluding UNCERTAIN: <b>{pct(metrics['accuracy_excluding_uncertain'])}</b></div>
<div class='metric'>False-accept rate (NG → PASS): <b>{pct(metrics['false_accept_rate'])}</b></div>
<div class='metric'>False-reject rate (GOOD → NG): <b>{pct(metrics['false_reject_rate'])}</b></div>
<div class='metric'>UNCERTAIN rate: <b>{pct(metrics['uncertain_rate'])}</b></div>
<div class='metric'>Coverage rate: <b>{pct(metrics['coverage_rate'])}</b></div>
<h2>Confusion matrix</h2><table><tr><th>Ground truth</th><th>PASS</th><th>NG</th><th>UNCERTAIN</th></tr>
<tr><td>GOOD</td><td>{metrics['counts']['GOOD']['PASS']}</td><td>{metrics['counts']['GOOD']['NG']}</td><td>{metrics['counts']['GOOD']['UNCERTAIN']}</td></tr>
<tr><td>NG</td><td>{metrics['counts']['NG']['PASS']}</td><td>{metrics['counts']['NG']['NG']}</td><td>{metrics['counts']['NG']['UNCERTAIN']}</td></tr></table>
<h2>Performance by defect type</h2><table><tr><th>Defect type</th><th>Samples</th><th>False accept</th><th>False reject</th><th>UNCERTAIN</th><th>Coverage</th></tr>{defect_rows_html}</table>
<h2>Samples</h2><table><tr><th>Sample</th><th>Ground truth</th><th>Prediction</th><th>Defect</th><th>Image</th></tr>{rows_html}</table>
</body></html>"""
    (args.output_dir / "evaluation.html").write_text(report_html, encoding="utf-8")
    print(json.dumps({"metrics": metrics, "by_defect_type": by_defect}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
