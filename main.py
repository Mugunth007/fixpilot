"""FixPilot CLI — command-line entry point for autonomous SRE and GitHub remediation."""

import argparse
import sys
import io

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from src.agents.crew import FixPilotCrew
from src.triggers.presets import get_preset_scenario, list_preset_scenarios

console = Console(force_terminal=True)


def run_cli():
    parser = argparse.ArgumentParser(description="FixPilot: Autonomous Self-Healing SRE & Code Remediator")
    parser.add_argument(
        "--scenario",
        type=str,
        default="ci_auth_failure",
        help="Preset scenario ID (e.g. ci_auth_failure, github_payment_webhook)",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List all preset scenarios",
    )
    args = parser.parse_args()

    if args.list_scenarios:
        console.print("[bold cyan]Available Scenarios:[/bold cyan]")
        for s in list_preset_scenarios():
            console.print(f" - [bold green]{s.id}[/bold green]: {s.name}")
        return

    scenario = get_preset_scenario(args.scenario)
    if not scenario:
        console.print(f"[bold red]Scenario '{args.scenario}' not found![/bold red]")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold white]{scenario.name}[/bold white]\n[dim]{scenario.description}[/dim]",
            title="🚀 FixPilot Autonomous Run Initiated",
            border_style="cyan",
        )
    )

    crew = FixPilotCrew()
    with console.status("[bold green]Executing FixPilot multi-agent self-healing loop..."):
        result = crew.run_remediation(
            incident_title=scenario.title,
            raw_logs=scenario.raw_logs,
            force_self_healing_demo=True,
        )

    # 1. Guardrail Report
    console.print("\n[bold cyan]1. 🛡️ Local AI Guardrail Layer[/bold cyan]")
    guard_table = Table(title="Sanitization Telemetry", show_header=True)
    guard_table.add_column("Engine Mode", style="magenta")
    guard_table.add_column("Secrets Redacted", style="green")
    guard_table.add_column("Redacted Categories", style="yellow")
    guard_table.add_row(
        crew.guardrail.engine_mode,
        str(result.guardrail_result.redactions_count),
        ", ".join(set(f.finding_type for f in result.guardrail_result.findings)) or "None",
    )
    console.print(guard_table)

    # 2. Investigation Report
    console.print("\n[bold cyan]2. 🔍 Investigator Agent Findings[/bold cyan]")
    console.print(f"[bold]Root Cause:[/bold] {result.investigation.root_cause}")
    console.print(f"[bold]Target Files:[/bold] {', '.join(result.investigation.target_files)}")

    # 3. Meta-Agent Self-Healing
    if result.meta_diagnosis:
        console.print("\n[bold yellow]3. 🧠 Meta-Agent Self-Healing (neatlogs Trace Inspection)[/bold yellow]")
        console.print(
            Panel(
                f"[bold red]Previous Failed Step:[/bold red] {result.meta_diagnosis.failed_span_name}\n"
                f"[bold red]Trace Diagnosis:[/bold red] {result.meta_diagnosis.failure_cause}\n\n"
                f"[bold green]Corrective Guidance Injected:[/bold green] {result.meta_diagnosis.corrective_instructions}",
                title="🔍 neatlogs Trace Auto-Remediation",
                border_style="yellow",
            )
        )

    # 4. Verification
    console.print("\n[bold cyan]4. ✅ Verifier Agent Outcome[/bold cyan]")
    ver_status = "[bold green]100% PASSED[/bold green]" if result.verification.passed else "[bold red]FAILED[/bold red]"
    console.print(f"Status: {ver_status} ({result.verification.tests_passed}/{result.verification.tests_run} tests)")

    # 5. Pull Request & Economics
    console.print("\n[bold cyan]5. 📝 Pull Request & cfo.ai Unit Economics[/bold cyan]")
    console.print(f"[bold]PR Title:[/bold] {result.pull_request.title}")
    console.print(f"[bold]PR URL:[/bold] [link={result.pull_request.pr_url}]{result.pull_request.pr_url}[/link]")
    console.print(f"[bold]Entire Checkpoint:[/bold] `{result.fix_outcome.entire_checkpoint.checkpoint_id}`")

    if result.trace_diff:
        console.print("\n" + result.trace_diff.markdown_summary)


if __name__ == "__main__":
    run_cli()
