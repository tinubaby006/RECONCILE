import io
import json
import tempfile
import os
import sys
from unittest.mock import patch
from reconcile.cli import main


def test_cli_ipc_inspect():
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write("id,name,amount\n1,Alice,100\n")
        temp_path = f.name

    try:
        request = {
            "command": "inspect",
            "params": {"file_path": temp_path}
        }
        stdin_stream = io.StringIO(json.dumps(request))
        stdout_stream = io.StringIO()

        with patch.object(sys, "stdin", stdin_stream), patch.object(sys, "stdout", stdout_stream):
            main(argv=["ipc"])

        output = stdout_stream.getvalue().strip()
        result = json.loads(output)
        assert result["type"] == "result"
        assert result["success"] is True
        assert result["data"]["total_rows"] == 1
        assert len(result["data"]["columns"]) == 3
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_cli_ipc_reconcile():
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f_a:
        f_a.write("id,amount\nA1,500\n")
        path_a = f_a.name

    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f_b:
        f_b.write("ref,amount\nA1,500\n")
        path_b = f_b.name

    try:
        request = {
            "command": "reconcile",
            "params": {
                "file_a": path_a,
                "file_b": path_b,
                "mappings": [
                    {"col_a": "id", "col_b": "ref", "role": "match_key"},
                    {"col_a": "amount", "col_b": "amount", "role": "amount"},
                ]
            }
        }
        stdin_stream = io.StringIO(json.dumps(request))
        stdout_stream = io.StringIO()

        with patch.object(sys, "stdin", stdin_stream), patch.object(sys, "stdout", stdout_stream):
            main(argv=["ipc"])

        lines = [line.strip() for line in stdout_stream.getvalue().strip().split("\n") if line.strip()]
        # Progress lines
        progress_lines = [json.loads(l) for l in lines if '"progress"' in l]
        assert len(progress_lines) > 0

        # Result line
        result_lines = [json.loads(l) for l in lines if '"result"' in l]
        assert len(result_lines) == 1
        assert result_lines[0]["success"] is True
        summary = result_lines[0]["data"]["summary"]
        assert summary["matched_count"] == 1
    finally:
        if os.path.exists(path_a):
            os.remove(path_a)
        if os.path.exists(path_b):
            os.remove(path_b)
