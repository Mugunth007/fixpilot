"""Generates voiceover audio segments using Edge-TTS and calculates exact durations."""

import asyncio
import os
import subprocess
from pathlib import Path
import edge_tts

OUTPUT_DIR = Path("demo_generation")
OUTPUT_DIR.mkdir(exist_ok=True)
AUDIO_DIR = OUTPUT_DIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

FFPROBE_EXE = r"C:\Users\mugun\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffprobe.exe"
FFMPEG_EXE = r"C:\Users\mugun\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"

VOICE = "en-US-ChristopherNeural"

SEGMENTS = [
    {
        "id": "seg1_intro",
        "title": "Introduction & Vision",
        "text": "Welcome to FixPilot, the autonomous self-healing SRE and code remediator built for the neatHack AI Agent Hackathon. When production CI pipelines break or critical bugs strike late at night, human on-call engineers spend hours chasing stack traces. FixPilot autonomously diagnoses, fixes, verifies, and opens pull requests—solving the core challenge: building agents you'd trust to run without you watching."
    },
    {
        "id": "seg2_guardrail",
        "title": "Local AI Guardrail Layer",
        "text": "The first critical obstacle to autonomous trust is security and production privacy. Cloud LLMs must never see raw production secrets. FixPilot features an on-device local guardrail layer. As you can see in our incident simulator, raw logs containing database URIs with passwords, active JWT authentication tokens, email addresses, and internal IPs are intercepted locally. Our zero-leak sanitizer instantly redacts every credential on-device before any context reaches the cloud LLM."
    },
    {
        "id": "seg3_trigger",
        "title": "Incident Trigger & Remediation Swarm",
        "text": "Now, let's select our late-night CI authentication failure scenario and launch the autonomous remediation swarm. Notice our four-step pipeline spring into action: Local Guardrail sanitization, Investigator root cause analysis, Fixer code remediation with Entire checkpoints, and Self-Healing test verification."
    },
    {
        "id": "seg4_meta_agent",
        "title": "Meta-Agent Closed-Loop Self-Healing",
        "text": "Here is FixPilot's standout breakthrough: Meta-Agent closed-loop self-healing. In the first run, the initial code patch caught the 401 status code but lacked idempotency tracking, causing an infinite retry loop during verification. Instead of failing and paging an engineer, FixPilot's Meta-Agent inspects its own execution trace directly from neatlogs. It identifies the exact failing span, diagnoses the recursion issue, and provides actionable guidance back to the Fixer. On the second iteration, the fix passes all fifteen test suites with zero regressions."
    },
    {
        "id": "seg5_neatlogs",
        "title": "neatlogs Observability & Trace Diff",
        "text": "Under the neatlogs Evidence tab, we have full trace transparency. neatlogs captures every agent invocation, tool execution, LLM call, token usage, and latency. Here is our live before-and-after trace comparison: Run one clearly shows the failed span in red, while Run two demonstrates the self-corrected resolution in green. With over two thousand tokens saved on the second run and immediate trace diff generation, neatlogs provides the irrefutable evidence required for production trust."
    },
    {
        "id": "seg6_github_entire",
        "title": "GitHub PR & Entire Checkpoints",
        "text": "FixPilot doesn't stop at verification—it automatically generates a complete GitHub Pull Request. The PR includes a surgical git diff patch adding the idempotency retry guard, along with Entire graph dependency nodes and checkpoint IDs. Developers can review, verify, and merge with total peace of mind."
    },
    {
        "id": "seg7_cfo",
        "title": "cfo.ai Unit Economics & Business Value",
        "text": "Finally, let's explore the enterprise impact powered by cfo.ai unit economics. While traditional human on-call triage costs seventy-five dollars per incident, FixPilot resolves the same failure autonomously for just two point eight cents. Using our interactive calculator, an organization facing one hundred fifty monthly incidents saves over eleven thousand dollars per month—achieving an extraordinary ninety-nine point nine percent cost reduction."
    },
    {
        "id": "seg8_outro",
        "title": "Conclusion",
        "text": "FixPilot unites local privacy guardrails, entire repository checkpoints, cfo.ai unit economics, and neatlogs trace-driven self-healing into an autonomous SRE system you can truly trust. Thank you for watching!"
    }
]

def get_audio_duration(file_path: Path) -> float:
    cmd = [
        FFPROBE_EXE,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

async def generate_all():
    timeline = []
    print("Generating voiceover audio segments with Edge-TTS...")
    for idx, seg in enumerate(SEGMENTS):
        out_file = AUDIO_DIR / f"{seg['id']}.mp3"
        print(f"[{idx+1}/{len(SEGMENTS)}] Generating {seg['id']} ({seg['title']})...")
        communicate = edge_tts.Communicate(seg["text"], VOICE, rate="+0%")
        await communicate.save(str(out_file))
        duration = get_audio_duration(out_file)
        print(f"  -> Generated: {duration:.2f}s")
        timeline.append({
            **seg,
            "file": str(out_file),
            "duration": duration
        })

    # Save timeline info
    import json
    with open(OUTPUT_DIR / "voiceover_timeline.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, indent=2)

    total_speech_duration = sum(t["duration"] for t in timeline)
    print(f"\nAll {len(timeline)} segments generated!")
    print(f"Total Speech Duration: {total_speech_duration:.2f} seconds ({total_speech_duration/60:.2f} minutes)")

if __name__ == "__main__":
    asyncio.run(generate_all())
