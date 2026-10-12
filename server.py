"""FixPilot Web Dashboard Server — high-performance Flask app with zero C-compilation dependencies."""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from flask import Flask, render_template, request, jsonify
from src.agents.crew import FixPilotCrew
from src.triggers.presets import list_preset_scenarios, get_preset_scenario
from src.config import settings

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
crew = FixPilotCrew()


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


import json
from pathlib import Path

_CACHE_FILE = Path("last_remediation.json")

def _load_cached_result():
    if _CACHE_FILE.exists():
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

_last_remediation_result = _load_cached_result()


@app.route("/")
def index():
    """Renders the main FixPilot dashboard."""
    scenarios = [s.model_dump() for s in list_preset_scenarios()]
    status = {
        "litellm_configured": bool(settings.litellm.api_key and settings.litellm.api_key != "your_litellm_api_key_here"),
        "neatlogs_configured": bool(settings.neatlogs.api_key and settings.neatlogs.api_key != "your_neatlogs_api_key_here"),
        "guardrail_engine": crew.guardrail.engine_mode,
        "entire_checkpoints": True,
        "neatlogs_project_id": settings.neatlogs.project_id,
        "neatlogs_org_id": settings.neatlogs.org_id,
        "neatlogs_url": f"https://app.neatlogs.com/traces?orgId={settings.neatlogs.org_id}&projectId={settings.neatlogs.project_id}",
    }
    return render_template("index.html", scenarios=scenarios, status=status, initial_result=_last_remediation_result)


@app.route("/api/preview-sanitize", methods=["POST"])
def preview_sanitize():
    """Returns local sanitization preview showing redacted secrets."""
    data = request.json or {}
    raw_logs = data.get("raw_logs", "")
    mask_result = crew.guardrail.sanitize_log(raw_logs)

    findings = [
        {"type": f.finding_type, "value": f.value[:8] + "...", "confidence": f.confidence}
        for f in mask_result.findings
    ]

    return jsonify({
        "sanitized_text": mask_result.sanitized_text,
        "redactions_count": mask_result.redactions_count,
        "findings": findings,
        "engine_mode": crew.guardrail.engine_mode,
    })


@app.route("/api/run-remediation", methods=["POST"])
def run_remediation():
    """Executes the full FixPilot autonomous multi-agent remediation loop."""
    data = request.json or {}
    incident_title = data.get("incident_title", "CI Failure: Production Remediation")
    raw_logs = data.get("raw_logs", "")
    force_self_healing = data.get("force_self_healing", True)

    result = crew.run_remediation(
        incident_title=incident_title,
        raw_logs=raw_logs,
        force_self_healing_demo=force_self_healing,
    )

    # Format structured JSON response for the frontend
    initial_trace = crew.trace_manager.get_run_trace(result.trace_diff.initial_run_id) if result.trace_diff else None
    corrected_trace = crew.trace_manager.get_run_trace(result.run_id)

    response_payload = {
        "run_id": result.run_id,
            "incident_title": result.incident_title,
            "guardrail": {
                "redactions_count": result.guardrail_result.redactions_count,
                "engine_mode": crew.guardrail.engine_mode,
                "findings": [f.finding_type for f in result.guardrail_result.findings],
            },
            "investigation": {
                "root_cause": result.investigation.root_cause,
                "target_files": result.investigation.target_files,
                "proposed_fix_strategy": result.investigation.proposed_fix_strategy,
                "steps": result.investigation.investigation_steps,
            },
            "fix": {
                "file_path": result.fix_outcome.file_path,
                "explanation": result.fix_outcome.explanation,
                "diff": result.fix_outcome.diff_patch,
                "checkpoint_id": result.fix_outcome.entire_checkpoint.checkpoint_id,
                "checkpoint_nodes": result.fix_outcome.entire_checkpoint.entire_graph_nodes,
            },
            "verification": {
                "passed": result.verification.passed,
                "tests_run": result.verification.tests_run,
                "tests_passed": result.verification.tests_passed,
                "logs": result.verification.verification_logs,
            },
            "meta_agent": {
                "triggered": result.meta_diagnosis is not None,
                "failed_span": result.meta_diagnosis.failed_span_name if result.meta_diagnosis else None,
                "cause": result.meta_diagnosis.failure_cause if result.meta_diagnosis else None,
                "instructions": result.meta_diagnosis.corrective_instructions if result.meta_diagnosis else None,
            } if result.meta_diagnosis else None,
            "trace_diff": {
                "initial_run": result.trace_diff.initial_run_id,
                "corrected_run": result.trace_diff.corrected_run_id,
                "markdown": result.trace_diff.markdown_summary,
                "error_resolved": result.trace_diff.error_resolved,
            } if result.trace_diff else None,
            "traces": {
                "dashboard_url": f"https://app.neatlogs.com/traces?orgId={settings.neatlogs.org_id}&projectId={settings.neatlogs.project_id}",
                "initial_run": {
                    "id": initial_trace.run_id,
                    "url": initial_trace.neatlogs_url,
                    "status": initial_trace.status,
                    "spans": [s.model_dump() for s in initial_trace.spans],
                    "tokens": initial_trace.total_tokens,
                    "duration_s": initial_trace.total_duration_s,
                } if initial_trace else None,
                "corrected_run": {
                    "id": corrected_trace.run_id,
                    "url": corrected_trace.neatlogs_url,
                    "status": corrected_trace.status,
                    "spans": [s.model_dump() for s in corrected_trace.spans],
                    "tokens": corrected_trace.total_tokens,
                    "duration_s": corrected_trace.total_duration_s,
                } if corrected_trace else None,
            },
            "pull_request": {
                "title": result.pull_request.title,
                "url": result.pull_request.pr_url,
                "body": result.pull_request.body_markdown,
            },
            "telemetry": {
                "iterations": result.iterations_count,
                "total_tokens": result.total_tokens,
                "total_cost_usd": result.total_cost_usd,
        }
    }

    global _last_remediation_result
    _last_remediation_result = response_payload
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(response_payload, f, indent=2)
    except Exception:
        pass

    return jsonify(response_payload)


if __name__ == "__main__":
    print("🚀 FixPilot Dashboard starting at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
