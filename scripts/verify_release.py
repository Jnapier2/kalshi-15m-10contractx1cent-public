"""Compatibility entrypoint for the single canonical package verifier."""
import runpy
from pathlib import Path
root = Path(__file__).resolve().parents[1]
entry = runpy.run_path(str(root / "run_buy_planner.py"))
result = entry["verify_release"]()
print(result)
raise SystemExit(0 if result["status"] == "PASS" else 2)
