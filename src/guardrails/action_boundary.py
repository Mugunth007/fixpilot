"""Action Boundary Enforcer — prevents agents from executing destructive commands."""

import re
from typing import List, Optional
from pydantic import BaseModel


class ActionEvaluation(BaseModel):
    """The safety evaluation result of an action/command proposed by an agent."""
    command: str
    is_safe: bool
    requires_approval: bool
    risk_level: str  # SAFE, WARNING, DANGEROUS, BLOCKED
    reason: str
    matched_pattern: Optional[str] = None


class ActionBoundary:
    """Enforces safety guardrails over commands, scripts, and file modifications."""

    # Explicitly forbidden commands that will immediately be terminated
    BLOCKED_PATTERNS = [
        (r"\brm\s+(-[rfRF]{1,4}\s+|--recursive\s+).*", "Destructive recursive file deletion"),
        (r"\b(format|mkfs|dd\s+if=)", "Drive or filesystem formatting operation"),
        (r"\b(DROP\s+DATABASE|DROP\s+TABLE|TRUNCATE\s+TABLE)\b", "Destructive database schema operation"),
        (r"\bgit\s+push\s+.*--force\b", "Force-pushing can overwrite remote branch history"),
        (r"\bgit\s+reset\s+--hard\b", "Hard reset discards uncommitted workspace state"),
        (r"\bchmod\s+777\b", "Insecure global permission assignment"),
        (r"\bcurl\s+.*\|\s*(bash|sh)\b", "Piping remote script directly to shell is unsafe"),
        (r"\bshutdown\s+|reboot\b", "System shutdown or reboot commands are disallowed"),
    ]

    # Sensitive operations that require explicit user flag
    SENSITIVE_PATTERNS = [
        (r"\bgit\s+push\b", "Pushing to remote repository requires confirmation"),
        (r"\b(npm\s+publish|pip\s+upload)\b", "Publishing packages to public registries"),
        (r"\b(kubectl\s+delete|helm\s+uninstall)\b", "Infrastructure resource deletion"),
        (r"\b(DROP|DELETE\s+FROM)\b", "Direct production data deletion statement"),
    ]

    def evaluate(self, command: str) -> ActionEvaluation:
        """Evaluates a command string against safety rules."""
        trimmed = command.strip()

        # Check blocked patterns first
        for pattern, reason in self.BLOCKED_PATTERNS:
            if re.search(pattern, trimmed, re.IGNORECASE):
                return ActionEvaluation(
                    command=trimmed,
                    is_safe=False,
                    requires_approval=True,
                    risk_level="BLOCKED",
                    reason=f"Action blocked by safety policy: {reason}",
                    matched_pattern=pattern,
                )

        # Check sensitive patterns
        for pattern, reason in self.SENSITIVE_PATTERNS:
            if re.search(pattern, trimmed, re.IGNORECASE):
                return ActionEvaluation(
                    command=trimmed,
                    is_safe=True,
                    requires_approval=True,
                    risk_level="WARNING",
                    reason=f"Action requires explicit verification: {reason}",
                    matched_pattern=pattern,
                )

        # Safe by default
        return ActionEvaluation(
            command=trimmed,
            is_safe=True,
            requires_approval=False,
            risk_level="SAFE",
            reason="Command is within allowed non-destructive boundary",
            matched_pattern=None,
        )
