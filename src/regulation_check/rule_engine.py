"""
rule_engine.py

High-level orchestration layer for regulatory compliance evaluation.

This module coordinates:

- Rule loading
- Compliance evaluation
- Result serialization

It does NOT implement business logic directly.
All decision logic lives in evaluator.py.

Design principles:

- deterministic
- auditable
- testable
- separation of concerns
"""

import logging
from datetime import datetime

from regulation_check.evaluator import evaluate_compliance
from regulation_check.loader import load_rules_for_date

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Utilities
# --------------------------------------------------


def validate_date(date_str: str) -> str:
    """
    Validate ISO date format.

    Returns the same string if valid.
    Raises ValueError if invalid.
    """

    datetime.strptime(date_str, "%Y-%m-%d")

    return date_str


def normalize_text(text: str) -> str:
    """
    Normalize input text for deterministic matching.
    """

    if text is None:
        raise ValueError("Text cannot be None")

    return text.strip()


# --------------------------------------------------
# Core Public API
# --------------------------------------------------


def check_compliance(
    ingredient: str,
    concentration_percent: float,
    product_type: str,
    region: str = "EU",
    evaluation_date: str = None,
) -> dict:
    """
    Main entry point for compliance evaluation.

    Parameters
    ----------

    ingredient : str
        Ingredient name

    concentration_percent : float
        Concentration percentage

    product_type : str
        Product type

    region : str
        Regulatory region (default: EU)

    evaluation_date : str
        Evaluation date in ISO format (YYYY-MM-DD)

    Returns
    -------

    dict

        Example:

        {
            "status": "Restricted",
            "conditions": [
                "Maximum allowed concentration: 6%"
            ],
            "regulatory_reference": {
                "annex": "Annex III",
                "entry": "12"
            }
        }
    """

    logger.info("Starting compliance check")

    # --------------------------------------------------
    # Validate inputs
    # --------------------------------------------------

    if not ingredient:
        raise ValueError("ingredient is required")

    if concentration_percent is None:
        raise ValueError("concentration_percent is required")

    if concentration_percent < 0:
        raise ValueError("concentration_percent must be positive")

    if not product_type:
        raise ValueError("product_type is required")

    ingredient = normalize_text(ingredient)
    product_type = normalize_text(product_type)

    # --------------------------------------------------
    # Handle evaluation date
    # --------------------------------------------------

    if evaluation_date is None:
        evaluation_date = datetime.today().strftime("%Y-%m-%d")

    validate_date(evaluation_date)

    logger.info("Evaluation date: %s", evaluation_date)

    # --------------------------------------------------
    # Region validation (future-ready)
    # --------------------------------------------------

    if region != "EU":
        logger.warning("Unsupported region: %s", region)

    # --------------------------------------------------
    # Load rules
    # --------------------------------------------------

    logger.info("Loading rules")

    prohibited_rules, restricted_rules = load_rules_for_date(evaluation_date)

    logger.info(
        "Rules loaded: %s prohibited, %s restricted",
        len(prohibited_rules),
        len(restricted_rules),
    )

    # --------------------------------------------------
    # Evaluate compliance
    # --------------------------------------------------

    logger.info("Evaluating ingredient: %s", ingredient)

    result = evaluate_compliance(
        ingredient=ingredient,
        concentration_percent=concentration_percent,
        product_type=product_type,
        prohibited_rules=prohibited_rules,
        restricted_rules=restricted_rules,
        evaluation_date=evaluation_date,
    )

    # --------------------------------------------------
    # Serialize result
    # --------------------------------------------------

    result_dict = result.to_dict()

    logger.info("Compliance result: %s", result_dict.get("status"))

    return result_dict
