# AI INSPECTION - RULE CONFIGURATION
# Version: 0.2.0
# Human-readable shared rule file.
# Product-specific / inspection-changing values belong here.

[PROJECT]
name=AI_Inspection
version=0.2.0

[PRODUCT]
id=PRODUCT_A

[INSPECTION]
final_decision=ALL_REQUIRED_REGIONS_PASS
uncertain_policy=RECHECK_THEN_NG

[REGION:R01]
name=Component_Count
method=DETECTION
enabled=true
expected_component=BOLT_M6
expected_quantity=4
min_confidence=0.85
position_check=false

[REGION:R02]
name=Component_Type
method=DETECTION_CLASSIFICATION
enabled=true
expected_component=BOLT_M8
expected_quantity=2
min_confidence=0.90
position_check=true
position_tolerance_px=15

[REGION:R03]
name=Grease_Presence
method=SEGMENTATION
enabled=true
grease_required=true
min_confidence=0.80
min_coverage_percent=60
max_coverage_percent=100
roi_only=true

[REGION:R04]
name=Grease_Zone
method=SEGMENTATION
enabled=true
grease_required=true
min_confidence=0.80
min_coverage_percent=50
forbidden_zone_check=true

[RECHECK]
enabled=true
max_attempts=2
min_confidence=0.70
multi_frame=true

[OUTPUT]
save_evidence_image=true
save_raw_result=true
save_final_result=true
