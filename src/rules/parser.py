"""Parser for the human-readable Rule.cmd format."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict


def _parse_value(value: str) -> Any:
    value = value.strip()
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


@dataclass
class RuleConfig:
    sections: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def get(self, section: str, key: str, default=None):
        return self.sections.get(section, {}).get(key, default)

    def region(self, region_id: str) -> Dict[str, Any]:
        return self.sections.get(f"REGION:{region_id}", {})


def parse_rule_file(path: str | Path) -> RuleConfig:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    sections: Dict[str, Dict[str, Any]] = {}
    current = None

    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            sections.setdefault(current, {})
            continue

        if "=" not in line:
            raise ValueError(f"Invalid Rule.cmd line {line_no}: {raw}")

        if current is None:
            raise ValueError(f"Key outside section at line {line_no}")

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Empty key at line {line_no}")
        sections[current][key] = _parse_value(value)

    return RuleConfig(sections)
