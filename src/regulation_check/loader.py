"""
loader.py

Responsible for loading, validating, normalizing, and caching
regulatory rule data.

This module separates data access from rule evaluation logic.

Core responsibilities:

- Discover available rule versions
- Select correct version based on evaluation date
- Load rule files from disk
- Validate rule structure
- Normalize rule data
- Cache loaded rules for performance
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from regulation_check.models import build_rules

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Configuration
# --------------------------------------------------

RULES_DIR = Path("rules")

PROHIBITED_FILE = "prohibited_substances.json"
RESTRICTED_FILE = "restricted_substances.json"

# Simple in-memory cache
_RULE_CACHE: dict[str, tuple[list[dict], list[dict]]] = {}


# --------------------------------------------------
# Date Utilities
# --------------------------------------------------


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


# --------------------------------------------------
# Version Discovery
# --------------------------------------------------


def get_available_versions() -> list[str]:
    """
    Discover rule versions from directory names.

    Expected format:

    rules/
        2025-09-01/
        2026-05-01/
    """

    if not RULES_DIR.exists():
        raise FileNotFoundError("Rules directory not found")

    versions = []

    for path in RULES_DIR.iterdir():
        if path.is_dir():
            try:
                parse_date(path.name)
                versions.append(path.name)

            except ValueError:
                continue

    if not versions:
        raise RuntimeError("No rule versions found")

    return sorted(versions)


# --------------------------------------------------
# Version Selection
# --------------------------------------------------


def select_rule_version(evaluation_date: str) -> str:
    """
    Select the latest rule version
    less than or equal to evaluation date.
    """

    versions = get_available_versions()

    eval_date = parse_date(evaluation_date)

    selected_version = None

    for version in versions:
        version_date = parse_date(version)

        if version_date <= eval_date:
            selected_version = version

    if not selected_version:
        raise RuntimeError(f"No applicable rule version for date {evaluation_date}")

    logger.info("Selected rule version: %s", selected_version)

    return selected_version


# --------------------------------------------------
# File Loading
# --------------------------------------------------


def load_json_file(file_path: Path) -> list[dict]:
    """
    Load JSON safely.
    """

    if not file_path.exists():
        logger.warning("File not found: %s", file_path)
        return []

    try:
        with open(file_path) as f:
            data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("JSON must be a list")

            return data

    except json.JSONDecodeError as err:
        raise RuntimeError from err(f"Invalid JSON file: {file_path}")


# --------------------------------------------------
# Core Loader
# --------------------------------------------------


def load_rules_for_version(version: str) -> tuple[list[dict], list[dict]]:
    """
    Load rule files for a specific version.
    """

    # Check cache first

    if version in _RULE_CACHE:
        logger.debug("Using cached rules for version %s", version)

        return _RULE_CACHE[version]

    version_path = RULES_DIR / version

    prohibited_path = version_path / PROHIBITED_FILE

    restricted_path = version_path / RESTRICTED_FILE

    logger.info("Loading rules for version %s", version)

    prohibited_rules = load_json_file(prohibited_path)

    restricted_rules = load_json_file(restricted_path)

    prohibited_rules = build_rules(prohibited_rules)
    restricted_rules = build_rules(restricted_rules)

    _RULE_CACHE[version] = (prohibited_rules, restricted_rules)

    return (prohibited_rules, restricted_rules)


# --------------------------------------------------
# Public API
# --------------------------------------------------


def load_rules_for_date(evaluation_date: str) -> tuple[list[dict], list[dict]]:
    """
    Main loader entry point.

    Steps:

    1) Select correct rule version
    2) Load rules
    3) Validate rules
    4) Normalize rules
    5) Cache results
    """

    version = select_rule_version(evaluation_date)

    return load_rules_for_version(version)
