# GWAS Manhattan & P-value Cleaner

Validate genome-wide association summary statistics, inspect Manhattan and QQ plots, and export cleaned data. The browser application runs locally without a backend; the Python CLI provides equivalent data validation and descriptive genomic inflation statistics.

## Features

- CSV import with chromosome (CHR, CHROM, CHROMOSOME), base-pair (BP, POS, POSITION, BASE_PAIR) and p-value (P, PVAL, PVALUE, P_VALUE, P-VALUE) column aliases.
- Supports chromosomes **1–22, X, Y and MT**; requires positive integer positions and finite p-values in **(0, 1]**.
- Rejects invalid entries including zero/underflowed p-values; never invents replacement values.
- Displays Manhattan and QQ plots with the conventional human-GWAS reference threshold of **p < 5 × 10⁻⁸**.
- Reports valid/rejected marker counts and genomic inflation **λGC = median(χ² with 1 df) / 0.4549364231**.
- Exports valid records with canonical coordinates, p-values and -log10(p); text that could trigger spreadsheet formulas is escaped.

**Interpretation:** λGC is an unadjusted descriptive statistic; it does not distinguish population stratification, relatedness, residual confounding or polygenicity. The QQ plot assumes a uniform-null reference and does not include an LD-aware confidence envelope. The genome-wide threshold is a conventional reference, not universally appropriate. This tool is not a complete GWAS QC pipeline.

## Use in your browser

Open [web/index.html](web/index.html) in a recent browser. Upload a CSV or select **Try sample data**. Review the statistics and plots, then select **Download cleaned CSV**.

Processing is local; files are not uploaded. In-browser limits are **15 MB** and **200,000 data rows**. Plots downsample when needed for responsiveness; exports retain **all valid rows**. Larger datasets can be processed with the Python CLI.

The repository includes a GitHub Pages workflow for the static application. The site becomes accessible once Pages is enabled with **GitHub Actions** as its source and deployment succeeds.

## Python CLI

Python **3.10+**; the core cleaner uses only the standard library.

~~~bash
python gwas_cleaner.py batch --input sample.csv --output cleaned_gwas.csv
python gwas_cleaner.py single --p 0.5 --p 1e-9
~~~

Batch input can include additional variant metadata such as SNP IDs. The cleaner preserves original columns and appends GWAS_CHR, GWAS_BP, GWAS_P and NEG_LOG10_P. Invalid rows are omitted and counted in the JSON summary. If no row is valid, the output file is not replaced.

## Optional legacy API and agent modules

The existing agents/, cli.py, enrichment.py and simulator.py interfaces remain for compatibility. They implement *generic task evaluation*, not GWAS statistical analysis. Their metric thresholds and mock-chat responses should not be interpreted as validated clinical or statistical inference.

To run the optional REST API:

~~~bash
python -m pip install -r requirements.txt
python cli.py serve --host 127.0.0.1 --port 8000
~~~

The API exposes /health, /metrics, /api/audit, /api/chat and /api/audit/logs; it does **not** power the browser GWAS workflow. If deploying with Docker Compose, supply a private AUDIT_SECRET_KEY environment variable. The legacy PHI regex guard is not sufficient to establish HIPAA compliance or reliably de-identify arbitrary health records. Do not send patient-identifiable material.

## Tests

~~~bash
python -m pip install -r requirements.txt pytest
python -m pytest -q
node tests/browser_smoke.cjs
~~~

GitHub Actions tests Python 3.10–3.12 and runs a Node-based browser logic smoke test.

## Technology and license

Python standard library, optional FastAPI/Pydantic service, and dependency-free HTML/CSS/JavaScript with Canvas plots. Designed for recent Chrome, Firefox, Safari and Edge; real-device/browser validation is separate from automated JavaScript smoke tests.

MIT license — see [LICENSE](LICENSE).
