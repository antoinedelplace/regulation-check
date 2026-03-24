# EU Cosmetics Regulation Rule Engine Prototype

## Overview

This project demonstrates a deterministic rule engine built from the **EU Cosmetics Regulation (EC) No 1223/2009**.

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
    "regulation": "EC 1223/2009",
    "annex": "Annex III",
    "entry": "12",
    "cas_number": "7722-84-1",
    "effective_date": "2025-09-01"
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
├── src/
│   └── regulation_check/
│   │   ├── main.py
│   │   ├── rule_engine.py
│   │   ├── loader.py
│   │   ├── models.py
│   │   └── evaluator.py
│
├── tests/
│   ├── test_evaluator.py
│   ├── test_loader.py
│   ├── test_models.py
│   └── test_rule_engine.py
│
├── data/
│   └── sample_inputs.json
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

* runtime dependencies
* development tools
* testing tools

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
  "ingredient": "Hydrogen Peroxide",
  "allowed": true,
  "max_concentration_percent": 6,
  "product_types": [
    "Hair products"
  ],
  "regulatory_reference": {
    "regulation": "EC 1223/2009",
    "annex": "Annex III",
    "entry": "12",
    "cas_number": "7722-84-1"
  }
}
```

---

### Prohibited Substance Example

```json
{
  "ingredient": "Acetone Oxime",
  "allowed": false,
  "status": "Prohibited",
  "regulatory_reference": {
    "regulation": "EC 1223/2009",
    "annex": "Annex II",
    "entry": "1754",
    "effective_date": "2026-05-01"
  }
}
```

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

```bash
uv run nox
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

## Limitations

This prototype intentionally limits scope.

Current simplifications:

* Partial annex coverage
* Simplified concentration rules
* Limited product categories
* Manual rule validation
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
