#!/usr/bin/env python3
"""Validate GWAS summary statistics and prepare Manhattan/QQ plot data.

Uses only the Python standard library. Zero p-values are rejected rather than
silently replaced with an arbitrary floor. Lambda GC is descriptive and is not
adjusted for polygenicity, LD or ancestry.
"""
import argparse
import csv
import json
import math
import os
import statistics
import sys
import tempfile
from statistics import NormalDist

ALIASES = {
    "CHR": ("CHR", "CHROM", "CHROMOSOME"),
    "BP": ("BP", "POS", "POSITION", "BASE_PAIR"),
    "P": ("P", "PVAL", "PVALUE", "P_VALUE", "P-VALUE"),
}
CHI_SQUARE_MEDIAN_DF1 = 0.454936423119572
NORMAL = NormalDist()


def column_mapping(fieldnames):
    """Find required columns case-insensitively; ambiguous duplicate names fail."""
    names = {}
    for name in fieldnames:
        if name is None:
            raise ValueError("CSV contains a missing column name")
        key = name.strip().upper()
        if key in names:
            raise ValueError(f"Duplicate CSV column: {name}")
        names[key] = name
    mapping = {}
    for standard, alternatives in ALIASES.items():
        found = [names[a] for a in alternatives if a in names]
        if len(found) != 1:
            raise ValueError(f"Expected exactly one {standard} column (aliases: {', '.join(alternatives)})")
        mapping[standard] = found[0]
    return mapping


def normalize_chromosome(raw):
    value = str(raw).strip().upper()
    if value.startswith("CHR"):
        value = value[3:]
    specials = {"X": 23, "Y": 24, "M": 25, "MT": 25}
    if value in specials:
        return specials[value]
    if value.isdigit() and 1 <= int(value) <= 22:
        return int(value)
    raise ValueError("Chromosome must be 1-22, X, Y or MT")


def clean_row(row, mapping):
    """Return a cleaned canonical record; reject invalid or underflowed p-values."""
    chromosome = normalize_chromosome(row[mapping["CHR"]])
    bp_raw = str(row[mapping["BP"]]).strip()
    if not bp_raw.isdigit() or int(bp_raw) < 1:
        raise ValueError("BP must be a positive integer")
    bp = int(bp_raw)
    p = float(str(row[mapping["P"]]).strip())
    if not math.isfinite(p) or p <= 0.0 or p > 1.0:
        raise ValueError("P must be finite and in (0, 1]; zero/underflow is invalid")
    return {"CHR": chromosome, "BP": bp, "P": p, "NEG_LOG10_P": -math.log10(p)}


def genomic_inflation(p_values):
    """Median one-degree-of-freedom chi-square divided by the null median.

    NormalDist.inv_cdf(p/2) avoids 1-p catastrophic cancellation for tiny p.
    """
    values = list(p_values)
    if not values:
        raise ValueError("At least one valid p-value is required")
    if any(not isinstance(p, (int, float)) or not math.isfinite(p) or p <= 0 or p > 1 for p in values):
        raise ValueError("All p-values must be finite and in (0, 1]")
    chi2 = [NORMAL.inv_cdf(p / 2.0) ** 2 for p in values]
    return statistics.median(chi2) / CHI_SQUARE_MEDIAN_DF1


def calculate_metrics(*, p_values):
    """Summarize an iterable of valid GWAS p-values (not a clinical score)."""
    ps = list(p_values)
    inflation = genomic_inflation(ps)
    return {
        "tool": "gwas-manhattan-pvalue-cleaner",
        "n_valid": len(ps),
        "lambda_gc": inflation,
        "min_p": min(ps),
        "genome_wide_significant": sum(p < 5e-8 for p in ps),
        "note": "Lambda GC is descriptive; interpretation requires GWAS design and LD context.",
    }


def _safe_spreadsheet_value(value):
    """Escape spreadsheet formulas while retaining signed numeric GWAS effects."""
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if stripped.startswith(("=", "+", "-", "@")):
        try:
            if math.isfinite(float(stripped)):
                return value
        except ValueError:
            pass
        return "'" + value
    return value


def process_batch(input_csv, output_csv):
    """Write valid rows to CSV, retaining source columns and appending canonical data.

    Invalid rows are counted, not silently coerced. Atomic replacement avoids
    leaving a partially written output on failure.
    """
    if not os.path.isfile(input_csv):
        raise FileNotFoundError(f"Input file not found: {input_csv}")
    values = []
    rejected = 0
    written = 0
    temp_path = None
    try:
        with open(input_csv, newline="", encoding="utf-8-sig") as source:
            reader = csv.DictReader(source)
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or has no headers")
            mapping = column_mapping(reader.fieldnames)
            columns = list(reader.fieldnames)
            if any(name in columns for name in ("GWAS_CHR", "GWAS_BP", "GWAS_P", "NEG_LOG10_P")):
                raise ValueError("Output columns already exist in the input")
            destination = os.path.abspath(output_csv)
            with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8",
                                             dir=os.path.dirname(destination), delete=False) as output:
                temp_path = output.name
                writer = csv.DictWriter(output, fieldnames=columns + ["GWAS_CHR", "GWAS_BP", "GWAS_P", "NEG_LOG10_P"])
                writer.writeheader()
                for record in reader:
                    try:
                        if None in record:
                            raise ValueError("Extra CSV fields")
                        cleaned = clean_row(record, mapping)
                    except (ValueError, TypeError, KeyError, OverflowError):
                        rejected += 1
                        continue
                    safe_record = {key: _safe_spreadsheet_value(value) for key, value in record.items()}
                    safe_record.update({
                        "GWAS_CHR": cleaned["CHR"], "GWAS_BP": cleaned["BP"],
                        "GWAS_P": cleaned["P"], "NEG_LOG10_P": cleaned["NEG_LOG10_P"],
                    })
                    writer.writerow(safe_record)
                    values.append(cleaned["P"])
                    written += 1
        if not written:
            raise ValueError("No valid GWAS records found; output was not replaced")
        os.replace(temp_path, output_csv)
        temp_path = None
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
    result = calculate_metrics(p_values=values)
    result["n_rejected"] = rejected
    result["output"] = output_csv
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="GWAS p-value validation and Manhattan/QQ CSV preparation")
    sub = parser.add_subparsers(dest="command", required=True)
    single = sub.add_parser("single", help="Calculate lambda GC for supplied p-values")
    single.add_argument("--p", type=float, required=True, action="append", help="P-value; repeat for each marker")
    batch = sub.add_parser("batch", help="Clean GWAS summary statistics CSV")
    batch.add_argument("-i", "--input", required=True, help="Input CSV with CHR,BP,P columns")
    batch.add_argument("-o", "--output", default="cleaned_gwas.csv")
    args = parser.parse_args(argv)
    try:
        result = (calculate_metrics(p_values=args.p) if args.command == "single"
                  else process_batch(args.input, args.output))
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, csv.Error, OverflowError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
