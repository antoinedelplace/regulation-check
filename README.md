# EU Cosmetics Regulation Rule Engine Prototype

## Overview

This project demonstrates a deterministic rule engine built from the [**EU Cosmetics Regulation (EC) No 1223/2009**](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02009R1223-20250901#anx_II).

The goal is to transform regulatory text into structured, machine-readable rules that automatically determine whether a cosmetic ingredient is compliant under specific conditions.

The system answers questions such as:

> *For this ingredient, used at this concentration in this type of cosmetic product in the EU, what does the regulation require?*

The response is:

* Deterministic
* Traceable
* Reproducible
* Version-aware
* Explainable

This repository focuses on correctness, transparency, and regulatory reasoning rather than full regulatory coverage.

---

## Key Features

* Deterministic rule engine
* Structured regulatory rules
* Regulation versioning support
* Transitional period handling
* Full regulatory traceability
* Explainable compliance decisions
* Testable rule logic
* AI-assisted rule extraction pipeline
* Modern Python tooling (uv, pytest, ruff, nox, pre-commit)
* Reproducible development environment

---

## Example Query

```json
{
  "ingredient": "Hydrogen Peroxide",
  "concentration_percent": 3,
  "product_type": "Hair product",
  "region": "EU",
  "evaluation_date": "2026-06-01"
}
```

---

## Example Output

```json
{
  "status": "Allowed with conditions",
  "conditions": [
    "Maximum concentration: 6%"
  ],
  "regulatory_reference": {
    "annex": "Annex III",
    "entry": "12"
  }
}
```

---

## Architecture

```
Regulation Text
       │
       ▼
Rule Extraction (AI-assisted)
       │
       ▼
Structured Rules (JSON)
       │
       ▼
Rule Engine (Deterministic Logic)
       │
       ▼
Compliance Decision + Explanation
```

---

## Core Design Principles

* Deterministic decisions
* Regulatory traceability
* Version-aware rule evaluation
* Reproducibility
* Simplicity
* Explainability
* Extensibility

---

## Regulation Versioning

EU cosmetic regulations are updated regularly through amendments.

Amendments apply from specific effective dates and modify Annex II–VI entries.

This system supports rule versioning to ensure that compliance decisions are evaluated against the correct legal state.

---

### Rule Version Structure

```
rules/

    2025-09-01/
        prohibited_substances.json
        restricted_substances.json

    2026-05-01/
        prohibited_substances.json
        restricted_substances.json
```

---

### Rule Metadata Example

```json
{
  "regulation": "EC 1223/2009",
  "amendment": "EU 2026/78",
  "effective_date": "2026-05-01",
  "jurisdiction": "EU"
}
```

---

## Transitional Period Handling

Regulatory amendments may include transitional periods during which products can still be placed on the market or remain available.

The rule engine supports these conditions.

---

### Decision Types

* Allowed
* Allowed with conditions
* Restricted
* Prohibited
* Transitional
* Unknown

---

### Example Transitional Rule

```json
{
  "ingredient": "Example Substance",
  "status": "Transitional",
  "placed_on_market_until": "2026-07-31",
  "available_until": "2028-07-31",
  "regulatory_reference": {
    "annex": "Annex II",
    "entry": "1752"
  }
}
```

---

## Regulatory Scope

This prototype demonstrates regulatory reasoning using a limited subset of the regulation.

---

### Current Scope

* Annex II — Prohibited substances
* Annex III — Restricted substances
* Annex IV — Allowed colorants
* Annex V — Allowed preservatives
* Annex VI — Allowed UV filters
* Concentration limits
* Product-type conditions
* Deterministic compliance evaluation

The **`rules/2025-09-01/`** snapshot is aligned with the consolidated text [**CELEX:02009R1223-20250901**](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02009R1223-20250901#anx_II): **Annex II** and **Annex III** are populated from that source (see [Regenerating rules from EUR-Lex](#regenerating-rules-from-eur-lex)). Other `rules/<date>/` folders may contain smaller illustrative subsets.

---

### Out of Scope

* Full toxicological safety assessment
* Exposure modeling
* Labeling validation
* Product safety reports (PIF)
* Supply chain responsibilities
* Market surveillance workflows
* Multilingual regulatory parsing

---

## Decision Logic

The rule engine evaluates compliance using deterministic logic.

---

### Evaluation Order

1. Load correct rule version
2. Match ingredient
3. Check prohibition status
4. Check restriction conditions
5. Validate concentration limits
6. Apply transitional rules
7. Return decision with explanation

---

## Compliance Evaluation Context

The rule engine evaluates ingredient compliance in the context of:

* Product type
* Intended use
* Concentration level
* Regulatory conditions
* Evaluation date

---

## Project Structure

```
regulation-check/

├── rules/
│   ├── 2025-09-01/
│   │   ├── prohibited_substances.json
│   │   └── restricted_substances.json
│   │
│   └── 2026-05-01/
│       ├── prohibited_substances.json
│       └── restricted_substances.json
│
├── scripts/
│   ├── parse_annex_ii_from_eurlex_txt.py   # Annex II → prohibited_substances.json
│   └── parse_annex_iii_from_eurlex_html.py  # Annex III → restricted_substances.json
│
├── src/
│   └── regulation_check/
│       ├── main.py
│       ├── rule_engine.py
│       ├── loader.py
│       ├── models.py
│       └── evaluator.py
│
├── tests/
│   ├── test_evaluator.py
│   ├── test_loader.py
│   ├── test_models.py
│   └── test_rule_engine.py
│
├── data/
│   └── sample_input.json
│
├── pyproject.toml
├── noxfile.py
├── .pre-commit-config.yaml
├── .gitignore
└── README.md
```

---

## Installation

This project uses **uv** for fast, reproducible Python environments.

### 1) Clone the repository

```bash
git clone git@github.com:antoinedelplace/regulation-check.git

cd regulation-check
```

### 2) Install dependencies

```bash
uv sync --group dev
```

This installs:

* runtime dependencies (the `regulation_check` package has zero runtime third-party dependencies)
* development tools
* testing tools

To regenerate rule JSON from EUR-Lex (optional), also install the **extract** group:

```bash
uv sync --group dev --group extract
```

---

## Usage

Run a compliance check using a sample input file:

```bash
uv run regulation-check \
    --input_file data/sample_input.json
```

---

## Programmatic Usage

```python
from regulation_check.rule_engine import check_compliance

result = check_compliance(
    ingredient="Hydrogen Peroxide",
    concentration_percent=3,
    product_type="Hair product",
    region="EU",
    evaluation_date="2026-06-01"
)

print(result)
```

---

## Rule Format

Rules are stored in structured JSON.

---

### Restricted Substance Example

```json
{
  "ingredient": "hydrogen peroxide",
  "max_concentration_percent": 6,
  "product_types": [
    "Hair products"
  ],
  "regulatory_reference": {
    "annex": "Annex III",
    "entry": "12"
  }
}
```

(Ingredient names are normalized to lowercase for matching; source JSON may use any casing.)

---

### Prohibited Substance Example

```json
{
  "ingredient": "acetone oxime",
  "placed_on_market_until": "2026-07-31",
  "available_until": "2028-07-31",
  "regulatory_reference": {
    "annex": "Annex II",
    "entry": "1754"
  }
}
```

Optional transitional fields apply only when an amendment sets a phase-out period.

---

## Rule Engine Responsibilities

The rule engine is responsible for:

* Loading rule versions
* Matching ingredients
* Evaluating restrictions
* Applying transitional logic
* Returning compliance decisions
* Providing regulatory traceability

The engine does not rely on probabilistic reasoning.

All decisions are deterministic.

---

## Development Workflow

### Run tests

Use Nox so the same pytest options as CI are applied (including coverage for `src/` and `scripts/`):

```bash
uv run nox -s tests
```

For a quick run without Nox:

```bash
uv run pytest
```

---

### Run linting

```bash
uv run ruff check .
```

---

### Format code

```bash
uv run ruff format .
```

---

### Run all automation

Lint and tests (same as the `ci` session):

```bash
uv run nox
```

Or explicitly:

```bash
uv run nox -s ci
```

---

### Install Git hooks

```bash
uv run pre-commit install
```

---

## Example Test Cases

* Allowed ingredient within limit
* Restricted ingredient exceeding limit
* Prohibited ingredient
* Transitional rule evaluation
* Version-specific rule validation
* Unknown ingredient handling

Testing ensures deterministic behavior.

---

## Use of AI

Artificial Intelligence was used as a development tool within the pipeline.

AI assisted with:

* Parsing regulatory text
* Extracting structured rules
* Normalizing regulatory language
* Generating initial rule candidates
* Identifying edge cases

The final rule engine itself is deterministic and rule-based.

AI is not used to make compliance decisions.

---

## Regulation Update Pipeline

Regulation updates are handled through a structured ingestion workflow.

---

### Update Steps

1. Detect new amendment publication
2. Parse updated annex entries
3. Generate structured rule changes
4. Validate rule consistency
5. Publish new rule version

---

## Regenerating rules from EUR-Lex

Scripts under `scripts/` rebuild **Annex II** (prohibited) and **Annex III** (restricted) JSON from the **consolidated** Regulation EC 1223/2009 as published on EUR-Lex. Install the **extract** dependency group first (`uv sync --group extract`).

### Annex II — `prohibited_substances.json`

The parser expects a **plain-text** line dump of the HTML page (for example, save the EUR-Lex “Web” view to a `.txt` file, or use the same structure as the [Annex II anchor](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02009R1223-20250901#anx_II) content).

```bash
python scripts/parse_annex_ii_from_eurlex_txt.py path/to/eurlex_annex_ii.txt rules/2025-09-01/prohibited_substances.json
```

### Annex III — `restricted_substances.json`

Parses the HTML table directly (uses `pandas.read_html`).

```bash
python scripts/parse_annex_iii_from_eurlex_html.py rules/2025-09-01/restricted_substances.json
```

Optional: `--url` to point at another consolidated URI (default: `CELEX:02009R1223-20250901`).

**Notes:**

* Matching in the engine is **exact** on normalized ingredient strings; long Annex III product-type labels are stored as in the regulation.
* Rows with only qualitative conditions may use `"max_concentration_percent": null`.
* Amendment-only rows in the HTML are filtered out where possible.

---

## Limitations

This prototype intentionally limits scope.

Current simplifications:

* Annex IV–VI are not loaded by the default rule files (only II and III in `rules/<version>/`).
* Ingredient matching is exact (no fuzzy or synonym resolution).
* Extracted Annex III rows may still need manual review for edge cases.
* No automated regulatory monitoring

---

## Future Improvements

With additional development time, the system could be extended to:

* Full regulation coverage
* Automated amendment detection
* API interface
* Web dashboard
* Rule validation tooling
* Multi-region regulatory support
* Version comparison engine
* Audit logging
* Regulatory impact analysis

---

## License

MIT License
