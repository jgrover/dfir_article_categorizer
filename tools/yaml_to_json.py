#!/usr/bin/env python3
"""Convert category_rules.yaml (editable source) to category_rules.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "PyYAML is required for this converter. Install dev deps:\n"
        "  python -m pip install -r requirements-dev.txt\n"
    )
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_YAML = ROOT / "category_rules.yaml"
DEFAULT_JSON = ROOT / "category_rules.json"


def _flatten_pattern(value: object) -> str:
    text = "" if value is None else str(value)
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def _flatten_str_list(values: object) -> list[str]:
    if not values:
        return []
    if not isinstance(values, list):
        raise TypeError(f"expected a list of strings, got {type(values).__name__}")
    return [_flatten_pattern(item) for item in values]


def normalize_rules(raw: dict) -> dict:
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


def convert(yaml_path: Path, json_path: Path) -> dict:
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    payload = normalize_rules(raw)
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return payload


def taxonomy_names(payload: dict) -> list[str]:
    names = [cat["name"] for cat in payload["categories"]]
    fallback = payload["fallback"]
    if fallback not in names:
        names.append(fallback)
    return names


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yaml", type=Path, default=DEFAULT_YAML)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument(
        "--emit-taxonomy",
        action="store_true",
        help="Print a JS CATEGORY_TAXONOMY array to stdout after converting.",
    )
    args = parser.parse_args()
    payload = convert(args.yaml, args.json)
    print(f"Wrote {args.json} ({len(payload['categories'])} categories)")
    if args.emit_taxonomy:
        names = taxonomy_names(payload)
        print("const CATEGORY_TAXONOMY = [")
        for name in names:
            print(f"  {json.dumps(name, ensure_ascii=False)},")
        print("];")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
