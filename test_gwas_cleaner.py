import csv
import math
import pytest

from gwas_cleaner import (
    calculate_metrics, clean_row, column_mapping, genomic_inflation,
    main, process_batch,
)


def test_lambda_gc_null_median_is_one():
    assert genomic_inflation([0.5] * 10) == pytest.approx(1, rel=1e-6)


def test_lambda_gc_strong_signal_and_precision():
    assert genomic_inflation([1e-100]) > 400
    assert math.isfinite(genomic_inflation([1e-300]))
    assert calculate_metrics(p_values=[1e-9, 0.5])["genome_wide_significant"] == 1


@pytest.mark.parametrize("bad", [0, -1, 1.1, float("nan"), float("inf"), -float("inf")])
def test_invalid_pvalues_rejected(bad):
    with pytest.raises(ValueError, match="p-values"):
        genomic_inflation([bad])


def test_column_aliases_and_chromosome_normalization():
    m = column_mapping(["chromosome", "position", "p_value"])
    assert clean_row({"chromosome": "chrX", "position": "123", "p_value": "0.01"}, m)["CHR"] == 23
    assert clean_row({"chromosome": "MT", "position": "1", "p_value": "1"}, m)["CHR"] == 25


@pytest.mark.parametrize("chrom,bp,p", [
    ("0", "12", "0.01"), ("23", "12", "0.01"), ("chr2", "-1", "0.01"),
    ("1", "1.2", "0.01"), ("1", "0", "0.01"), ("1", "12", "0"),
    ("1", "12", "1e-999"), ("1", "12", "nan"), ("1", "12", "2")
])
def test_bad_gwas_records(chrom, bp, p):
    with pytest.raises(ValueError):
        clean_row({"CHR": chrom, "BP": bp, "P": p}, column_mapping(["CHR", "BP", "P"]))


def test_batch_rejects_invalid_rows_and_blocks_csv_formula(tmp_path):
    source = tmp_path / "raw.csv"
    target = tmp_path / "clean.csv"
    source.write_text(
        'CHR,BP,P,SNP\n1,123,0.5,"=1+1"\nX,456,1e-9,rs1\n1,0,0.3,invalid\n2,234,0,underflow\n',
        encoding="utf-8",
    )
    result = process_batch(str(source), str(target))
    assert result["n_valid"] == 2
    assert result["n_rejected"] == 2
    assert result["genome_wide_significant"] == 1
    with target.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert rows[0]["SNP"] == "'=1+1"
    assert rows[0]["BETA"] == "-0.5"
    assert rows[1]["GWAS_CHR"] == "23"
    assert float(rows[1]["NEG_LOG10_P"]) == pytest.approx(9)


def test_batch_missing_file():
    with pytest.raises(FileNotFoundError):
        process_batch("nonexistent_file.csv", "output.csv")


def test_empty_or_invalid_batch_preserves_existing_output(tmp_path):
    source = tmp_path / "raw.csv"
    target = tmp_path / "clean.csv"
    target.write_text("original", encoding="utf-8")
    source.write_text("CHR,BP,P\n1,10,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="No valid"):
        process_batch(str(source), str(target))
    assert target.read_text(encoding="utf-8") == "original"
    source.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        process_batch(str(source), str(target))


def test_duplicate_or_missing_columns():
    with pytest.raises(ValueError, match="Duplicate"):
        column_mapping(["CHR", "chr", "BP", "P"])
    with pytest.raises(ValueError, match="exactly one P"):
        column_mapping(["CHR", "BP"])


def test_cli():
    assert main(["single", "--p", "0.5"]) == 0
    assert main(["batch", "-i", "nonexistent.csv"]) == 1
    assert main(["single", "--p", "0"]) == 1
