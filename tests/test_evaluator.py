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

    assert len(result.conditions) == 2


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
