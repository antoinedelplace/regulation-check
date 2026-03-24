"""
Build rules/.../restricted_substances.json from Annex III of consolidated Regulation
1223/2009 (EUR-Lex HTML). Uses pandas.read_html (requires lxml, beautifulsoup4).

Usage:
    pip install pandas lxml beautifulsoup4
    python scripts/parse_annex_iii_from_eurlex_html.py \\
        [--url URL] <output.json>
"""

from __future__ import annotations

import argparse
import io
import json
import re
import urllib.request

import pandas as pd

ANNEX_III_TABLE_INDEX = 4
USER_AGENT = "Mozilla/5.0 (compatible; regulation-check/0.1)"


def fetch_html(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def normalize_ws(s: str) -> str:
    s = s.replace("\xa0", " ").replace("\u2009", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_float_eu(num: str) -> float:
    return float(num.replace(",", ".").replace(" ", ""))


REF_RE = re.compile(r"^\d+[a-z]?$")


def is_noise_row(col5: str, col6: str, col7: str) -> bool:
    """Skip amendment / footnote rows that repeat a reference number."""
    blob = normalize_ws(f"{col5} {col6} {col7}")
    if not blob:
        return False
    if blob[0] in "\u25bc\u25ba":  # ▼ ►
        return True
    if re.match(r"^M\d+\b", blob):
        return True
    return False


def is_data_ref(cell: object) -> bool:
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return False
    s = str(cell).strip()
    return bool(REF_RE.match(s))


ROMAN_PCT_RE = re.compile(
    r"\(([ivxlcdm]+)\)\s*([\d,\.]+)\s*(?:%|‰)",
    re.IGNORECASE,
)

PLAIN_PCT_RE = re.compile(
    r"(?<!\()(?:^|[\s;])([\d,\.]+)\s*(?:%|‰)(?!\s*\))",
)


def extract_percent_pairs(col6: str, col7: str) -> list[tuple[float | None, str]]:
    """
    Return list of (max_percent or None, product_type_hint_suffix).
    When multiple (i)/(ii) blocks exist, pair with col7 segments.
    """
    c6 = normalize_ws(col6)
    c7 = normalize_ws(col7)
    if not c6 and not c7:
        return []

    roman_matches = list(ROMAN_PCT_RE.finditer(c6))
    if len(roman_matches) >= 2:
        out: list[tuple[float | None, str]] = []
        for m in roman_matches:
            # Regex group(1) is the Roman label; group(2) is the numeric part.
            # The Roman label itself isn't needed here, since we use m.group(1)
            # again when building the segment-matching pattern.
            _, num = m.group(1).lower(), m.group(2)
            try:
                pct = parse_float_eu(num)
            except ValueError:
                pct = None
            # Pull segment from col7 after same roman label
            seg = ""
            pat = rf"\({re.escape(m.group(1))}\)\s*([^(]*?)(?=\([ivxlcdm]+\)|$)"
            seg_m = re.search(pat, c7, flags=re.IGNORECASE | re.DOTALL)
            if seg_m:
                seg = normalize_ws(seg_m.group(1))
            out.append((pct, seg))
        return out

    # Single or multiple plain percentages
    nums = []
    for m in PLAIN_PCT_RE.finditer(c6):
        try:
            nums.append(parse_float_eu(m.group(1)))
        except ValueError:
            continue
    if not nums:
        # try col7 (some rows put % only in 'other')
        for m in PLAIN_PCT_RE.finditer(c7):
            try:
                nums.append(parse_float_eu(m.group(1)))
            except ValueError:
                continue
    if not nums:
        return []

    if len(nums) == 1:
        return [(nums[0], "")]
    # Multiple plain percents — emit one rule each with same product type blob
    return [(n, "") for n in nums]


def build_product_type(col5: str, suffix: str) -> str | None:
    base = normalize_ws(col5)
    suf = normalize_ws(suffix)
    if base and suf:
        return f"{base} — {suf}"
    if base:
        return base
    if suf:
        return suf
    return None


def row_to_rules(row: pd.Series) -> list[dict]:
    ref = str(row.iloc[0]).strip()
    col1 = "" if pd.isna(row.iloc[1]) else str(row.iloc[1])
    col2 = "" if pd.isna(row.iloc[2]) else str(row.iloc[2])
    col5 = "" if pd.isna(row.iloc[5]) else str(row.iloc[5])
    col6 = "" if pd.isna(row.iloc[6]) else str(row.iloc[6])
    col7 = "" if pd.isna(row.iloc[7]) else str(row.iloc[7])

    if is_noise_row(col5, col6, col7):
        return []

    ingredient = normalize_ws(col2) if normalize_ws(col2) else normalize_ws(col1)
    if not ingredient:
        return []

    pairs = extract_percent_pairs(col6, col7)
    if not pairs:
        # Qualitative-only row: still record for traceability
        pt = build_product_type(col5, "")
        return [
            {
                "ingredient": ingredient,
                "max_concentration_percent": None,
                "product_types": [pt] if pt else [],
                "regulatory_reference": {"annex": "Annex III", "entry": ref},
            }
        ]

    rules: list[dict] = []
    for pct, suf in pairs:
        pt = build_product_type(col5, suf)
        r = {
            "ingredient": ingredient,
            "max_concentration_percent": pct,
            "product_types": [pt] if pt else [],
            "regulatory_reference": {"annex": "Annex III", "entry": ref},
        }
        rules.append(r)
    return rules


def parse_annex_iii_table(df: pd.DataFrame) -> list[dict]:
    all_rules: list[dict] = []
    seen: set[tuple] = set()

    for idx in range(len(df)):
        row = df.iloc[idx]
        if not is_data_ref(row.iloc[0]):
            continue
        for r in row_to_rules(row):
            key = (
                r["ingredient"].lower(),
                r["regulatory_reference"]["entry"],
                r["max_concentration_percent"],
                tuple(r.get("product_types") or []),
            )
            if key in seen:
                continue
            seen.add(key)
            all_rules.append(r)

    return all_rules


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "output_json",
        help="Path to write restricted_substances.json",
    )
    p.add_argument(
        "--url",
        default="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02009R1223-20250901",
    )
    args = p.parse_args()

    html = fetch_html(args.url)
    dfs = pd.read_html(io.BytesIO(html))
    df = dfs[ANNEX_III_TABLE_INDEX]
    rules = parse_annex_iii_table(df)

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {len(rules)} rules to {args.output_json}")


if __name__ == "__main__":
    main()
