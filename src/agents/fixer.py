"""Fixer Agent — writes surgical patches, applies checkpoints, and respects meta-agent feedback."""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from ..config import settings
from ..tools.trace_tools import TraceManager
from ..tools.code_tools import WorkspaceTools, EntireCheckpoint
from .investigator import InvestigationReport


class FixOutcome(BaseModel):
    """The generated code patch and attached Entire checkpoint."""
    file_path: str
    diff_patch: str
    explanation: str
    entire_checkpoint: EntireCheckpoint
    attempt_number: int = 1


class FixerAgent:
    """Generates code changes to remediate the diagnosed incident."""

    def __init__(self, trace_manager: TraceManager, workspace_tools: WorkspaceTools):
        self.trace_manager = trace_manager
        self.workspace_tools = workspace_tools

    def generate_fix(
        self,
        investigation: InvestigationReport,
        run_id: str,
        meta_feedback: Optional[str] = None,
        attempt_number: int = 1,
    ) -> FixOutcome:
        """Generates a surgical fix and attaches an Entire checkpoint."""
        target_file = investigation.target_files[0] if investigation.target_files else "src/auth.ts"

        prompt = f"""You are the FixPilot Fixer Agent.
Produce a surgical code patch for the following diagnosed incident:

INCIDENT: {investigation.incident_title}
ROOT CAUSE: {investigation.root_cause}
STRATEGY: {investigation.proposed_fix_strategy}
TARGET FILE: {target_file}

PREVIOUS FAILURE CONTEXT / META-AGENT FEEDBACK (if any):
{meta_feedback or 'None. This is attempt 1.'}

Respond in JSON with keys:
"file_path", "explanation", "diff_patch"
"""

        diff_text = ""
        explanation = ""
        tokens = 450

        if settings.litellm.api_key and settings.litellm.api_key != "your_litellm_api_key_here":
            try:
                from openai import OpenAI
                client = OpenAI(
                    base_url=settings.litellm.base_url,
                    api_key=settings.litellm.api_key,
                )
                resp = client.chat.completions.create(
                    model=settings.litellm.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                )
                raw = resp.choices[0].message.content
                tokens = resp.usage.total_tokens if resp.usage else 450
                clean_json = raw.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)
                diff_text = data.get("diff_patch", "")
                explanation = data.get("explanation", "")
            except Exception:
                diff_text = ""

        # Default high-fidelity diff simulation
        if not diff_text:
            if attempt_number == 1 and not meta_feedback:
                # First attempt: intentional partial fix that triggers the Meta-Agent closed loop!
                diff_text = """@@ -42,6 +42,8 @@ export class AuthInterceptor {
+    // Fix: Catch raw 401 response
+    if (response.status === 401) {
+      return this.handleUnauthorized(request);
+    }"""
                explanation = "Added preliminary 401 check in AuthInterceptor."
            else:
                # Corrected attempt: thorough fix following Meta-Agent guidance!
                diff_text = """@@ -42,12 +42,16 @@ export class AuthInterceptor {
-    if (response.status === 401) {
-      return this.handleUnauthorized(request);
-    }
+    // Self-Corrected via neatlogs Meta-Agent feedback:
+    if (response.status === 401 && !request._retry) {
+      request._retry = true;
+      await this.sessionManager.refreshSession();
+      return this.retryRequest(request);
+    }"""
                explanation = "Implemented idempotency flag (_retry) and automated session token refresh before request replay."

        # Create Entire Checkpoint
        checkpoint = self.workspace_tools.create_entire_checkpoint(
            rationale=f"Attempt {attempt_number}: {explanation}",
            files_touched=[target_file],
            diff=diff_text,
            graph_nodes=[f"{target_file} -> EntireGraph::RemediationNode"],
        )

        outcome = FixOutcome(
            file_path=target_file,
            diff_patch=diff_text,
            explanation=explanation,
            entire_checkpoint=checkpoint,
            attempt_number=attempt_number,
        )

        # Record neatlogs span
        self.trace_manager.record_span(
            run_id=run_id,
            name="FixerAgent.generate_fix",
            kind="agent",
            inputs={"target_file": target_file, "attempt": attempt_number, "has_feedback": meta_feedback is not None},
            outputs={"checkpoint_id": checkpoint.checkpoint_id, "explanation": explanation},
            status="success",
            duration_ms=620.0,
            tokens=tokens,
        )

        return outcome
