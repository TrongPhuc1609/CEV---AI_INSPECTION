# Physical Trial Dataset

This directory is reserved for **real PCB image evidence** used during V1.9 commissioning and offline validation.

## What belongs here

- Real camera frames or exported production images.
- A `manifest.jsonl` describing the ground truth for every image.
- Optional review notes and inspection reports.

Do not commit confidential production data, customer-identifying information, or uncontrolled images. Keep large datasets outside Git when appropriate and record their checksum/location in the manifest or trial report.

## Ground-truth contract

Each manifest row must contain:

- `sample_id`: unique stable sample identifier.
- `image`: path relative to this repository.
- `ground_truth`: `GOOD` or `NG`.
- `defect_type`: optional defect category such as `missing_component`, `extra_component`, `wrong_component`, `grease_missing`, `grease_insufficient`, `grease_wrong_zone`, or `unknown`.
- `notes`: optional operator/reviewer note.

Example:

```json
{"sample_id":"GOOD_001","image":"data/physical_trial/images/GOOD_001.jpg","ground_truth":"GOOD","defect_type":"","notes":"Reference good board"}
{"sample_id":"NG_001","image":"data/physical_trial/images/NG_001.jpg","ground_truth":"NG","defect_type":"missing_component","notes":"Verified by operator"}
```

## Minimum validation set

Do not claim real-world model/rule acceptance from one image. Build a labelled set containing:

1. GOOD boards across normal lighting/position variation.
2. NG boards for every supported defect class.
3. Borderline/uncertain samples.
4. Challenging illumination, blur, focus and positioning cases.

The acceptance criteria must be agreed before the test run. The repository tooling reports false accepts, false rejects and uncertain-rate separately so these are not hidden by a single accuracy number.

## Running the trial

1. Put images under `data/physical_trial/images/`.
2. Create `manifest.jsonl` using the contract above.
3. Run `python tools/run_real_trial_batch.py data/physical_trial/manifest.jsonl`.
4. Run `python tools/evaluate_real_trial.py data/physical_trial/manifest.jsonl --predictions data/physical_trial/results/predictions.jsonl`.
5. Archive the generated JSON/HTML report as test evidence.

The current V1.9 machine-vision recipe is a measurement-boundary test. It does **not** prove component or grease defect classification until product-specific ROIs, labels, algorithms and acceptance thresholds have been commissioned from real evidence.
