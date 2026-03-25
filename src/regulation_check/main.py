"""
main.py

Entry point for the EU Cosmetics Regulation Rule Engine.

This script evaluates ingredient compliance against structured
regulatory rules derived from Regulation (EC) No 1223/2009.

Usage:

python main.py

python main.py --ingredient "Hydrogen Peroxide" \
               --concentration 3 \
               --product_type "Hair product" \
               --evaluation_date 2026-06-01

python main.py --input_file data/sample_inputs.json
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from regulation_check.rule_engine import check_compliance

# --------------------------------------------------
# Logging Configuration
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Helpers
# --------------------------------------------------


def validate_date(date_str: str) -> str:
    """
    Validate ISO date format.

    Returns validated date string.
    """

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str

    except ValueError:
        logger.error("Invalid date format. Use YYYY-MM-DD.")
        sys.exit(1)


def load_input_file(file_path: str) -> dict:
    """
    Load JSON input file.
    """

    path = Path(file_path)

    if not path.exists():
        logger.error("Input file not found: %s", file_path)
        sys.exit(1)

    try:
        with open(path) as f:
            return json.load(f)

    except json.JSONDecodeError:
        logger.error("Invalid JSON file.")
        sys.exit(1)


def print_result(result: dict) -> None:
    """
    Pretty-print compliance result.
    """

    print("\nCompliance Result")
    print("-" * 60)

    print(json.dumps(result, indent=2))

    print("-" * 60)


# --------------------------------------------------
# CLI
# --------------------------------------------------


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="EU Cosmetics Regulation Compliance Checker"
    )

    parser.add_argument("--ingredient", type=str, help="Ingredient name")

    parser.add_argument("--concentration", type=float, help="Concentration percentage")

    parser.add_argument("--product_type", type=str, help="Product type")

    parser.add_argument("--region", type=str, default="EU", help="Region (default: EU)")

    parser.add_argument(
        "--evaluation_date",
        type=str,
        default=datetime.today().strftime("%Y-%m-%d"),
        help="Evaluation date (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--input_file", type=str, help="JSON file with compliance query"
    )

    return parser.parse_args()


# --------------------------------------------------
# Main
# --------------------------------------------------


def main():
    args = parse_arguments()

    logger.info("Starting compliance evaluation")

    # Validate date
    evaluation_date = validate_date(args.evaluation_date)

    # ------------------------------------------
    # Input from file
    # ------------------------------------------

    if args.input_file:
        logger.info("Loading input from file")

        data = load_input_file(args.input_file)

        required_fields = ["ingredient", "concentration_percent", "product_type"]

        for field in required_fields:
            if field not in data:
                logger.error("Missing required field in input file: %s", field)
                sys.exit(1)

        # If provided, the JSON input should drive the evaluation date.
        evaluation_date = validate_date(
            data.get("evaluation_date") or evaluation_date
        )

        ingredient = data["ingredient"]
        concentration = data["concentration_percent"]
        product_type = data["product_type"]
        region = data.get("region", "EU")

    # ------------------------------------------
    # Input from CLI
    # ------------------------------------------

    else:
        if not all([args.ingredient, args.concentration, args.product_type]):
            logger.error(
                "Missing required arguments.\n"
                "Provide either:\n"
                "--input_file\n"
                "or\n"
                "--ingredient --concentration --product_type"
            )
            sys.exit(1)

        ingredient = args.ingredient
        concentration = args.concentration
        product_type = args.product_type
        region = args.region

    # ------------------------------------------
    # Run Rule Engine
    # ------------------------------------------

    logger.info("Evaluating ingredient: %s", ingredient)

    try:
        result = check_compliance(
            ingredient=ingredient,
            concentration_percent=concentration,
            product_type=product_type,
            region=region,
            evaluation_date=evaluation_date,
        )

        print_result(result)

    except Exception as e:
        logger.exception("Compliance evaluation failed")

        result = {"status": "Error", "message": str(e)}

        print_result(result)

        sys.exit(1)


# --------------------------------------------------

if __name__ == "__main__":
    main()
