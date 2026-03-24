"""
Tests for scripts/parse_annex_ii_from_eurlex_txt.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from parse_annex_ii_from_eurlex_txt import (
    classify_id_line,
    clean_ingredient,
    consume_cas_ec_block,
    extract_inci_variants,
    is_skippable_line,
    iter_substance_texts,
    looks_like_ref,
    parse_annex_ii,
)


def test_looks_like_ref_strips_trailing_dot() -> None:
    assert looks_like_ref("345.") == 345
    assert looks_like_ref("  42  ") == 42
    assert looks_like_ref("99999") is False


def test_classify_id_line_cas_ec() -> None:
    assert classify_id_line("51-84-3") == "cas"
    assert classify_id_line("200-128-9") == "ec"
    assert classify_id_line("-") == "empty_id"


def test_classify_id_line_prose_with_embedded_cas_returns_none() -> None:
    line = (
        "Salt (CAS 71134-97-9) when used as a substance in hair dye products"
    )
    assert classify_id_line(line) is None


def test_clean_ingredient_strips_markdown_links() -> None:
    s = "Foo [▼M1](https://example.com) bar"
    out = clean_ingredient(s)
    assert "http" not in out.lower()
    assert "foo" in out.lower()


def test_extract_inci_variants() -> None:
    text = "X; [INCI: My INCI Name]"
    assert "My INCI Name" in extract_inci_variants(text)


def test_iter_substance_texts_splits_semicolon() -> None:
    parts = iter_substance_texts("Alpha; Beta")
    assert len(parts) == 2
    assert parts[0].lower().startswith("alpha")


def test_is_skippable_line() -> None:
    assert is_skippable_line("") is True
    assert is_skippable_line("   ") is True
    assert is_skippable_line("[▼X](https://eur-lex.europa.eu/...)") is True
    assert is_skippable_line("Benzene") is False


def test_parse_annex_ii_minimal_table() -> None:
    lines = """
Preamble

ANNEX II

LIST OF SUBSTANCES PROHIBITED IN COSMETIC PRODUCTS

Reference number

a

b

c

d

1

Acetone

67-64-1

200-662-2

2

Benzene

71-43-2

200-753-7

ANNEX III

LIST OF SUBSTANCES WHICH
""".splitlines()

    rules = parse_annex_ii(lines)
    assert len(rules) == 2
    assert rules[0]["ingredient"].lower() == "acetone"
    assert rules[0]["regulatory_reference"]["entry"] == "1"
    assert rules[1]["ingredient"].lower() == "benzene"
    assert rules[1]["regulatory_reference"]["entry"] == "2"


def test_parse_annex_ii_missing_header_raises() -> None:
    with pytest.raises(ValueError, match="Annex II header not found"):
        parse_annex_ii(["no annex here"])


def test_consume_cas_ec_block_advances_index() -> None:
    lines = [
        "1",
        "Name",
        "12-34-5",
        "123-456-7",
        "2",
    ]
    i = consume_cas_ec_block(lines, 2, 1)
    assert i == 4


def test_main_writes_json(tmp_path: Path) -> None:
    inp = tmp_path / "in.txt"
    out = tmp_path / "out.json"
    inp.write_text(
        "\n".join(
            [
                "ANNEX II",
                "LIST OF SUBSTANCES PROHIBITED IN COSMETIC PRODUCTS",
                "d",
                "1",
                "Xylitol",
                "87-99-0",
                "201-788-0",
                "ANNEX III",
            ]
        ),
        encoding="utf-8",
    )

    argv = ["parse_annex_ii_from_eurlex_txt.py", str(inp), str(out)]
    with patch.object(sys, "argv", argv):
        import parse_annex_ii_from_eurlex_txt as mod

        mod.main()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["ingredient"].lower() == "xylitol"


def test_main_usage_exit_code() -> None:
    with patch.object(sys, "argv", ["x"]):
        import parse_annex_ii_from_eurlex_txt as mod

        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == 1
