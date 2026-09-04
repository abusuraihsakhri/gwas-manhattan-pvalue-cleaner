# Gwas Manhattan Pvalue Cleaner

> **Domain:** Privacy-Preserving Healthcare & Federated Computing
> **Reference Guidelines & Standards:** `HIPAA Safe Harbor §164.514 & Differential Privacy RDP`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

GWAS Summary Statistics Cleaner & Genomic Inflation (Lambda GC) tool.
Calculates genomic inflation factor (Lambda GC) and cleans summary stats for Manhattan/QQ plots.

Multi-agent enterprise system with worker-based evaluation, PHI outbound protection,
and tamper-evident audit logging. Includes a FastAPI REST server, CLI interface,
and batch processing capabilities.

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_metrics()`**: Core domain algorithm — computes weighted scores and classifies severity tiers.
- **`process_single()`** — evaluates a single set of parameters and prints JSON results.
- **`process_batch()`** — processes CSV input files and appends classification columns.
- **`main()`** — CLI entry point with subcommands for single and batch evaluation.

### 🤖 Multi-Agent System (agents/ module)

- **SystemSupervisor** — orchestrates multi-worker task evaluation.
- **InvariantQCWorker** — primary metric threshold boundary auditor.
- **SafetyEscalationWorker** — safety interlock and escalation trigger.
- **ProtocolConformanceWorker** — spec conformance and anomaly detection.
- **PHIGuard** — Zero-PHI outbound interceptor blocking SSNs, MRNs, emails, etc.
- **AuditTrail** — tamper-evident HMAC-SHA256 chained audit logging.
- **ActiveLearningEngine** — Bayesian calibration feedback for worker reliability.

---

## 💻 Installation

```bash
pip install fastapi uvicorn pydantic pytest
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Evaluation Mode
```bash
python gwas_cleaner.py single --v1 12.0 --v2 4.0 --v3 2.0
```

### 2. Batch CSV Processing
```bash
python gwas_cleaner.py batch -i sample.csv -o results.csv
```

### 3. Enterprise CLI (agents-based)
```bash
# Single audit task
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2

# Batch processing
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail integrity
python cli.py verify-audit

# Launch FastAPI REST server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Input Data Schema (Batch CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Task / case identifier | Required |
| `target_identifier` | Entity or target key | Required |
| `primary_metric` | Primary measurement or score | Required |
| `secondary_metric` | Secondary confidence score | Optional (default 5.0) |
| `status_descriptor` | Status code or phenotype | Optional (default NOMINAL) |
| `is_critical_flag` | Emergency escalation flag | Optional (default False) |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** AST and regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation. Requires `AUDIT_SECRET_KEY` environment variable for persistent integrity across restarts.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI REST endpoints and operational Prometheus metrics (`/metrics`).
* **Multi-Agent Consensus:** Worker-based evaluation with severity classification (ROUTINE, ELEVATED, CRITICAL_STAT).

### Environment Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `AUDIT_SECRET_KEY` | Secret key for HMAC-SHA256 audit signing | Random per-session (ephemeral) |
| `MODEL_PROVIDER` | LLM provider for chat (mock, ollama, claude, openai) | mock |

> **Security Note:** Set `AUDIT_SECRET_KEY` in production to ensure audit trail integrity persists across process restarts. Without it, a random ephemeral key is generated per session.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t gwas-manhattan-pvalue-cleaner .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key gwas-manhattan-pvalue-cleaner
```

Or using Docker Compose:

```bash
docker-compose up --build
```

---

## 📁 Project Structure

```
gwas-manhattan-pvalue-cleaner/
├── agents/                   # Enterprise multi-agent system
│   ├── api.py               # FastAPI REST endpoints
│   ├── base.py              # Security, PHI guard, audit trail
│   ├── learning.py          # Bayesian calibration engine
│   ├── llm_factory.py       # LLM provider abstraction
│   ├── metrics.py           # Prometheus metrics exporter
│   ├── models.py            # Pydantic data models
│   ├── streamer.py          # WebSocket telemetry broadcaster
│   ├── supervisor.py        # Master orchestrator
│   └── workers.py           # Domain-specific worker agents
├── tests/                   # Pytest test suite
├── cli.py                   # Enterprise CLI entry point
├── gwas_cleaner.py          # Core GWAS cleaner CLI
├── enrichment.py            # Enrichment feature engines
├── simulator.py             # High-throughput stress simulator
├── Dockerfile               # Container build spec
├── docker-compose.yml       # Multi-service orchestration
└── sample.csv               # Example input data
```
