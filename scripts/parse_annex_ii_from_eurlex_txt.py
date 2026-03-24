"""
One-off helper: parse Annex II table from EUR-Lex markdown-like text dump
and emit prohibited_substances.json entries.

Usage:
    python scripts/parse_annex_ii_from_eurlex_txt.py <input.txt> <output.json>
"""

from __future__ import annotations

import json
import re
import sys


def strip_footnotes(s: str) -> str:
    s = re.sub(r"\s*\[\d+\]\s*$", "", s)
    s = re.sub(r"\s*\(\d+\)\s*$", "", s)
    return s.strip()


def clean_ingredient(s: str) -> str:
    s = re.sub(r"\[▼[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[►[^\]]*\]\([^)]*\)", "", s)
    s = strip_footnotes(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_skippable_line(line: str) -> bool:
    if not line.strip():
        return True
    if re.match(r"^\[▼[^\]]*\]\(https?://", line.strip()):
        return True
    if re.match(r"^\[►[^\]]*\]\(https?://", line.strip()):
        return True
    if line.strip().startswith("http"):
        return True
    return False


def looks_like_ref(line: str) -> bool | int:
    s = line.strip().rstrip(".")
    if not re.match(r"^\d+$", s):
        return False
    n = int(s)
    if 1 <= n <= 2100:
        return n
    return False


def classify_id_line(line: str) -> str | None:
    s = strip_footnotes(line.replace("—", "-")).strip()
    # Substance names often embed CAS numbers, e.g. "(CAS 71134-97-9)".
    if re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]{4,}", s):
        return None
    if s in {"-", "-/-", "- /-"}:
        return "empty_id"
    if re.match(r"^\d{3}-\d{3}-\d+(\/[^\s]*)?$", s):
        return "ec"
    if re.match(r"^\d+-\d{2}-\d(\/[\d\-]+)?$", s):
        return "cas"
    if re.match(r"^\d+-\d+-\d+(\/[\d\-]+)?$", s):
        if re.match(r"^\d{3}-\d{3}-\d+(\/[^\s]*)?$", s):
            return "ec"
        return "cas"
    if re.search(r"\d+-\d+-\d+", s):
        return "cas"
    return None


def extract_inci_variants(text: str) -> list[str]:
    out: list[str] = []
    for m in re.finditer(r"\[INCI:\s*([^\]]+)\]", text, flags=re.I):
        inner = clean_ingredient(m.group(1))
        if inner:
            out.append(inner)
    return out


def iter_substance_texts(name_blob: str) -> list[str]:
    parts: list[str] = []
    for piece in re.split(r"\s*;\s*\n?|\n+", name_blob):
        p = clean_ingredient(piece)
        if not p:
            continue
        parts.append(p)
        for inci in extract_inci_variants(piece):
            if inci.lower() not in {x.lower() for x in parts}:
                parts.append(inci)
    if not parts and name_blob.strip():
        parts.append(clean_ingredient(name_blob))
    return parts


def consume_cas_ec_block(lines: list[str], i: int, ref: int) -> int:
    """
    After substance name lines, advance i past one or more (CAS[, EC]) rows.
    Stops when the next line is another reference number (different from ref)
    or is clearly the start of the next substance name field.
    """
    while i < len(lines):
        while i < len(lines) and is_skippable_line(lines[i]):
            i += 1
        if i >= len(lines):
            break
        r = looks_like_ref(lines[i])
        if r is not False and r != ref:
            break
        if r == ref:
            i += 1
            continue
        cls = classify_id_line(lines[i])
        if cls is None:
            break
        i += 1  # CAS or empty CAS column
        if i < len(lines):
            r2 = looks_like_ref(lines[i])
            if r2 is not False and r2 != ref:
                break
            cls2 = classify_id_line(lines[i])
            if cls2 in {"cas", "ec", "empty_id"}:
                i += 1  # EC row
            elif cls2 is None:
                pass
    return i


def parse_annex_ii(lines: list[str]) -> list[dict]:
    try:
        ann2_i = next(
            i
            for i, L in enumerate(lines)
            if L.strip() == "ANNEX II"
            or "LIST OF SUBSTANCES PROHIBITED IN COSMETIC PRODUCTS" in L
        )
    except StopIteration:
        raise ValueError("Annex II header not found") from None

    try:
        ann3_i = next(
            i
            for i, L in enumerate(lines[ann2_i:], start=ann2_i)
            if L.strip() == "ANNEX III"
        )
    except StopIteration:
        ann3_i = len(lines)

    chunk = lines[ann2_i:ann3_i]

    start = 0
    for i, L in enumerate(chunk):
        if L.strip() == "1" and i + 1 < len(chunk):
            nxt = chunk[i + 1].strip()
            if nxt and not looks_like_ref(nxt) and not is_skippable_line(chunk[i + 1]):
                start = i
                break

    i = start
    rules: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add_rule(entry: str, ingredient: str) -> None:
        ing = clean_ingredient(ingredient)
        if not ing:
            return
        key = (entry, ing.lower())
        if key in seen:
            return
        seen.add(key)
        rules.append(
            {
                "ingredient": ing,
                "regulatory_reference": {"annex": "Annex II", "entry": entry},
            }
        )

    while i < len(chunk):
        while i < len(chunk) and is_skippable_line(chunk[i]):
            i += 1
        if i >= len(chunk):
            break
        rnum = looks_like_ref(chunk[i])
        if rnum is False:
            i += 1
            continue

        entry = str(rnum)
        i += 1

        while i < len(chunk):
            while i < len(chunk) and is_skippable_line(chunk[i]):
                i += 1
            if i >= len(chunk):
                break
            rnext = looks_like_ref(chunk[i])
            if rnext is not False and rnext != rnum:
                break
            if rnext == rnum:
                i += 1
                continue

            name_lines: list[str] = []
            while i < len(chunk):
                while i < len(chunk) and is_skippable_line(chunk[i]):
                    i += 1
                if i >= len(chunk):
                    break
                r2 = looks_like_ref(chunk[i])
                if r2 is not False:
                    break
                cls = classify_id_line(chunk[i])
                if cls in {"cas", "ec", "empty_id"}:
                    break
                name_lines.append(chunk[i].strip())
                i += 1

            if not name_lines:
                break

            name_blob = "\n".join(name_lines)
            for sub in iter_substance_texts(name_blob):
                add_rule(entry, sub)

            i = consume_cas_ec_block(chunk, i, rnum)

    return rules


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage: python parse_annex_ii_from_eurlex_txt.py <input.txt> <output.json>",
            file=sys.stderr,
        )
        sys.exit(1)
    inp, outp = sys.argv[1], sys.argv[2]
    with open(inp, encoding="utf-8") as f:
        lines = f.read().splitlines()

    rules = parse_annex_ii(lines)
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {len(rules)} rules to {outp}", file=sys.stderr)


if __name__ == "__main__":
    main()
