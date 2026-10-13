"""
Command Line Interface for Gwas Manhattan Pvalue Cleaner.
"""
import argparse
import csv
import json
import math
import os
import sys
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger

supervisor = SystemSupervisor(model_provider="mock")


def _validate_safe_path(path_str: str) -> str:
    """Reject relative paths escaping the working directory.

    An explicitly supplied absolute path is treated as a trusted local CLI
    choice; this is not a filesystem sandbox.
    """
    if not path_str or "\x00" in path_str:
        raise ValueError("Invalid file path")
    if not os.path.isabs(path_str):
        resolved = os.path.realpath(os.path.abspath(path_str))
        cwd = os.path.realpath(os.getcwd())
        if os.path.commonpath((cwd, resolved)) != cwd:
            raise ValueError(f"Relative input path escapes working directory: {path_str}")
    return path_str


def main(argv=None):
    parser = argparse.ArgumentParser(prog="gwas-manhattan-pvalue-cleaner", description="Gwas Manhattan Pvalue Cleaner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print(f"  GWAS MANHATTAN PVALUE CLEANER")
        print("  Legacy generic task evaluation (not GWAS statistical analysis)")
        print(f"  Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for a in dossier.alerts:
            print(f"\n  [{a.urgency.value}] from {a.origin_worker}:")
            print(f"  Summary: {a.summary}")
            print(f"  Details: {a.technical_details}")
            print(f"  Action:  {a.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Gwas Manhattan Pvalue Cleaner Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0

    if args.command == "batch":
        # Validate input file exists
        if not os.path.isfile(args.input):
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            return 1

        try:
            _validate_safe_path(args.input)
        except ValueError as e:
            print(f"Security error: {e}", file=sys.stderr)
            return 1

        try:
            with open(args.input, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    print("Error: CSV file is empty or has no headers", file=sys.stderr)
                    return 1
                fieldnames = list(reader.fieldnames)
                rows = list(reader)
        except csv.Error as e:
            print(f"Error reading CSV: {e}", file=sys.stderr)
            return 1
        except OSError as e:
            print(f"Error reading input file: {e}", file=sys.stderr)
            return 1

        out_fields = fieldnames + ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]
        if len(set(out_fields)) != len(out_fields):
            print("Error: Duplicate or reserved CSV headers", file=sys.stderr)
            return 1
        out_rows = []
        for line, r in enumerate(rows, start=2):
            try:
                if None in r:
                    raise ValueError("Unexpected extra CSV fields")
                primary = float(r.get("primary_metric") or 15.0)
                secondary = float(r.get("secondary_metric") or 5.0)
                if not math.isfinite(primary) or not math.isfinite(secondary):
                    raise ValueError("Metrics must be finite")
                payload = SystemTaskPayload(
                    task_id=r.get("task_id") or "TASK-01",
                    target_identifier=r.get("target_identifier") or "TARGET-01",
                    primary_metric=primary,
                    secondary_metric=secondary,
                    status_descriptor=r.get("status_descriptor") or "NOMINAL",
                    is_critical_flag=str(r.get("is_critical_flag", "")).lower() in ("true", "1", "yes"),
                )
                dossier = supervisor.process_task(payload)
            except (ValueError, TypeError) as exc:
                print(f"Error: CSV row {line}: {exc}", file=sys.stderr)
                return 1
            row_dict = dict(r)
            row_dict["overall_urgency"] = dossier.overall_urgency.value
            row_dict["integrity_status"] = dossier.integrity_status.value
            row_dict["total_alerts"] = dossier.total_alerts
            row_dict["audit_hash"] = dossier.audit_hash
            out_rows.append(row_dict)

        try:
            with open(args.output, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=out_fields)
                writer.writeheader()
                writer.writerows(out_rows)
        except OSError as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
        print(f"Processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        import uvicorn
        from agents.api import app
        print(f"Starting Gwas Manhattan Pvalue Cleaner API server on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
