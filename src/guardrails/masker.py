"""Data Masker & Re-hydrator — replaces sensitive data with reversible surrogate tokens."""

from typing import Dict, List, Tuple
from pydantic import BaseModel
from .scanner import SecretScanner, PIIFinding


class MaskResult(BaseModel):
    """The outcome of data masking, containing sanitized text and the reversible map."""
    sanitized_text: str
    redactions_count: int
    findings: List[PIIFinding]
    token_map: Dict[str, str]  # surrogate_token -> original_value


class DataMasker:
    """Masks secrets and PII with consistent surrogate tokens, and rehydrates on demand."""

    def __init__(self, scanner: SecretScanner = None):
        self.scanner = scanner or SecretScanner()

    def mask(self, text: str) -> MaskResult:
        """Finds all secrets in the text and returns sanitized text with a mapping dictionary."""
        if not text:
            return MaskResult(sanitized_text="", redactions_count=0, findings=[], token_map={})

        findings = self.scanner.scan(text)
        if not findings:
            return MaskResult(
                sanitized_text=text,
                redactions_count=0,
                findings=[],
                token_map={},
            )

        token_map: Dict[str, str] = {}
        category_counters: Dict[str, int] = {}

        # Build replacement string from end to start to preserve accurate character slice offsets
        reconstructed = list(text)
        sorted_rev = sorted(findings, key=lambda f: f.start, reverse=True)

        for finding in sorted_rev:
            cat = finding.finding_type
            category_counters[cat] = category_counters.get(cat, 0) + 1
            surrogate = f"[REDACTED_{cat}_{category_counters[cat]}]"

            token_map[surrogate] = finding.value
            reconstructed[finding.start:finding.end] = list(surrogate)

        sanitized_text = "".join(reconstructed)

        return MaskResult(
            sanitized_text=sanitized_text,
            redactions_count=len(findings),
            findings=findings,
            token_map=token_map,
        )

    def rehydrate(self, masked_text: str, token_map: Dict[str, str]) -> str:
        """Re-substitutes surrogate placeholders back to their original runtime values."""
        if not masked_text or not token_map:
            return masked_text

        result = masked_text
        for surrogate, original in token_map.items():
            result = result.replace(surrogate, original)
        return result
