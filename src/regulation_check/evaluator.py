"""
evaluator.py

Responsible for applying regulatory rules to determine compliance.

This module contains deterministic decision logic only.
It does NOT load files or handle input/output.

Core responsibilities:

- Match ingredient to rules
- Evaluate prohibited substances
- Apply transitional provisions
- Evaluate restrictions
- Check concentration limits
- Check product type compatibility
- Produce structured compliance results
"""

from datetime import datetime

from regulation_check.models import (
    ComplianceResult,
    Rule,
)

# --------------------------------------------------
# Status Constants
# --------------------------------------------------

STATUS_ALLOWED = "Allowed"
STATUS_ALLOWED_WITH_CONDITIONS = "Allowed with conditions"
STATUS_RESTRICTED = "Restricted"
STATUS_PROHIBITED = "Prohibited"
STATUS_TRANSITIONAL = "Transitional"
STATUS_UNKNOWN = "Unknown"


# --------------------------------------------------
# Utilities
# --------------------------------------------------


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def normalize(text: str) -> str:
    return text.strip().lower()


# --------------------------------------------------
# Rule Matching
# --------------------------------------------------


def find_matching_rule(ingredient: str, rules: list[Rule]) -> Rule | None:
    """
    Find rule matching ingredient name.
    """

    target = normalize(ingredient)

    for rule in rules:
        if rule.ingredient == target:
            return rule

    return None


# --------------------------------------------------
# Transitional Logic
# --------------------------------------------------


def is_within_transitional_period(rule: Rule, evaluation_date: str) -> bool:
    """
    Determine if transitional period applies.
    """

    if not rule.placed_on_market_until:
        return False

    eval_date = parse_date(evaluation_date)

    deadline = parse_date(rule.placed_on_market_until)

    return eval_date <= deadline


# --------------------------------------------------
# Decision Builders
# --------------------------------------------------


def build_prohibited_result(rule: Rule) -> ComplianceResult:

    return ComplianceResult(
        status=STATUS_PROHIBITED, regulatory_reference=rule.regulatory_reference
    )


def build_transitional_result(rule: Rule) -> ComplianceResult:

    return ComplianceResult(
        status=STATUS_TRANSITIONAL,
        regulatory_reference=rule.regulatory_reference,
        placed_on_market_until=rule.placed_on_market_until,
        available_until=rule.available_until,
    )


def build_restricted_result(rule: Rule, conditions: list[str]) -> ComplianceResult:

    return ComplianceResult(
        status=STATUS_RESTRICTED,
        conditions=conditions,
        regulatory_reference=rule.regulatory_reference,
    )


def build_allowed_with_conditions_result(
    rule: Rule, conditions: list[str]
) -> ComplianceResult:

    return ComplianceResult(
        status=STATUS_ALLOWED_WITH_CONDITIONS,
        conditions=conditions,
        regulatory_reference=rule.regulatory_reference,
    )


def build_unknown_result() -> ComplianceResult:

    return ComplianceResult(
        status=STATUS_UNKNOWN, message="Ingredient not found in rule set"
    )


# --------------------------------------------------
# Restriction Evaluation
# --------------------------------------------------


def evaluate_product_type(rule: Rule, product_type: str) -> str | None:
    """
    Check product type compatibility.
    """

    if not rule.product_types:
        return None

    if product_type not in rule.product_types:
        return "Not permitted for this product type"

    return None


def evaluate_concentration(rule: Rule, concentration_percent: float) -> str | None:
    """
    Check concentration limits.
    """

    if rule.max_concentration_percent is None:
        return None

    if concentration_percent > rule.max_concentration_percent:
        return f"Maximum allowed concentration: {rule.max_concentration_percent}%"

    return None


def evaluate_restriction(
    rule: Rule, concentration_percent: float, product_type: str
) -> ComplianceResult:
    """
    Evaluate restriction conditions.
    """

    conditions = []

    product_condition = evaluate_product_type(rule, product_type)

    if product_condition:
        conditions.append(product_condition)

    concentration_condition = evaluate_concentration(rule, concentration_percent)

    if concentration_condition:
        conditions.append(concentration_condition)

    if conditions:
        return build_restricted_result(rule, conditions)

    return build_allowed_with_conditions_result(
        rule,
        [f"Maximum concentration: {rule.max_concentration_percent}%"]
        if rule.max_concentration_percent
        else [],
    )


# --------------------------------------------------
# Main Evaluation Entry
# --------------------------------------------------


def evaluate_compliance(
    ingredient: str,
    concentration_percent: float,
    product_type: str,
    prohibited_rules: list[Rule],
    restricted_rules: list[Rule],
    evaluation_date: str,
) -> ComplianceResult:
    """
    Core compliance evaluation logic.

    Decision priority:

    1) Prohibited
    2) Transitional
    3) Restricted
    4) Allowed / Unknown
    """

    # ------------------------------------------
    # Check prohibited
    # ------------------------------------------

    prohibited_rule = find_matching_rule(ingredient, prohibited_rules)

    if prohibited_rule:
        if is_within_transitional_period(prohibited_rule, evaluation_date):
            return build_transitional_result(prohibited_rule)

        return build_prohibited_result(prohibited_rule)

    # ------------------------------------------
    # Check restricted
    # ------------------------------------------

    restricted_rule = find_matching_rule(ingredient, restricted_rules)

    if restricted_rule:
        return evaluate_restriction(
            restricted_rule, concentration_percent, product_type
        )

    # ------------------------------------------
    # Unknown
    # ------------------------------------------

    return build_unknown_result()
