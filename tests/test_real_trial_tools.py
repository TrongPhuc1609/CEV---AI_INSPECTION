from pathlib import Path

import pytest

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


def test_runtime_fail_is_reported_as_ng() -> None:
    assert normalize_prediction("FAIL") == "NG"
    assert normalize_prediction("PASS") == "PASS"
    assert normalize_prediction("UNCERTAIN") == "UNCERTAIN"
