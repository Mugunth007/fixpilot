"""Preset Incident Scenarios — realistic production failure scenarios for testing and judging demonstrations."""

from typing import Dict, List, Optional
from pydantic import BaseModel


class PresetScenario(BaseModel):
    """A realistic failure event that triggers FixPilot."""
    id: str
    name: str
    trigger_type: str  # ci_failure, github_issue
    title: str
    description: str
    raw_logs: str
    expected_redactions: int


PRESETS: Dict[str, PresetScenario] = {
    "ci_auth_failure": PresetScenario(
        id="ci_auth_failure",
        name="🔴 3 AM CI Failure: Auth Token Refresh (Leaked JWT)",
        trigger_type="ci_failure",
        title="CI Build #1049 Failed: AuthInterceptor throws unhandled 401 rejection",
        description="A late-night production CI build failed during integration tests. The log contains an active JWT token and database connection string.",
        raw_logs="""[2026-10-11T03:14:02.102Z] INFO: Starting test runner for backend-auth...
[2026-10-11T03:14:04.421Z] DEBUG: Database connected at postgres://db_admin:P@ssw0rd99!@prod-db.internal.vpc:5432/auth_db
[2026-10-11T03:14:05.118Z] ERROR: UnhandledPromiseRejection: 401 Unauthorized in AuthInterceptor
[2026-10-11T03:14:05.119Z] Stack trace:
    at SessionManager.refreshSession (src/auth/session.ts:84:15)
    at AuthInterceptor.handle (src/middleware/auth.ts:42:22)
    at async TestRunner.execute (test/auth.test.ts:18:9)
[2026-10-11T03:14:05.120Z] DEBUG: Authorization header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
[2026-10-11T03:14:05.121Z] System admin contact: oncall-team@company.internal (IP: 192.168.1.144)
[2026-10-11T03:14:05.122Z] Exit code: 1. Build FAILED.""",
        expected_redactions=4,
    ),
    "github_payment_webhook": PresetScenario(
        id="github_payment_webhook",
        name="🐛 GitHub Issue #42: Stripe Webhook Replay Exhaustion",
        trigger_type="github_issue",
        title="Issue #42: Payment webhook retry loop causes duplicate fulfillment",
        description="High-priority bug filed by customer success. Payment webhooks re-processed on transient network timeout. Log contains Stripe secret key and AWS credentials.",
        raw_logs="""[2026-10-11T14:22:11Z] [StripeWebhookHandler] Processing event evt_1N2e4k2eZvKYlo2CL
[2026-10-11T14:22:12Z] [AWSClient] Backing up payload to s3://payment-ledger with AKIAIOSFODNN7EXAMPLE
[2026-10-11T14:22:13Z] [ERROR] Timeout in database transaction. Retrying webhook with secret sec_token_demo_51MszE4k2eZvKYlo2C00998877...
[2026-10-11T14:22:14Z] [EXCEPTION] DuplicateKeyError: order_id already settled in src/payments/webhook.ts:58:11
[2026-10-11T14:22:15Z] Stack trace:
    at WebhookHandler.settleOrder (src/payments/webhook.ts:58:11)
    at Router.dispatch (src/server.ts:104:9)
[2026-10-11T14:22:16Z] Webhook rejected with HTTP 500.""",
        expected_redactions=2,
    ),
}


def list_preset_scenarios() -> List[PresetScenario]:
    """Returns all available preset scenarios."""
    return list(PRESETS.values())


def get_preset_scenario(scenario_id: str) -> Optional[PresetScenario]:
    """Retrieves a specific scenario by id."""
    return PRESETS.get(scenario_id)
