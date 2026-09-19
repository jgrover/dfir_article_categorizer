from __future__ import annotations

import json
from pathlib import Path

import classify

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "classify_cases.json"


def test_title_fixtures_match_captured_dashboard_behavior() -> None:
    rows = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert rows
    for row in rows:
        assert classify.classify_article(row["item"]) == row["labels"]


def test_training_exclude_does_not_exclusive_tag_ml() -> None:
    labels = classify.classify_article(
        {"title": "Training ML models for malware classification"}
    )
    assert "Training and Certifications" not in labels


def test_mobile_weak_patterns_drop_on_vehicle_exclude() -> None:
    labels = classify.classify_article(
        {"title": "Paired smartphone in-vehicle infotainment forensics"}
    )
    assert "Mobile forensics" not in labels
    assert labels == ["Vehicle Forensics"]


def test_fallback_when_nothing_matches() -> None:
    assert classify.classify_article(
        {"title": "A brief note on laboratory accreditation methods"}
    ) == [classify.FALLBACK_CATEGORY]


def test_aboutdfir_nuggets_override() -> None:
    assert classify.classify_article(
        {
            "title": "Infosec News Nuggets — week of Sept 15",
            "source": "AboutDFIR",
            "url": "https://aboutdfir.com/nuggets",
        }
    ) == ["Incident Response & Malware"]


def test_editorial_type_appended() -> None:
    labels = classify.classify_article(
        {"title": "Welcome to the special issue", "type": "Editorial"}
    )
    assert "Editorial & commentary" in labels
