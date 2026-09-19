from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _flatten_pattern(value: object) -> str:
    text = "" if value is None else str(value)
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def _flatten_str_list(values: object) -> list[str]:
    if not values:
        return []
    if not isinstance(values, list):
        raise TypeError(f"expected a list of strings, got {type(values).__name__}")
    return [_flatten_pattern(item) for item in values]


def yaml_payload() -> dict:
    import yaml

    raw = yaml.safe_load((ROOT / "category_rules.yaml").read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("YAML root must be a mapping")
    special_cases = []
    for case in raw.get("special_cases") or []:
        if not isinstance(case, dict):
            raise TypeError("special_cases entries must be mappings")
        special_cases.append(
            {
                "id": str(case.get("id") or ""),
                "notes": str(case.get("notes") or ""),
                "title_pattern": _flatten_pattern(case.get("title_pattern")),
                "blob_contains": str(case.get("blob_contains") or ""),
                "blob_fields": [str(field) for field in case.get("blob_fields") or []],
                "labels": [str(label) for label in case.get("labels") or []],
            }
        )
    categories = []
    for cat in raw.get("categories") or []:
        if not isinstance(cat, dict):
            raise TypeError("categories entries must be mappings")
        categories.append(
            {
                "name": str(cat["name"]),
                "exclusive": bool(cat.get("exclusive")),
                "notes": str(cat.get("notes") or ""),
                "patterns": _flatten_str_list(cat.get("patterns")),
                "title_only": _flatten_str_list(cat.get("title_only")),
                "exclude": _flatten_str_list(cat.get("exclude")),
                "weak_patterns": _flatten_str_list(cat.get("weak_patterns")),
            }
        )
    return {
        "version": int(raw.get("version") or 1),
        "fallback": str(raw.get("fallback") or "Digital forensics (general)"),
        "max_labels": int(raw.get("max_labels") or 4),
        "editorial_types": [str(item) for item in raw.get("editorial_types") or []],
        "editorial_category": str(raw.get("editorial_category") or "Editorial & commentary"),
        "special_cases": special_cases,
        "categories": categories,
    }
