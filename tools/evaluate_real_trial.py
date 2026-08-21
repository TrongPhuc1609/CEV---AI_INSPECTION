"""Evaluate labelled real-image predictions and emit JSON + HTML evidence.

Usage:
  python tools/evaluate_real_trial.py \
    data/physical_trial/manifest.jsonl \
    --predictions data/physical_trial/results/predictions.jsonl
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

VALID_PREDICTIONS = {"PASS", "NG", "UNCERTAIN"}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a labelled real-image trial")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data/physical_trial/results"))
    args = parser.parse_args()

    manifest = {row["sample_id"]: row for row in load_jsonl(args.manifest)}
    predictions = load_jsonl(args.predictions)
    if not predictions:
        raise ValueError("No predictions supplied")

    counts = {"GOOD": {"PASS": 0, "NG": 0, "UNCERTAIN": 0}, "NG": {"PASS": 0, "NG": 0, "UNCERTAIN": 0}}
    details: list[dict] = []
    for row in predictions:
        sample_id = row.get("sample_id")
        if sample_id not in manifest:
            raise ValueError(f"Prediction has unknown sample_id: {sample_id}")
        gt = manifest[sample_id]["ground_truth"]
        pred = row.get("prediction")
        if pred not in VALID_PREDICTIONS:
            raise ValueError(f"Invalid prediction for {sample_id}: {pred}")
        counts[gt][pred] += 1
        details.append({
            "sample_id": sample_id,
            "ground_truth": gt,
            "prediction": pred,
            "defect_type": manifest[sample_id].get("defect_type", ""),
            "image": manifest[sample_id]["image"],
        })

    total = len(details)
    good = sum(counts["GOOD"].values())
    ng = sum(counts["NG"].values())
    correct = counts["GOOD"]["PASS"] + counts["NG"]["NG"]
    false_accepts = counts["NG"]["PASS"]
    false_rejects = counts["GOOD"]["NG"]
    uncertain = counts["GOOD"]["UNCERTAIN"] + counts["NG"]["UNCERTAIN"]
    metrics = {
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

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"metrics": metrics, "samples": details}
    (args.output_dir / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    def pct(value: float | None) -> str:
        return "N/A" if value is None else f"{value * 100:.2f}%"

    rows_html = "".join(
        f"<tr><td>{html.escape(d['sample_id'])}</td><td>{d['ground_truth']}</td><td>{d['prediction']}</td><td>{html.escape(d['defect_type'])}</td><td>{html.escape(d['image'])}</td></tr>"
        for d in details
    )
    report_html = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Real Trial Evaluation</title>
<style>body{{font-family:Arial,sans-serif;margin:2rem}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:.4rem;text-align:left}}th{{background:#eee}}.metric{{margin:.3rem 0}}</style>
</head><body><h1>Real-World Trial Evaluation</h1>
<div class='metric'>Samples: <b>{total}</b></div>
<div class='metric'>Accuracy excluding UNCERTAIN: <b>{pct(metrics['accuracy_excluding_uncertain'])}</b></div>
<div class='metric'>False-accept rate (NG → PASS): <b>{pct(metrics['false_accept_rate'])}</b></div>
<div class='metric'>False-reject rate (GOOD → NG): <b>{pct(metrics['false_reject_rate'])}</b></div>
<div class='metric'>UNCERTAIN rate: <b>{pct(metrics['uncertain_rate'])}</b></div>
<div class='metric'>Coverage rate: <b>{pct(metrics['coverage_rate'])}</b></div>
<h2>Confusion matrix</h2><table><tr><th>Ground truth</th><th>PASS</th><th>NG</th><th>UNCERTAIN</th></tr>
<tr><td>GOOD</td><td>{counts['GOOD']['PASS']}</td><td>{counts['GOOD']['NG']}</td><td>{counts['GOOD']['UNCERTAIN']}</td></tr>
<tr><td>NG</td><td>{counts['NG']['PASS']}</td><td>{counts['NG']['NG']}</td><td>{counts['NG']['UNCERTAIN']}</td></tr></table>
<h2>Samples</h2><table><tr><th>Sample</th><th>Ground truth</th><th>Prediction</th><th>Defect</th><th>Image</th></tr>{rows_html}</table>
</body></html>"""
    (args.output_dir / "evaluation.html").write_text(report_html, encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
