"""Local Secret & PII Scanner — identifies credentials, tokens, and sensitive data in logs and files."""

import re
from typing import List
from pydantic import BaseModel


class PIIFinding(BaseModel):
    """Represents a discovered secret or sensitive data point."""
    finding_type: str
    value: str
    start: int
    end: int
    confidence: float = 1.0


class SecretScanner:
    """Scans text for common production secrets, API tokens, connection strings, and PII."""

    # High-precision patterns for production leaks
    PATTERNS = {
        "JWT_TOKEN": r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}",
        "AWS_ACCESS_KEY": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        "AWS_SECRET_KEY": r"(?i)aws_(?:secret|key|access_key)[\s:=]+['\"]?([A-Za-z0-9/+=]{40})['\"]?",
        "GITHUB_TOKEN": r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}",
        "STRIPE_KEY": r"(?:sk|pk)_(?:live|test)_[0-9a-zA-Z]{24,99}",
        "GENERIC_API_KEY": r"(?i)(?:api[_-]?key|auth[_-]?token|bearer|secret)[\s:=]+['\"]?([a-zA-Z0-9_\-\.]{24,128})['\"]?",
        "DATABASE_URI": r"(?:postgres|postgresql|mongodb|mysql|redis):\/\/[a-zA-Z0-9_]+:[^\s]+@[a-zA-Z0-9_\-\.]+:\d+\/[a-zA-Z0-9_\-\.]+",
        "PRIVATE_KEY": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "PASSWORD_ASSIGNMENT": r"(?i)(?:password|passwd|pwd)[\s:=]+['\"]?([^\s'\"]{6,64})['\"]?",
        "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "IP_ADDRESS": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
    }

    def __init__(self):
        self._compiled = {k: re.compile(v) for k, v in self.PATTERNS.items()}

    def scan(self, text: str) -> List[PIIFinding]:
        """Scans the provided text and returns non-overlapping findings sorted by position."""
        if not text:
            return []

        raw_findings: List[PIIFinding] = []

        for category, regex in self._compiled.items():
            for match in regex.finditer(text):
                # If regex has capture group 1 (e.g. for extracting key value after prefix)
                if match.groups() and match.group(1):
                    val = match.group(1)
                    start = match.start(1)
                    end = match.end(1)
                else:
                    val = match.group(0)
                    start = match.start()
                    end = match.end()

                raw_findings.append(
                    PIIFinding(
                        finding_type=category,
                        value=val,
                        start=start,
                        end=end,
                        confidence=0.98 if "KEY" in category or "TOKEN" in category else 0.90,
                    )
                )

        # Sort findings by start index and deduplicate overlapping ranges
        raw_findings.sort(key=lambda f: f.start)
        clean_findings: List[PIIFinding] = []
        last_end = -1

        for f in raw_findings:
            if f.start >= last_end:
                clean_findings.append(f)
                last_end = f.end

        return clean_findings
