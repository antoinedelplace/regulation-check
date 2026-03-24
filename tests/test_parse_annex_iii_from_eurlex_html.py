"""
Tests for scripts/parse_annex_iii_from_eurlex_html.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

import parse_annex_iii_from_eurlex_html as annex_iii
from parse_annex_iii_from_eurlex_html import (
    ANNEX_III_TABLE_INDEX,
    build_product_type,
    extract_percent_pairs,
    fetch_html,
    is_data_ref,
    is_noise_row,
    normalize_ws,
    parse_annex_iii_table,
    parse_float_eu,
    row_to_rules,
)


def test_normalize_ws_nbsp() -> None:
    assert normalize_ws("a\u00a0b") == "a b"


def test_parse_float_eu() -> None:
    assert parse_float_eu("0,2") == pytest.approx(0.2)
    assert parse_float_eu("8") == 8.0


def test_is_noise_row() -> None:
    assert is_noise_row("", "", "\u25bcM32") is True
    assert is_noise_row("", "", "M9 footnote") is True
    assert is_noise_row("(a) Hair products", "5 %", "") is False


def test_is_data_ref() -> None:
    assert is_data_ref("2a") is True
    assert is_data_ref("12") is True
    assert is_data_ref("Reference number") is False
    assert is_data_ref(float("nan")) is False


def test_extract_percent_pairs_roman_split() -> None:
    col6 = "(a) (i) 8 %  (ii) 11 %"
    col7 = "(i) General use pH 7 (ii) Professional use pH 8"
    pairs = extract_percent_pairs(col6, col7)
    assert len(pairs) == 2
    assert pairs[0][0] == pytest.approx(8.0)
    assert pairs[1][0] == pytest.approx(11.0)
    assert "general" in pairs[0][1].lower()


def test_extract_percent_pairs_plain_single() -> None:
    pairs = extract_percent_pairs("(b) 5 %", "ready for use")
    assert len(pairs) == 1
    assert pairs[0][0] == pytest.approx(5.0)


def test_build_product_type() -> None:
    assert build_product_type("Base", "Suffix") == "Base — Suffix"
    assert build_product_type("Only base", "") == "Only base"


def test_row_to_rules_with_percents() -> None:
    row = pd.Series(
        {
            0: "3",
            1: "Oxalic acid, its esters and alkaline salts",
            2: "Oxalic acid",
            3: "144-62-7",
            4: "205-634-3",
            5: "Hair products",
            6: "5 %",
            7: "Professional use",
            8: "",
        }
    )
    rules = row_to_rules(row)
    assert len(rules) == 1
    assert rules[0]["max_concentration_percent"] == pytest.approx(5.0)
    assert rules[0]["ingredient"].lower() == "oxalic acid"
    assert rules[0]["regulatory_reference"]["entry"] == "3"


def test_row_to_rules_qualitative_only() -> None:
    row = pd.Series(
        {
            0: "99",
            1: "Some restriction",
            2: "Ingredient X",
            3: "",
            4: "",
            5: "All products",
            6: "",
            7: "No numeric limit in cell",
            8: "",
        }
    )
    rules = row_to_rules(row)
    assert len(rules) == 1
    assert rules[0]["max_concentration_percent"] is None
    assert rules[0]["product_types"] == ["All products"]


def test_row_to_rules_noise_returns_empty() -> None:
    row = pd.Series(
        {
            0: "2a",
            1: "X",
            2: "Y",
            3: "",
            4: "",
            5: "\u25bcB",
            6: "\u25bcB",
            7: "\u25bcB",
            8: "",
        }
    )
    assert row_to_rules(row) == []


def test_parse_annex_iii_table_dedupes() -> None:
    df = pd.DataFrame(
        [
            ["3", "G", "Oxalic acid", "144-62-7", "205-634-3", "Hair", "5 %", "", ""],
            ["3", "G", "Oxalic acid", "144-62-7", "205-634-3", "Hair", "5 %", "", ""],
        ]
    )
    rules = parse_annex_iii_table(df)
    assert len(rules) == 1


def test_main_writes_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    html = b"<html><body><table></table></body></html>"
    tiny_table = pd.DataFrame(
        [
            ["3", "Group", "Oxalic acid", "144-62-7", "205-634-3", "Hair", "5 %", "", ""],
        ]
    )

    out = tmp_path / "restricted.json"

    def fake_fetch(_url: str) -> bytes:
        return html

    def fake_read_html(_bio: object, *_a: object, **_kw: object) -> list:
        return [[], [], [], [], tiny_table]

    monkeypatch.setattr(annex_iii, "fetch_html", fake_fetch)
    monkeypatch.setattr(pd, "read_html", fake_read_html)

    argv = [
        "parse_annex_iii_from_eurlex_html.py",
        str(out),
        "--url",
        "https://example.invalid/test",
    ]
    with patch.object(sys, "argv", argv):
        annex_iii.main()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) >= 1
    assert data[0]["regulatory_reference"]["annex"] == "Annex III"


def test_fetch_html_calls_urlopen() -> None:
    with patch.object(annex_iii.urllib.request, "urlopen") as uo:
        uo.return_value.__enter__.return_value.read.return_value = b"<html/>"
        assert fetch_html("https://example.com/x") == b"<html/>"
        uo.assert_called_once()


def test_annex_iii_table_index_constant() -> None:
    assert ANNEX_III_TABLE_INDEX == 4
