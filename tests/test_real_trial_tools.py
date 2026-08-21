import json
from pathlib import Path

import pytest

from tools.evaluate_real_trial import main as evaluate_main
from tools.evaluate_real_trial import normalize_prediction
from tools.run_real_trial_batch import load_manifest


def test_load_manifest_accepts_good_and_ng(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        '{"sample_id":"G1","image":"g.jpg","ground_truth":"GOOD"}\n'
        '{"sample_id":"N1","image":"n.jpg","ground_truth":"NG","defect_type":"missing_component"}\n',
        encoding="utf-8",
    )
    rows = load_manifest(manifest)
    assert [row["sample_id"] for row in rows] == ["G1", "N1"]


def test_load_manifest_rejects_invalid_ground_truth(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text('{"sample_id":"X","image":"x.jpg","ground_truth":"PASS"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="ground_truth"):
        load_manifest(manifest)


def test_load_manifest_rejects_missing_required_field(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text('{"sample_id":"X","image":"x.jpg"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="ground_truth"):
        load_manifest(manifest)


def test_load_manifest_rejects_duplicate_sample_id(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        '{"sample_id":"X","image":"x1.jpg","ground_truth":"GOOD"}\n'
        '{"sample_id":"X","image":"x2.jpg","ground_truth":"NG"}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate sample_id"):
        load_manifest(manifest)


def test_runtime_fail_is_reported_as_ng() -> None:
    assert normalize_prediction("FAIL") == "NG"
    assert normalize_prediction("PASS") == "PASS"
    assert normalize_prediction("UNCERTAIN") == "UNCERTAIN"


def _write_trial_files(tmp_path: Path, predictions: list[dict]) -> tuple[Path, Path]:
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        '{"sample_id":"G1","image":"g.jpg","ground_truth":"GOOD","defect_type":"good_reference"}\n'
        '{"sample_id":"N1","image":"n.jpg","ground_truth":"NG","defect_type":"missing_component"}\n',
        encoding="utf-8",
    )
    prediction_path = tmp_path / "predictions.jsonl"
    prediction_path.write_text(
        "".join(json.dumps(row) + "\n" for row in predictions),
        encoding="utf-8",
    )
    return manifest, prediction_path


def test_evaluation_rejects_incomplete_predictions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, predictions = _write_trial_files(
        tmp_path,
        [{"sample_id": "G1", "prediction": "PASS"}],
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "evaluate_real_trial.py",
            str(manifest),
            "--predictions",
            str(predictions),
            "--output-dir",
            str(tmp_path / "results"),
        ],
    )
    with pytest.raises(ValueError, match="complete manifest"):
        evaluate_main()


def test_evaluation_reports_by_defect_type(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, predictions = _write_trial_files(
        tmp_path,
        [
            {"sample_id": "G1", "prediction": "PASS"},
            {"sample_id": "N1", "prediction": "NG"},
        ],
    )
    output_dir = tmp_path / "results"
    monkeypatch.setattr(
        "sys.argv",
        [
            "evaluate_real_trial.py",
            str(manifest),
            "--predictions",
            str(predictions),
            "--output-dir",
            str(output_dir),
        ],
    )
    assert evaluate_main() == 0
    report = json.loads((output_dir / "evaluation.json").read_text(encoding="utf-8"))
    assert report["by_defect_type"]["missing_component"]["total"] == 1
    assert report["by_defect_type"]["missing_component"]["false_accepts"] == 0
    assert "Performance by defect type" in (output_dir / "evaluation.html").read_text(encoding="utf-8")
