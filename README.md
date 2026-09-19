# DFIR article categorizer

Shared classification rules for digital-forensics / DFIR articles, news items, and related posts.

**YAML is the editable source of truth.** `category_rules.json` is generated for consumers that can only use the Python standard library (for example a local dashboard that must not depend on PyYAML).

This repository does not fetch feeds or render a UI. It ships the rules, a small stdlib classifier, and the converter/tests used to change those rules safely.

## How classification works

`classify.classify_article(item)` reads a dashboard-shaped dict (`title`, optional `abstract` / `summary` / `excerpt` / `keywords` / `type` / `url` / `link_url` / `source` / `section`) and returns a list of category names.

1. **Special cases** run first. AboutDFIR “Infosec News Nuggets” posts are forced to `Incident Response & Malware`.
2. **Exclusive categories** (`DFIR Jobs`, `Mental Health`, `Training and Certifications`) are first-match and return a single label. Keep them first in the YAML file.
3. Training has **title-only** patterns (real course/program headlines) and **exclude** patterns (ML “training”, certificate authorities, and similar false positives).
4. Remaining categories are **scored** by how many of their patterns hit. Legal and mobile can drop **weak patterns** when an exclude phrase is present.
5. At most **four** labels are kept. Editorial item types (`Editorial`, `Erratum`, `Letter`) append `Editorial & commentary` if it is missing.
6. If nothing matches, the fallback is **`Digital forensics (general)`**.

The literature category **`OSINT, social media & messaging`** is a stable name — do not rename it.

Runtime classification uses only the standard library: load JSON, compile `re.I` patterns, score, cap.

## Repository layout

| File | Role |
| --- | --- |
| `category_rules.yaml` | Edit this |
| `category_rules.json` | Generated; what dashboards should vendor |
| `classify.py` | Stdlib engine (`classify_article`) |
| `tools/yaml_to_json.py` | YAML → JSON converter (needs PyYAML) |
| `tests/` | Pattern compile check + title→label fixtures |
| `schema/category_rules.schema.json` | Optional JSON Schema |

## How to contribute

Edit `category_rules.yaml`, not the JSON. Add or tighten `patterns`, and use `notes` to explain intent (for example why a phrase is title-only or excluded). Keep exclusive categories at the top so first-match behavior stays stable. Prefer YAML single-quoted strings so regex backslashes stay literal; a `|` block is fine for a long pattern (the converter strips wrapping newlines). Do not hand-edit `category_rules.json` — JSON string escaping is different (`\\b` vs `\b`) and will drift. After you change the YAML, run `python tools/yaml_to_json.py` and `python -m pytest`, then open a pull request.

### Regex caveats

- Patterns are compiled with `re.IGNORECASE`.
- In YAML, `'\bdfir jobs\b'` is a regex word-boundary. In JSON that same pattern must be `"\\bdfir jobs\\b"`.
- A YAML `|` block may include a trailing newline; `tools/yaml_to_json.py` flattens that so the compiled regex does not change.
- Test both the title and a typical excerpt. Training title-only rules exist because footer CTAs such as “training program” would otherwise exclusive-tag unrelated interviews.

## Development

Python 3.8+ for `classify.py`. PyYAML and pytest are **dev** dependencies of this repo only:

```bat
python -m pip install -r requirements-dev.txt
python tools/yaml_to_json.py
python -m pytest
```

Print a JS `CATEGORY_TAXONOMY` array (names plus fallback) after converting:

```bat
python tools/yaml_to_json.py --emit-taxonomy
```

## Using the JSON from another project

Copy `category_rules.json` (and optionally `classify.py`) into the consumer. Do not live-fetch GitHub at startup — vendor or pin a revision. The classifier is stdlib-only:

```python
from classify import classify_article

classify_article({"title": "Android WhatsApp messaging artefacts on GrapheneOS"})
```

## License

MIT
