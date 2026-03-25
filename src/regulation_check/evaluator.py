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

import re
from datetime import datetime

from rapidfuzz import fuzz

from regulation_check.models import ComplianceResult, Rule

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
# Fuzzy Matching Configuration
# --------------------------------------------------
INGREDIENT_MATCH_THRESHOLD = 90
INGREDIENT_MATCH_MARGIN = 5
# Product-type labels vary a lot across inputs and rule datasets.
# We use a lower threshold, but also normalize away generic "product(s)"
# tokens to reduce false positives (e.g., "Hair product" vs "Oral products").
PRODUCT_TYPE_MATCH_THRESHOLD = 60


# --------------------------------------------------
# Utilities
# --------------------------------------------------


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def normalize(text: str) -> str:
    return text.strip().lower()


def normalize_for_fuzzy(text: str) -> str:
    """
    Normalize text for fuzzy matching.

    Product types in the rules dataset often look like "(a) Hair products".
    We strip leading "(<letter>)" prefixes so user inputs like "Hair product"
    can still match.
    """

    if text is None:
        return ""

    text = text.strip().lower()

    # Remove leading "(a)" / "(12)" prefixes.
    text = re.sub(r"^\s*\(\s*[a-z0-9]+\s*\)\s*", "", text)

    # Replace punctuation with spaces.
    text = text.replace("(", " ").replace(")", " ")
    text = re.sub(r"[^a-z0-9%]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Drop generic product tokens that create false positives.
    # Example: "Hair product" and "Oral products" look similar due to "product(s)".
    tokens = [t for t in text.split() if t not in {"product", "products"}]
    return " ".join(tokens).strip()


def fuzzy_best_score(query: str, candidates: list[str]) -> int:
    """
    Compute best RapidFuzz score between `query` and `candidates`.
    """

    q = normalize_for_fuzzy(query)
    if not q:
        return 0

    best = 0
    for c in candidates:
        best = max(best, fuzz.token_set_ratio(q, normalize_for_fuzzy(c)))
    return best


# --------------------------------------------------
# Rule Matching
# --------------------------------------------------


def find_matching_rules(ingredient: str, rules: list[Rule]) -> list[Rule]:
    """
    Find all rules matching ingredient name.
    """
    if not rules:
        return []

    target = normalize_for_fuzzy(ingredient)
    if not target:
        return []

    scored: list[tuple[int, Rule]] = [
        (fuzz.token_set_ratio(target, normalize_for_fuzzy(rule.ingredient)), rule)
        for rule in rules
    ]

    best_score = max(scored, key=lambda x: x[0])[0] if scored else 0
    if best_score < INGREDIENT_MATCH_THRESHOLD:
        return []

    cutoff = max(INGREDIENT_MATCH_THRESHOLD, best_score - INGREDIENT_MATCH_MARGIN)
    return [rule for score, rule in scored if score >= cutoff]


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

    best_score = fuzzy_best_score(product_type, rule.product_types)
    if best_score < PRODUCT_TYPE_MATCH_THRESHOLD:
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
        # If product type doesn't match, the concentration limit in this rule
        # is not applicable, so we do not evaluate concentration.
        return build_restricted_result(rule, [product_condition])

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
        if not rule.product_types
        or fuzzy_best_score(product_type, rule.product_types)
        >= PRODUCT_TYPE_MATCH_THRESHOLD
    ]

    candidate_rules = applicable_rules if applicable_rules else rules

    evaluations: list[tuple[Rule, ComplianceResult]] = [
        (rule, evaluate_restriction(rule, concentration_percent, product_type))
        for rule in candidate_rules
    ]

    restricted_evaluations = [
        (rule, result)
        for rule, result in evaluations
        if result.status == STATUS_RESTRICTED
    ]
    if restricted_evaluations:
        merged_conditions: list[str] = []
        for _, result in restricted_evaluations:
            for condition in result.conditions:
                if condition not in merged_conditions:
                    merged_conditions.append(condition)
        return build_restricted_result(candidate_rules[0], merged_conditions)

    allowed_evaluations = [
        (rule, result)
        for rule, result in evaluations
        if result.status == STATUS_ALLOWED_WITH_CONDITIONS
    ]
    if allowed_evaluations:
        merged_conditions: list[str] = []
        for _, result in allowed_evaluations:
            for condition in result.conditions:
                if condition not in merged_conditions:
                    merged_conditions.append(condition)
        return build_allowed_with_conditions_result(
            allowed_evaluations[0][0], merged_conditions
        )

    # evaluate_restriction always returns restricted or allowed-with-conditions.
    return build_restricted_result(candidate_rules[0], ["No applicable rule match"])


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
