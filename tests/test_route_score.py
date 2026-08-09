from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "route_score.py"
spec = importlib.util.spec_from_file_location("route_score", MODULE_PATH)
module = importlib.util.module_from_spec(spec); assert spec and spec.loader
sys.modules[spec.name] = module; spec.loader.exec_module(module)


def route(values, flags=()): return module.choose_route(*values, set(flags)).agent
def route_cli(*args):
    runtime = tempfile.mkdtemp()
    result = subprocess.run([sys.executable, str(MODULE_PATH), "--runtime-dir", runtime, *args], capture_output=True, text=True, check=True)
    return json.loads(result.stdout), runtime


def test_mechanical(): assert route((0, 0, 0, 0, 0, 0)) == "luna_fast"
def test_default_feature(): assert route((0, 1, 1, 1, 0, 0)) == "luna_worker"
def test_bounded_multifile(): assert route((1, 2, 2, 2, 1, 0)) == "luna_deep"
def test_idempotency_gate(): assert route((1, 1, 2, 2, 1, 0), {"idempotency"}) == "terra_resolver"
def test_migration_gate(): assert route((0, 1, 1, 2, 0, 0), {"migration"}) == "terra_guard"
def test_architecture_gate(): assert route((2, 3, 3, 3, 2, 0), {"architecture"}) == "sol_architect"


def test_luna_fallback_is_terra_medium():
    fallback = module.apply_luna_availability_fallback(module.choose_route(0, 0, 0, 0, 0, 0, set()))
    assert (fallback.agent, fallback.model, fallback.effort) == ("terra_resolver", "gpt-5.6-terra", "medium")


def test_parent_same_model_equal_or_higher_effort_reuses_parent():
    target = module.choose_route(1, 2, 2, 2, 1, 0, set())
    assert module.parent_compatibility("gpt-5.6-luna", "high", target)["parent_reused"]
    assert not module.parent_compatibility("gpt-5.6-luna", "medium", target)["parent_reused"]


def test_parent_cross_model_never_reuses_parent():
    target = module.choose_route(0, 0, 0, 0, 0, 0, set())
    assert not module.parent_compatibility("gpt-5.6-terra", "high", target)["parent_reused"]


def test_active_open_uses_fallback_with_coherent_action():
    _, runtime = route_cli("--clarity", "1", "--scope", "2", "--coupling", "2", "--risk", "2", "--novelty", "1")
    availability = MODULE_PATH.parent / "model_availability.py"
    subprocess.run([sys.executable, str(availability), "--runtime-dir", runtime, "--now", "100", "unavailable", "--error", "Luna model unavailable"], check=True, capture_output=True, text=True)
    result = subprocess.run([sys.executable, str(MODULE_PATH), "--runtime-dir", runtime, "--now", "101", "--clarity", "1", "--scope", "2", "--coupling", "2", "--risk", "2", "--novelty", "1"], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    assert data["dispatch_action"] == "use_fallback" and data["requested_model"] == "gpt-5.6-terra"


def test_open_after_cooldown_probes_luna_without_terra_contradiction():
    _, runtime = route_cli("--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")
    availability = MODULE_PATH.parent / "model_availability.py"
    subprocess.run([sys.executable, str(availability), "--runtime-dir", runtime, "--now", "100", "unavailable", "--error", "Luna model unavailable"], check=True, capture_output=True, text=True)
    result = subprocess.run([sys.executable, str(MODULE_PATH), "--runtime-dir", runtime, "--now", "1900", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0"], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    assert data["dispatch_action"] == "probe_luna" and data["requested_model"] == "gpt-5.6-luna"


def test_existing_probe_requires_inspection_not_terra_fallback():
    _, runtime = route_cli("--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")
    availability = MODULE_PATH.parent / "model_availability.py"
    subprocess.run([sys.executable, str(availability), "--runtime-dir", runtime, "--now", "100", "unavailable", "--error", "Luna model unavailable"], check=True, capture_output=True, text=True)
    subprocess.run([sys.executable, str(availability), "--runtime-dir", runtime, "--now", "1900", "start-probe"], check=True, capture_output=True, text=True)
    result = subprocess.run([sys.executable, str(MODULE_PATH), "--runtime-dir", runtime, "--now", "1901", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0"], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    assert data["dispatch_action"] == "inspect_existing_probe" and data["requested_model"] == "gpt-5.6-luna"


def test_disable_luna_routes_normal_task_to_terra_without_availability_read():
    runtime = Path(tempfile.mkdtemp())
    state = {"schema_version": 2, "luna": {"circuit_state": "open", "status": "unavailable", "failure_count": 7, "last_error": "prior", "unavailable_until": 9999, "probe_started_at": None}}
    state_path = runtime / "model_availability.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    before = state_path.read_bytes()
    result = subprocess.run([sys.executable, str(MODULE_PATH), "--runtime-dir", str(runtime), "--disable-luna", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0"], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    assert data["requested_model"] == "gpt-5.6-terra" and data["requested_effort"] == "medium"
    assert data["dispatch_action"] == "user_override"
    assert data["user_override"] == "disable_luna" and data["availability_state_unchanged"] is True
    assert data["probe_count"] == 0 and data["fallback_count"] == 0 and state_path.read_bytes() == before


def test_disable_luna_natural_language_input_and_conflict():
    result, _ = route_cli("--user-input", "$codex-quota-router 禁用 Luna：普通任务", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")
    assert result["user_override"] == "disable_luna" and result["requested_model"] == "gpt-5.6-terra"
    conflict = subprocess.run([sys.executable, str(MODULE_PATH), "--user-input", "这次禁用 Luna; Use Luna only", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0"], capture_output=True, text=True)
    assert conflict.returncode != 0 and "conflicting user policies" in conflict.stderr


def test_use_luna_only_never_silently_falls_back():
    result, _ = route_cli("--flag", "use_luna_only", "--luna-unavailable", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")
    assert result["requested_model"] == "gpt-5.6-luna" and result["dispatch_action"] == "blocked_user_policy"


def test_disable_luna_preserves_terra_high_and_sol_architecture_gates():
    high, _ = route_cli("--disable-luna", "--flag", "security", "--clarity", "0", "--scope", "1", "--coupling", "1", "--risk", "3", "--novelty", "0")
    assert high["requested_model"] == "gpt-5.6-terra" and high["requested_effort"] == "high"
    architecture, _ = route_cli("--disable-luna", "--flag", "architecture", "--clarity", "2", "--scope", "3", "--coupling", "3", "--risk", "3", "--novelty", "2")
    assert architecture["requested_model"] == "gpt-5.6-sol" and architecture["requested_effort"] == "medium"
