"""Workspace & Code Tools — file modifications, test runner, and Entire checkpoint generation."""

import os
import subprocess
import difflib
import uuid
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..guardrails.action_boundary import ActionBoundary


class EntireCheckpoint(BaseModel):
    """Represents an Entire checkpoint capturing rationale, code diffs, and context graph."""
    checkpoint_id: str = Field(default_factory=lambda: f"cp_{str(uuid.uuid4())[:8]}")
    created_at: float = Field(default_factory=time.time)
    rationale: str
    files_touched: List[str]
    diff: str
    entire_graph_nodes: List[str] = Field(default_factory=list)


class WorkspaceTools:
    """Provides file operations, test execution, and Entire checkpoint generation."""

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.getcwd()
        self.action_boundary = ActionBoundary()

    def read_file(self, relative_path: str) -> str:
        """Reads content from a workspace file."""
        abs_path = os.path.join(self.workspace_root, relative_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {relative_path}")
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def write_file(self, relative_path: str, content: str) -> Dict[str, Any]:
        """Saves content to a workspace file and returns diff information."""
        abs_path = os.path.join(self.workspace_root, relative_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        original_content = ""
        if os.path.exists(abs_path):
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                original_content = f.read()

        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Generate unified diff
        diff_lines = list(
            difflib.unified_diff(
                original_content.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=f"a/{relative_path}",
                tofile=f"b/{relative_path}",
            )
        )
        diff_text = "".join(diff_lines)

        return {
            "path": relative_path,
            "status": "modified" if original_content else "created",
            "diff": diff_text,
        }

    def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Safely executes a shell or test command within the workspace."""
        # Enforce action boundary
        safety = self.action_boundary.evaluate(command)
        if not safety.is_safe:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"SECURITY BLOCK: {safety.reason}",
                "blocked": True,
            }

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "blocked": False,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -2,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "blocked": False,
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -3,
                "stdout": "",
                "stderr": str(e),
                "blocked": False,
            }

    def create_entire_checkpoint(
        self,
        rationale: str,
        files_touched: List[str],
        diff: str,
        graph_nodes: Optional[List[str]] = None,
    ) -> EntireCheckpoint:
        """Creates an Entire checkpoint recording the AI reasoning and code modifications."""
        nodes = graph_nodes or [f"{f} -> {os.path.basename(f)}" for f in files_touched]
        checkpoint = EntireCheckpoint(
            rationale=rationale,
            files_touched=files_touched,
            diff=diff,
            entire_graph_nodes=nodes,
        )
        return checkpoint
