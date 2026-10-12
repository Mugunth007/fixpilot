"""Dual-Engine Local Guardrail — combines local Llama 4-bit reasoning with high-speed regex sanitization."""

import os
from typing import Optional, Dict, Any
from ..config import settings
from .scanner import SecretScanner
from .masker import DataMasker, MaskResult
from .action_boundary import ActionBoundary, ActionEvaluation


class LocalGuardrailEngine:
    """Manages local guardrail execution.

    Attempts to load a local GGUF model via llama-cpp-python if configured and available.
    Falls back gracefully to high-performance regex masking and heuristic rules.
    """

    def __init__(self):
        self.masker = DataMasker(SecretScanner())
        self.action_boundary = ActionBoundary()
        self.llama_model = None
        self.engine_mode = "regex_heuristics"

        # Attempt to load local llama model if available
        self._init_local_model()

    def _init_local_model(self):
        model_path = settings.local_llm.model_path
        if not model_path or not os.path.exists(model_path):
            self.engine_mode = "fast_heuristics"
            return

        try:
            from llama_cpp import Llama
            self.llama_model = Llama(
                model_path=model_path,
                n_ctx=settings.local_llm.context_length,
                n_threads=settings.local_llm.n_threads,
                verbose=False,
            )
            self.engine_mode = "local_llama_hybrid"
        except Exception as e:
            # Fallback smoothly without breaking the agent runtime
            self.engine_mode = f"fast_heuristics (fallback: {str(e)[:30]})"

    def sanitize_log(self, text: str) -> MaskResult:
        """Sanitizes text by stripping all secrets, PII, and credentials before cloud transmission."""
        mask_result = self.masker.mask(text)

        # If local Llama model is available, perform additional semantic safety check
        if self.llama_model and mask_result.sanitized_text:
            try:
                # Quick semantic prompt to verify no leaked secrets remain
                prompt = (
                    "Q: Does the following sanitized log contain any unmasked passwords, secret keys, or credit cards? "
                    "Answer ONLY YES or NO.\n"
                    f"Text: {mask_result.sanitized_text[:500]}\nA:"
                )
                output = self.llama_model(prompt, max_tokens=8, stop=["\n"])
                answer = output["choices"][0]["text"].strip()
                # If local Llama detected residual sensitive text, append a flag
                if "YES" in answer.upper():
                    mask_result.findings.append(
                        self.masker.scanner.scan("SUSPECTED_RESIDUAL_LEAK")[0]
                        if self.masker.scanner.scan("SUSPECTED_RESIDUAL_LEAK")
                        else None
                    )
            except Exception:
                pass

        return mask_result

    def verify_action(self, command: str) -> ActionEvaluation:
        """Validates that a shell or git command adheres to the safety action boundary."""
        evaluation = self.action_boundary.evaluate(command)
        return evaluation

    def get_status(self) -> Dict[str, Any]:
        """Returns the current guardrail engine status and telemetry."""
        return {
            "mode": self.engine_mode,
            "has_local_model": self.llama_model is not None,
            "model_path": settings.local_llm.model_path,
            "action_rules_active": len(self.action_boundary.BLOCKED_PATTERNS) + len(self.action_boundary.SENSITIVE_PATTERNS),
        }
