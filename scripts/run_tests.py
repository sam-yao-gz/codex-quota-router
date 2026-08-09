#!/usr/bin/env python3
"""Run dependency-free test_* functions without pytest."""
from __future__ import annotations
import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
failures = []; count = 0
for path in sorted((root / "tests").glob("test_*.py")):
    spec = importlib.util.spec_from_file_location(path.stem, path); module = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module)
    for name, fn in sorted(vars(module).items()):
        if name.startswith("test_") and callable(fn) and fn.__code__.co_argcount == 0:
            count += 1
            try: fn()
            except Exception as exc: failures.append(f"{path.name}::{name}: {exc}")
if failures:
    print("TESTS FAILED"); print("\n".join(failures)); raise SystemExit(1)
print(f"TESTS PASSED: {count}")
