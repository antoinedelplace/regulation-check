"""
test_models.py

Tests for data model validation.
"""

import pytest

from regulation_check.models import (
    ComplianceResult,
    RegulatoryReference,
    Rule,
)

# --------------------------------------------------
# Tests
# --------------------------------------------------


def test_regulatory_reference_creation():

    ref = RegulatoryReference(annex="Annex III", entry="12")

    assert ref.annex == "Annex III"
    assert ref.entry == "12"


def test_rule_creation():

    rule = Rule(
        ingredient="Hydrogen Peroxide",
        max_concentration_percent=6,
        product_types=["Hair product"],
        regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
    )

    assert rule.ingredient == "hydrogen peroxide"


def test_invalid_negative_concentration():

    with pytest.raises(ValueError):
        Rule(
            ingredient="Test",
            max_concentration_percent=-1,
            regulatory_reference=RegulatoryReference(annex="Annex III", entry="12"),
        )


def test_date_validation():

    rule = Rule(
        ingredient="Test",
        placed_on_market_until="2026-07-31",
        regulatory_reference=RegulatoryReference(annex="Annex II", entry="123"),
    )

    assert rule.placed_on_market_until == "2026-07-31"


def test_compliance_result_serialization():

    result = ComplianceResult(status="Allowed", conditions=["Test condition"])

    data = result.to_dict()

    assert data["status"] == "Allowed"
    assert "conditions" in data
