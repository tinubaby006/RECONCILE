from __future__ import annotations

import argparse
import json
import sys
import warnings
from typing import Any

warnings.filterwarnings("ignore")

from reconcile.loaders import inspect_dataset, load_dataset
from reconcile.mapping.column_mapper import ColumnMapper
from reconcile.matching.reconciler import Reconciler
from reconcile.models import ColumnMapping


def emit_progress(percent: int, message: str) -> None:
    """Emits an unbuffered progress line to stdout formatted as NDJSON."""
    payload = {"type": "progress", "percent": percent, "message": message}
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def emit_result(data: Any, success: bool = True, error: str = "") -> None:
    """Emits the final result line to stdout formatted as JSON."""
    payload = {"type": "result", "success": success, "data": data, "error": error}
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def handle_inspect(params: dict[str, Any]) -> None:
    file_path = params.get("file_path")
    sheet_name = params.get("sheet_name")

    if not file_path:
        emit_result(None, success=False, error="Missing required parameter: file_path")
        return

    try:
        meta = inspect_dataset(file_path, sheet_name=sheet_name)
        emit_result(meta.to_dict())
    except Exception as e:
        emit_result(None, success=False, error=str(e))


def handle_map_columns(params: dict[str, Any]) -> None:
    file_a = params.get("file_a")
    file_b = params.get("file_b")
    sheet_a = params.get("sheet_a")
    sheet_b = params.get("sheet_b")

    if not file_a or not file_b:
        emit_result(None, success=False, error="Missing required parameters: file_a and file_b")
        return

    try:
        emit_progress(10, "Inspecting Dataset A...")
        meta_a = inspect_dataset(file_a, sheet_name=sheet_a)
        emit_progress(40, "Inspecting Dataset B...")
        meta_b = inspect_dataset(file_b, sheet_name=sheet_b)

        emit_progress(70, "Computing column similarities and roles...")
        mappings = ColumnMapper.suggest_mappings(meta_a, meta_b)
        emit_progress(100, "Mapping complete.")

        emit_result({
            "meta_a": meta_a.to_dict(),
            "meta_b": meta_b.to_dict(),
            "mappings": [m.to_dict() for m in mappings],
        })
    except Exception as e:
        emit_result(None, success=False, error=str(e))


def handle_reconcile(params: dict[str, Any]) -> None:
    file_a = params.get("file_a")
    file_b = params.get("file_b")
    sheet_a = params.get("sheet_a")
    sheet_b = params.get("sheet_b")
    raw_mappings = params.get("mappings", [])
    user_overrides = params.get("overrides", {})
    rules = params.get("rules", {})

    if not file_a or not file_b:
        emit_result(None, success=False, error="Missing required parameters: file_a and file_b")
        return

    try:
        emit_progress(5, "Loading datasets...")
        meta_a, df_a = load_dataset(file_a, sheet_name=sheet_a)
        meta_b, df_b = load_dataset(file_b, sheet_name=sheet_b)

        mappings = [
            ColumnMapping(
                col_a=m["col_a"],
                col_b=m.get("col_b"),
                role=m.get("role", "compare"),
                confidence=m.get("confidence", 1.0),
                status=m.get("status", "mapped"),
            )
            for m in raw_mappings
        ]

        amt_tol = float(rules.get("amount_tolerance", 0.01))
        dt_tol = int(rules.get("date_tolerance_days", 7))
        ent_sim = float(rules.get("entity_similarity_threshold", 70.0))

        reconciler = Reconciler(
            amount_tolerance=amt_tol,
            date_tolerance_days=dt_tol,
            entity_similarity_threshold=ent_sim,
        )

        summary, records, grouped = reconciler.reconcile(
            df_a=df_a,
            df_b=df_b,
            mappings=mappings,
            user_overrides=user_overrides,
            progress_callback=emit_progress,
        )

        emit_result({
            "summary": summary.to_dict(),
            "records": [r.to_dict() for r in records],
            "entities": {ent: [r.to_dict() for r in recs] for ent, recs in grouped.items()},
        })
    except Exception as e:
        emit_result(None, success=False, error=str(e))


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="RECONCILE Core Engine CLI")
    subparsers = parser.add_subparsers(dest="command")

    # IPC Mode (reads JSON from stdin)
    subparsers.add_parser("ipc", help="Run in JSON IPC mode via stdin/stdout")

    # Direct CLI helpers
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a dataset file")
    inspect_parser.add_argument("--file", required=True, help="Path to data file")
    inspect_parser.add_argument("--sheet", help="Optional sheet name for Excel")

    args = parser.parse_args(argv)

    if args.command == "ipc" or args.command is None:
        try:
            raw_input = sys.stdin.read().strip()
            if not raw_input:
                emit_result(None, success=False, error="Empty input received on stdin")
                return
            request = json.loads(raw_input)
            cmd = request.get("command")
            params = request.get("params", {})

            if cmd == "inspect":
                handle_inspect(params)
            elif cmd == "map_columns":
                handle_map_columns(params)
            elif cmd == "reconcile":
                handle_reconcile(params)
            else:
                emit_result(None, success=False, error=f"Unknown command: {cmd}")
        except Exception as e:
            emit_result(None, success=False, error=f"IPC error: {str(e)}")

    elif args.command == "inspect":
        handle_inspect({"file_path": args.file, "sheet_name": args.sheet})


if __name__ == "__main__":
    main()
