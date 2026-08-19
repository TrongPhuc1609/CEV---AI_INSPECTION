"""Stable hashes used to bind inspection evidence to its configuration."""
from __future__ import annotations

import hashlib
import json


def sha256_json(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def rule_config_hash(config) -> str:
    return sha256_json(config.sections)


def inspection_plan_hash(plan) -> str:
    from dataclasses import asdict
    return sha256_json(asdict(plan))
