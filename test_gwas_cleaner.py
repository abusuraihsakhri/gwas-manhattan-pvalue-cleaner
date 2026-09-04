import pytest
from gwas_cleaner import calculate_metrics, process_batch, main


def test_gwas_cleaner_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_gwas_cleaner_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


def test_gwas_cleaner_batch_missing_file():
    """process_batch should raise FileNotFoundError for missing input."""
    with pytest.raises(FileNotFoundError):
        process_batch("nonexistent_file.csv", "output.csv")


def test_gwas_cleaner_batch_empty_csv(tmp_path):
    """process_batch should raise ValueError for empty CSV."""
    csv_in = tmp_path / "empty.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="empty or has no headers"):
        process_batch(str(csv_in), str(csv_out))


def test_gwas_cleaner_cli_single():
    """CLI single command should work with defaults."""
    assert main(["single"]) == 0


def test_gwas_cleaner_cli_batch_error():
    """CLI batch command should return error code for missing file."""
    assert main(["batch", "-i", "nonexistent.csv"]) == 1
