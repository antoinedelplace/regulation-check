"""
test_loader.py

Tests for loader functionality.

Focus:

- version selection
- rule loading
- caching
"""

from regulation_check.loader import (
    get_available_versions,
    load_rules_for_version,
    select_rule_version,
)

# --------------------------------------------------
# Tests
# --------------------------------------------------


def test_versions_exist():

    versions = get_available_versions()

    assert isinstance(versions, list)

    assert len(versions) > 0


def test_select_rule_version():

    version = select_rule_version("2026-06-01")

    assert version <= "2026-06-01"


def test_load_rules_for_version():

    versions = get_available_versions()

    version = versions[-1]

    prohibited, restricted = load_rules_for_version(version)

    assert isinstance(prohibited, list)
    assert isinstance(restricted, list)


def test_loader_cache():

    versions = get_available_versions()

    version = versions[-1]

    first = load_rules_for_version(version)

    second = load_rules_for_version(version)

    assert first == second
