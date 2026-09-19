from __future__ import annotations

import re
from pathlib import Path

import classify

ROOT = Path(__file__).resolve().parents[1]
OSINT_NAME = "OSINT, social media & messaging"


def test_all_patterns_compile() -> None:
    raw = classify.load_rules()
    compiled = 0
    for category in raw["categories"]:
        for group in ("patterns", "title_only", "exclude", "weak_patterns"):
            for pattern in category.get(group) or []:
                re.compile(pattern, re.I)
                compiled += 1
    for case in raw.get("special_cases") or []:
        re.compile(str(case["title_pattern"]), re.I)
        compiled += 1
    assert compiled > 0
    classify.compile_rules(raw)


def test_exclusive_categories_are_first() -> None:
    names = classify.CATEGORY_NAMES
    exclusive = [name for name in names if name in classify.EXCLUSIVE_CATEGORIES]
    assert exclusive == names[: len(exclusive)]
    assert exclusive == [
        "DFIR Jobs",
        "Mental Health",
        "Training and Certifications",
    ]


def test_osint_name_is_exact() -> None:
    assert OSINT_NAME in classify.CATEGORY_NAMES


def test_no_skipped_dashboard_categories() -> None:
    expected = [
        "DFIR Jobs",
        "Mental Health",
        "Training and Certifications",
        "CTFs",
        "Podcasts",
        "Mobile forensics",
        "Memory forensics",
        "Disk & file system forensics",
        "Network forensics",
        "Cloud Forensics",
        "Multimedia & camera forensics",
        "Incident Response & Malware",
        "Anti-Forensics",
        "IoT, wearables & embedded",
        "Drone Forensics",
        "Vehicle Forensics",
        "Cryptocurrency & financial crime",
        "AI, ML & generative models",
        "OSINT, social media & messaging",
        "Browser Forensics",
        "OS & Application Forensics",
        "Legal, policy & ethics",
        "Editorial & commentary",
    ]
    assert classify.CATEGORY_NAMES == expected
    assert classify.FALLBACK_CATEGORY == "Digital forensics (general)"
    assert (ROOT / "category_rules.yaml").is_file()
    assert (ROOT / "category_rules.json").is_file()
