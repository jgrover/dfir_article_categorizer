from __future__ import annotations

import classify
from yaml_rules import yaml_payload


def pytest_configure() -> None:
    rules = classify.compile_rules(raw=yaml_payload())
    classify._COMPILED = rules
    classify._apply_defaults(rules)
