"""
test_evaluator.py

Unit tests for evaluator logic.

These tests validate deterministic regulatory decisions.

Run:

pytest
"""

import pytest

from regulation_check.evaluator import evaluate_compliance
from regulation_check.models import (
    RegulatoryReference,
    Rule,
)

# --------------------------------------------------
# Fixtures
# --------------------------------------------------


@pytest.fixture
def prohibited_rule():
    return Rule(
        ingredient="Acetone Oxime",
        placed_on_market_until="2026-07-31",
        available_until="2028-07-31",
        regulatory_reference=RegulatoryReference(annex="Annex II", entry="1754"),
    )


@pytest.fixture
def restricted_rule():
    return Rule(
        ingredient="Hydrogen Peroxide",
        max_concentration_percent=6,
        product_types=["Hair product"],
        regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
    )


@pytest.fixture
def prohibited_rules(prohibited_rule):
    return [prohibited_rule]


@pytest.fixture
def restricted_rules(restricted_rule):
    return [restricted_rule]


# --------------------------------------------------
# Tests
# --------------------------------------------------


def test_prohibited_substance(prohibited_rules):

    result = evaluate_compliance(
        ingredient="Acetone Oxime",
        concentration_percent=1,
        product_type="Hair product",
        prohibited_rules=prohibited_rules,
        restricted_rules=[],
        evaluation_date="2027-01-01",
    )

    assert result.status == "Prohibited"


def test_transitional_period(prohibited_rules):

    result = evaluate_compliance(
        ingredient="Acetone Oxime",
        concentration_percent=1,
        product_type="Hair product",
        prohibited_rules=prohibited_rules,
        restricted_rules=[],
        evaluation_date="2026-06-01",
    )

    assert result.status == "Transitional"
    assert result.placed_on_market_until == "2026-07-31"


def test_restricted_concentration_exceeded(restricted_rules):

    result = evaluate_compliance(
        ingredient="Hydrogen Peroxide",
        concentration_percent=7,
        product_type="Hair product",
        prohibited_rules=[],
        restricted_rules=restricted_rules,
        evaluation_date="2026-06-01",
    )

    assert result.status == "Restricted"

    assert "Maximum allowed concentration" in result.conditions[0]


def test_allowed_with_conditions(restricted_rules):

    result = evaluate_compliance(
        ingredient="Hydrogen Peroxide",
        concentration_percent=3,
        product_type="Hair product",
        prohibited_rules=[],
        restricted_rules=restricted_rules,
        evaluation_date="2026-06-01",
    )

    assert result.status == "Allowed with conditions"


def test_product_type_not_allowed(restricted_rules):

    result = evaluate_compliance(
        ingredient="Hydrogen Peroxide",
        concentration_percent=3,
        product_type="Skin cream",
        prohibited_rules=[],
        restricted_rules=restricted_rules,
        evaluation_date="2026-06-01",
    )

    assert result.status == "Restricted"

    assert "Not permitted for this product type" in result.conditions


def test_unknown_ingredient():

    result = evaluate_compliance(
        ingredient="Unknown Substance",
        concentration_percent=1,
        product_type="Hair product",
        prohibited_rules=[],
        restricted_rules=[],
        evaluation_date="2026-06-01",
    )

    assert result.status == "Unknown"


def test_case_insensitive_matching(restricted_rules):

    result = evaluate_compliance(
        ingredient="hydrogen peroxide",
        concentration_percent=3,
        product_type="Hair product",
        prohibited_rules=[],
        restricted_rules=restricted_rules,
        evaluation_date="2026-06-01",
    )

    assert result.status == "Allowed with conditions"


def test_multiple_conditions(restricted_rules):

    result = evaluate_compliance(
        ingredient="Hydrogen Peroxide",
        concentration_percent=10,
        product_type="Skin cream",
        prohibited_rules=[],
        restricted_rules=restricted_rules,
        evaluation_date="2026-06-01",
    )

    assert result.status == "Restricted"

    # Product type mismatch means the concentration limit in the rule is not
    # applicable, so we only report "Not permitted ...".
    assert len(result.conditions) == 1
    assert "Not permitted for this product type" in result.conditions
    assert not any("Maximum allowed concentration" in c for c in result.conditions)


def test_transitional_boundary_date(prohibited_rules):

    result = evaluate_compliance(
        ingredient="Acetone Oxime",
        concentration_percent=1,
        product_type="Hair product",
        prohibited_rules=prohibited_rules,
        restricted_rules=[],
        evaluation_date="2026-07-31",
    )

    assert result.status == "Transitional"


def test_after_transitional_deadline(prohibited_rules):

    result = evaluate_compliance(
        ingredient="Acetone Oxime",
        concentration_percent=1,
        product_type="Hair product",
        prohibited_rules=prohibited_rules,
        restricted_rules=[],
        evaluation_date="2026-08-01",
    )

    assert result.status == "Prohibited"


def test_product_type_fuzzy_prefix_normalization():
    # Rules often encode product types like "(a) Hair products".
    # User input may be "Hair product" (singular, no "(a)" prefix).
    rule = Rule(
        ingredient="Hydrogen Peroxide",
        max_concentration_percent=6,
        product_types=["(a) Hair products"],
        regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
    )

    result = evaluate_compliance(
        ingredient="Hydrogen Peroxide",
        concentration_percent=3,
        product_type="Hair product",
        prohibited_rules=[],
        restricted_rules=[rule],
        evaluation_date="2026-06-01",
    )

    assert result.status == "Allowed with conditions"
    assert result.conditions == ["Maximum concentration: 6%"]


def test_product_type_mismatch_does_not_apply_concentration():
    rule = Rule(
        ingredient="Hydrogen Peroxide",
        max_concentration_percent=0.5,
        product_types=["(a) Hair products"],
        regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
    )

    # Concentration exceeds 0.5, but product type doesn't match,
    # so we should NOT report a concentration-based maximum.
    result = evaluate_compliance(
        ingredient="Hydrogen Peroxide",
        concentration_percent=3,
        product_type="Skin cream",
        prohibited_rules=[],
        restricted_rules=[rule],
        evaluation_date="2026-06-01",
    )

    assert result.status == "Restricted"
    assert result.conditions == ["Not permitted for this product type"]
    assert not any("Maximum allowed concentration" in c for c in result.conditions)


def test_restricted_wins_over_allowed_with_conditions():
    allowed_rule = Rule(
        ingredient="Hydrogen Peroxide",
        max_concentration_percent=10,
        product_types=["(a) Hair products"],
        regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
    )
    restricted_rule = Rule(
        ingredient="Hydrogen Peroxide",
        max_concentration_percent=1,
        product_types=["(a) Hair products"],
        regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
    )

    result = evaluate_compliance(
        ingredient="Hydrogen Peroxide",
        concentration_percent=5,
        product_type="Hair product",
        prohibited_rules=[],
        restricted_rules=[allowed_rule, restricted_rule],
        evaluation_date="2026-06-01",
    )

    assert result.status == "Restricted"
    assert "Maximum allowed concentration: 1%" in result.conditions
    assert not any("Maximum concentration:" in c for c in result.conditions)


def test_multiple_restricted_rules_merge_conditions_for_same_product_type():
    rule_1 = Rule(
        ingredient="Hydrogen Peroxide",
        max_concentration_percent=2,
        product_types=["(a) Hair products"],
        regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
    )
    rule_2 = Rule(
        ingredient="Hydrogen Peroxide",
        max_concentration_percent=0.1,
        product_types=["(a) Hair products"],
        regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
    )

    result = evaluate_compliance(
        ingredient="Hydrogen Peroxide",
        concentration_percent=3,
        product_type="Hair product",
        prohibited_rules=[],
        restricted_rules=[rule_1, rule_2],
        evaluation_date="2026-06-01",
    )

    assert result.status == "Restricted"
    assert len(result.conditions) == 2
    assert "Maximum allowed concentration: 2%" in result.conditions
    assert "Maximum allowed concentration: 0.1%" in result.conditions


def test_no_ingredient_match_below_threshold_returns_unknown():
    rule = Rule(
        ingredient="Hydrogen Peroxide",
        max_concentration_percent=6,
        product_types=["(a) Hair products"],
        regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
    )

    result = evaluate_compliance(
        ingredient="Hydrogen Bromide",
        concentration_percent=3,
        product_type="Hair product",
        prohibited_rules=[],
        restricted_rules=[rule],
        evaluation_date="2026-06-01",
    )

    assert result.status == "Unknown"


def test_product_type_threshold_filters_other_constraints():
    hair_rule = Rule(
        ingredient="Hydrogen Peroxide",
        max_concentration_percent=6,
        product_types=["(a) Hair products"],
        regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
    )
    oral_rule = Rule(
        ingredient="Hydrogen Peroxide",
        max_concentration_percent=0.1,
        product_types=["(d) Oral products"],
        regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
    )
    nail_rule = Rule(
        ingredient="Hydrogen Peroxide",
        max_concentration_percent=0.5,
        product_types=["(c) Nail hardening products"],
        regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
    )

    # With product_type="Hair product" we should only apply hair_rule.
    # Therefore concentration=3 should be allowed with conditions (<= 6),
    # even though it would violate oral_rule/nail_rule.
    result = evaluate_compliance(
        ingredient="Hydrogen Peroxide",
        concentration_percent=3,
        product_type="Hair product",
        prohibited_rules=[],
        restricted_rules=[hair_rule, oral_rule, nail_rule],
        evaluation_date="2026-06-01",
    )

    assert result.status == "Allowed with conditions"
    assert result.conditions == ["Maximum concentration: 6%"]
