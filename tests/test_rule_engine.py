"""
test_rule_engine.py

Integration tests for rule engine.

These tests verify the full pipeline:

input -> loader -> evaluator -> result
"""

import pytest

from regulation_check.rule_engine import check_compliance

# --------------------------------------------------
# Tests
# --------------------------------------------------


def test_rule_engine_success():

    result = check_compliance(
        ingredient="Hydrogen Peroxide",
        concentration_percent=3,
        product_type="Hair product",
        evaluation_date="2026-06-01",
    )

    assert "status" in result


def test_rule_engine_restricted():

    result = check_compliance(
        ingredient="Hydrogen Peroxide",
        concentration_percent=10,
        product_type="Hair product",
        evaluation_date="2026-06-01",
    )

    assert result["status"] in ["Restricted", "Allowed with conditions"]


def test_rule_engine_unknown():

    result = check_compliance(
        ingredient="Unknown Substance",
        concentration_percent=1,
        product_type="Hair product",
        evaluation_date="2026-06-01",
    )

    assert result["status"] == "Unknown"


def test_missing_ingredient():

    with pytest.raises(ValueError):
        check_compliance(
            ingredient="", concentration_percent=1, product_type="Hair product"
        )


def test_negative_concentration():

    with pytest.raises(ValueError):
        check_compliance(
            ingredient="Test", concentration_percent=-1, product_type="Hair product"
        )
