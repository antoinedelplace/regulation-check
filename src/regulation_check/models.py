"""
models.py

Structured data models for regulatory rules and compliance decisions.

Purpose:

- Define explicit schema for rules
- Validate required fields
- Normalize data
- Provide deterministic result structure
- Improve maintainability and testability

Uses Python dataclasses to avoid external dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime

# --------------------------------------------------
# Utilities
# --------------------------------------------------


def normalize_text(text: str) -> str:
    """
    Normalize text for deterministic matching.
    """
    return text.strip().lower()


def validate_date(date_str: str | None) -> str | None:
    """
    Validate ISO date format.
    """

    if date_str is None:
        return None

    datetime.strptime(date_str, "%Y-%m-%d")

    return date_str


# --------------------------------------------------
# Regulatory Reference
# --------------------------------------------------


@dataclass
class RegulatoryReference:
    """
    Represents traceability to regulation.

    Example:

        Annex III
        Entry 12
    """

    annex: str
    entry: str

    def __post_init__(self):

        if not self.annex:
            raise ValueError("annex is required")

        if not self.entry:
            raise ValueError("entry is required")


# --------------------------------------------------
# Rule Model
# --------------------------------------------------


@dataclass
class Rule:
    """
    Represents a regulatory rule.

    Supports:

    - prohibited substances
    - restricted substances
    - transitional periods
    """

    ingredient: str

    max_concentration_percent: float | None = None

    product_types: list[str] | None = None

    placed_on_market_until: str | None = None

    available_until: str | None = None

    regulatory_reference: RegulatoryReference = field(default=None)

    def __post_init__(self):

        if not self.ingredient:
            raise ValueError("ingredient is required")

        self.ingredient = normalize_text(self.ingredient)

        if self.max_concentration_percent is not None:
            if self.max_concentration_percent < 0:
                raise ValueError("max_concentration_percent must be positive")

        self.placed_on_market_until = validate_date(self.placed_on_market_until)

        self.available_until = validate_date(self.available_until)


# --------------------------------------------------
# Compliance Result
# --------------------------------------------------


@dataclass
class ComplianceResult:
    """
    Represents the final compliance decision.
    """

    status: str

    conditions: list[str] = field(default_factory=list)

    regulatory_reference: RegulatoryReference | None = None

    placed_on_market_until: str | None = None

    available_until: str | None = None

    message: str | None = None

    def to_dict(self) -> dict:
        """
        Convert result to JSON-safe dictionary.
        """

        result = {
            "status": self.status,
            "conditions": self.conditions,
        }

        if self.regulatory_reference:
            result["regulatory_reference"] = {
                "annex": self.regulatory_reference.annex,
                "entry": self.regulatory_reference.entry,
            }

        if self.placed_on_market_until:
            result["placed_on_market_until"] = self.placed_on_market_until

        if self.available_until:
            result["available_until"] = self.available_until

        if self.message:
            result["message"] = self.message

        return result


# --------------------------------------------------
# Factory Helpers
# --------------------------------------------------


def build_regulatory_reference(data: dict) -> RegulatoryReference:
    """
    Convert dictionary to RegulatoryReference.
    """

    return RegulatoryReference(
        annex=data.get("annex"),
        entry=data.get("entry"),
    )


def build_rule(data: dict) -> Rule:
    """
    Convert dictionary to Rule object.
    """

    reference = None

    if "regulatory_reference" in data:
        reference = build_regulatory_reference(data["regulatory_reference"])

    return Rule(
        ingredient=data.get("ingredient"),
        max_concentration_percent=data.get("max_concentration_percent"),
        product_types=data.get("product_types"),
        placed_on_market_until=data.get("placed_on_market_until"),
        available_until=data.get("available_until"),
        regulatory_reference=reference,
    )


def build_rules(data_list: list[dict]) -> list[Rule]:
    """
    Convert list of dictionaries to Rule objects.
    """

    return [build_rule(data) for data in data_list]
