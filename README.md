# DFIR article categorizer

Shared classification rules for digital-forensics / DFIR articles, news items, and related posts.

**YAML is the only published rules file.** This repository does not ship generated JSON. Consumers that must stay on the Python standard library convert the YAML in their own project, then load JSON at runtime.

This repository does not fetch feeds or render a UI. It ships the YAML rules, a small stdlib classifier for JSON that consumers generate, and tests.

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
| `category_rules.yaml` | Edit this (source of truth) |
| `classify.py` | Stdlib engine (`classify_article`) that loads consumer-generated JSON |
| `tests/` | Pattern compile check + title→label fixtures |
| `schema/category_rules.schema.json` | Optional schema for the JSON consumers generate |

## How to contribute

Edit `category_rules.yaml`. Add or tighten `patterns`, and use `notes` to explain intent (for example why a phrase is title-only or excluded). Keep exclusive categories at the top so first-match behavior stays stable. Prefer YAML single-quoted strings so regex backslashes stay literal; a `|` block is fine for a long pattern (consumers should strip wrapping newlines when converting). After you change the YAML, run `python -m pytest`, then open a pull request.

### Regex caveats

- Patterns are compiled with `re.IGNORECASE`.
- In YAML, `'\bdfir jobs\b'` is a regex word-boundary. In generated JSON that same pattern must be `"\\bdfir jobs\\b"`.
- A YAML `|` block may include a trailing newline; flatten that during conversion so the compiled regex does not change.
- Test both the title and a typical excerpt. Training title-only rules exist because footer CTAs such as “training program” would otherwise exclusive-tag unrelated interviews.

## Development

Python 3.8+ for `classify.py`. PyYAML and pytest are **dev** dependencies of this repo (tests load YAML directly):

```bat
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Using the rules from another project

Copy `category_rules.yaml` into the consumer. Convert it to JSON **in that project** (PyYAML is only needed for the conversion step). Vendor or pin a revision of the YAML; do not live-fetch GitHub at startup.

Example: a local dashboard can keep a copy of this YAML, run a converter (`python tools/yaml_to_json.py`) to write `category_rules.json`, then load that JSON with the stdlib classifier:

```python
from classify import classify_article

classify_article({"title": "Android WhatsApp messaging artefacts on GrapheneOS"})
```

## License

MIT
