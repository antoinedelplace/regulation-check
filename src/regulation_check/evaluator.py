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


def find_matching_rules(ingredient: str, rules: list[Rule]) -> list[Rule]:
    """
    Find all rules matching ingredient name.
    """
    target = normalize(ingredient)
    return [rule for rule in rules if rule.ingredient == target]


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


def evaluate_restrictions_for_ingredient(
    rules: list[Rule], concentration_percent: float, product_type: str
) -> ComplianceResult:
    """
    Evaluate one or many restricted rules for an ingredient.

    If at least one rule is explicitly applicable to the product type,
    evaluate only those applicable rules. Otherwise evaluate all rules and
    return combined restrictions.
    """
    applicable_rules = [
        rule
        for rule in rules
        if not rule.product_types or product_type in rule.product_types
    ]

    candidate_rules = applicable_rules if applicable_rules else rules

    evaluations = [
        evaluate_restriction(rule, concentration_percent, product_type)
        for rule in candidate_rules
    ]

    # If any candidate allows usage with conditions, ingredient is allowed.
    for result in evaluations:
        if result.status == STATUS_ALLOWED_WITH_CONDITIONS:
            return result

    merged_conditions: list[str] = []
    for result in evaluations:
        for condition in result.conditions:
            if condition not in merged_conditions:
                merged_conditions.append(condition)

    return build_restricted_result(candidate_rules[0], merged_conditions)


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

    prohibited_matches = find_matching_rules(ingredient, prohibited_rules)

    if prohibited_matches:
        prohibited_rule = prohibited_matches[0]
        if is_within_transitional_period(prohibited_rule, evaluation_date):
            return build_transitional_result(prohibited_rule)

        return build_prohibited_result(prohibited_rule)

    # ------------------------------------------
    # Check restricted
    # ------------------------------------------

    restricted_matches = find_matching_rules(ingredient, restricted_rules)
    if restricted_matches:
        return evaluate_restrictions_for_ingredient(
            restricted_matches, concentration_percent, product_type
        )

    # ------------------------------------------
    # Unknown
    # ------------------------------------------

    return build_unknown_result()
