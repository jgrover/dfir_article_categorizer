#!/usr/bin/env python3
"""Stdlib DFIR article classifier. Loads category_rules.json and scores labels."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, parse_qsl, urlencode, urlparse

DEFAULT_RULES_PATH = Path(__file__).resolve().parent / "category_rules.json"

# Same URL folding the dashboard uses when concatenating url/link_url into the
# classify blob, so path patterns such as /jobs/ keep matching the same way.
_TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}


def canonical_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = (parsed.path or "").rstrip("/")
    query = parsed.query or ""
    if host in {"youtube.com", "m.youtube.com", "youtube-nocookie.com"}:
        vid = (parse_qs(query).get("v") or [""])[0]
        if vid:
            return f"youtube.com/watch?v={vid.lower()}"
    if host in {"youtu.be", "www.youtu.be"}:
        vid = path.lstrip("/").split("/")[0]
        if vid:
            return f"youtube.com/watch?v={vid.lower()}"
    kept = [
        (key, value)
        for key, value in parse_qsl(query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_QUERY_KEYS
    ]
    suffix = f"?{urlencode(kept)}" if kept else ""
    return f"{host}{path}{suffix}".lower()


def load_rules(path: Path | None = None) -> dict[str, Any]:
    rules_path = Path(path) if path is not None else DEFAULT_RULES_PATH
    return json.loads(rules_path.read_text(encoding="utf-8"))


class _CompiledCategory:
    __slots__ = (
        "name",
        "exclusive",
        "patterns",
        "title_only",
        "exclude",
        "weak_patterns",
    )

    def __init__(self, raw: dict[str, Any]) -> None:
        self.name = str(raw["name"])
        self.exclusive = bool(raw.get("exclusive"))
        self.patterns = [re.compile(pattern, re.I) for pattern in raw.get("patterns") or []]
        self.title_only = [re.compile(pattern, re.I) for pattern in raw.get("title_only") or []]
        self.exclude = [re.compile(pattern, re.I) for pattern in raw.get("exclude") or []]
        self.weak_patterns = {str(pattern) for pattern in raw.get("weak_patterns") or []}


class _CompiledSpecial:
    __slots__ = ("title_pattern", "blob_contains", "blob_fields", "labels")

    def __init__(self, raw: dict[str, Any]) -> None:
        self.title_pattern = re.compile(str(raw["title_pattern"]), re.I)
        self.blob_contains = str(raw.get("blob_contains") or "").lower()
        self.blob_fields = [str(field) for field in raw.get("blob_fields") or []]
        self.labels = [str(label) for label in raw.get("labels") or []]


class CompiledRules:
    def __init__(self, raw: dict[str, Any]) -> None:
        self.fallback = str(raw.get("fallback") or "Digital forensics (general)")
        self.max_labels = int(raw.get("max_labels") or 4)
        self.editorial_types = {str(item) for item in raw.get("editorial_types") or []}
        self.editorial_category = str(raw.get("editorial_category") or "Editorial & commentary")
        self.special_cases = [_CompiledSpecial(item) for item in raw.get("special_cases") or []]
        self.categories = [_CompiledCategory(item) for item in raw.get("categories") or []]
        self.exclusive_categories = frozenset(cat.name for cat in self.categories if cat.exclusive)
        self.category_names = [cat.name for cat in self.categories]


def compile_rules(raw: dict[str, Any] | None = None, path: Path | None = None) -> CompiledRules:
    return CompiledRules(raw if raw is not None else load_rules(path))


_COMPILED: CompiledRules | None = None


def _apply_defaults(rules: CompiledRules) -> None:
    global EXCLUSIVE_CATEGORIES, CATEGORY_NAMES, FALLBACK_CATEGORY, EDITORIAL_TYPES, EDITORIAL_CATEGORY
    EXCLUSIVE_CATEGORIES = rules.exclusive_categories
    CATEGORY_NAMES = rules.category_names
    FALLBACK_CATEGORY = rules.fallback
    EDITORIAL_TYPES = rules.editorial_types
    EDITORIAL_CATEGORY = rules.editorial_category


def compiled_rules(path: Path | None = None) -> CompiledRules:
    global _COMPILED
    if path is not None:
        return compile_rules(path=path)
    if _COMPILED is None:
        _COMPILED = compile_rules()
        _apply_defaults(_COMPILED)
    return _COMPILED


def _item_text(item: dict[str, Any]) -> str:
    return " ".join(
        [
            str(item.get("title") or ""),
            str(item.get("abstract") or ""),
            str(item.get("summary") or ""),
            str(item.get("excerpt") or ""),
            " ".join(item.get("keywords") or []),
            str(item.get("type") or ""),
            canonical_url(str(item.get("url") or "")),
            canonical_url(str(item.get("link_url") or "")),
            str(item.get("source") or ""),
            str(item.get("section") or ""),
        ]
    )


def _special_case_labels(item: dict[str, Any], rules: CompiledRules) -> list[str] | None:
    title = str(item.get("title") or "")
    for case in rules.special_cases:
        if not case.title_pattern.search(title):
            continue
        blob = " ".join(str(item.get(field) or "") for field in case.blob_fields).lower()
        if case.blob_contains in blob:
            return list(case.labels)
    return None


def _exclude_hit(category: _CompiledCategory, text: str) -> bool:
    return any(pattern.search(text) for pattern in category.exclude)


def classify_article(item: dict[str, Any], rules: CompiledRules | None = None) -> list[str]:
    """Return up to max_labels category names for a dashboard-shaped item."""
    compiled = rules if rules is not None else compiled_rules()
    special = _special_case_labels(item, compiled)
    if special is not None:
        return special
    title = str(item.get("title") or "")
    text = _item_text(item)
    scored: list[tuple[int, str]] = []
    for category in compiled.categories:
        if category.exclusive:
            matched = any(pattern.search(text) for pattern in category.patterns)
            if not matched and category.title_only:
                matched = any(pattern.search(title) for pattern in category.title_only)
            if matched:
                if category.exclude and _exclude_hit(category, text):
                    continue
                return [category.name]
            continue
        hits = [pattern for pattern in category.patterns if pattern.search(text)]
        if hits and category.exclude and _exclude_hit(category, text):
            hits = [pattern for pattern in hits if pattern.pattern not in category.weak_patterns]
        score = len(hits)
        if score:
            scored.append((score, category.name))
    scored.sort(key=lambda row: (-row[0], row[1]))
    categories = [name for _, name in scored[: compiled.max_labels]]
    if item.get("type") in compiled.editorial_types and compiled.editorial_category not in categories:
        categories.append(compiled.editorial_category)
    if not categories:
        categories = [compiled.fallback]
    return categories


EXCLUSIVE_CATEGORIES: frozenset[str] = frozenset()
CATEGORY_NAMES: list[str] = []
FALLBACK_CATEGORY = "Digital forensics (general)"
EDITORIAL_TYPES: set[str] = set()
EDITORIAL_CATEGORY = "Editorial & commentary"

if DEFAULT_RULES_PATH.is_file():
    compiled_rules()
