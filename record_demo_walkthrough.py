"""High-fidelity Automated Screen Recorder for FixPilot Demo Walkthrough.
Choreographed with millisecond precision to match the Edge-TTS master voiceover track.
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from playwright.sync_api import sync_playwright

FFMPEG_EXE = r"C:\Users\mugun\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
FFPROBE_EXE = r"C:\Users\mugun\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffprobe.exe"
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

OUTPUT_DIR = Path("demo_generation")
RAW_VIDEO_DIR = OUTPUT_DIR / "raw_video"
RAW_VIDEO_DIR.mkdir(parents=True, exist_ok=True)

MASTER_AUDIO = OUTPUT_DIR / "master_voiceover.mp3"
FINAL_VIDEO = OUTPUT_DIR / "FixPilot_Official_Demo.mp4"

# Load audio timeline
with open(OUTPUT_DIR / "voiceover_timeline.json", "r", encoding="utf-8") as f:
    TIMELINE = json.load(f)

# Helper to get exact audio duration
def get_duration(file_path: Path) -> float:
    cmd = [
        FFPROBE_EXE,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

CURSOR_SCRIPT = """
(function() {
    if (document.getElementById('__demo_cursor__')) return;
    const cursor = document.createElement('div');
    cursor.id = '__demo_cursor__';
    cursor.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 28px;
        height: 28px;
        z-index: 9999999;
        pointer-events: none;
        transition: transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
        transform: translate(200px, 200px);
    `;
    cursor.innerHTML = `
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" style="filter: drop-shadow(0 2px 8px rgba(0,0,0,0.6));">
            <path d="M4 2L20 9L12 12L9 20L4 2Z" fill="#3b82f6" stroke="#ffffff" stroke-width="1.8" stroke-linejoin="round"/>
        </svg>
        <div id="__click_ripple__" style="position: absolute; top: -6px; left: -6px; width: 36px; height: 36px; border-radius: 50%; border: 2.5px solid #60a5fa; opacity: 0; transform: scale(0.4); pointer-events: none; transition: all 0.35s ease-out;"></div>
    `;
    document.body.appendChild(cursor);

    window.__moveCursor = function(x, y) {
        cursor.style.transform = `translate(${x}px, ${y}px)`;
    };

    window.__clickCursor = function(x, y) {
        cursor.style.transform = `translate(${x}px, ${y}px)`;
        const rip = document.getElementById('__click_ripple__');
        if (rip) {
            rip.style.opacity = '1';
            rip.style.transform = 'scale(1.3)';
            setTimeout(() => {
                rip.style.opacity = '0';
                rip.style.transform = 'scale(0.4)';
            }, 320);
        }
    };

    window.__pulseHighlight = function(selector) {
        const el = document.querySelector(selector);
        if (!el) return;
        el.style.transition = 'box-shadow 0.4s ease, border-color 0.4s ease';
        el.style.boxShadow = '0 0 25px rgba(59, 130, 246, 0.4)';
        el.style.borderColor = 'rgba(59, 130, 246, 0.8)';
        setTimeout(() => {
            el.style.boxShadow = '';
            el.style.borderColor = '';
        }, 2200);
    };
})();
"""

def move_cursor(page, x, y, wait=0.5):
    page.evaluate(f"window.__moveCursor({x}, {y})")
    time.sleep(wait)

def click_cursor(page, x, y, wait=0.4):
    page.evaluate(f"window.__clickCursor({x}, {y})")
    time.sleep(wait)

def pulse(page, selector):
    page.evaluate(f"window.__pulseHighlight('{selector}')")

def run_choreography():
    total_audio_duration = get_duration(MASTER_AUDIO)
    print(f"Master Audio Duration: {total_audio_duration:.2f}s")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_EXE,
            headless=True,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--hide-scrollbars"
            ]
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(RAW_VIDEO_DIR),
            record_video_size={"width": 1920, "height": 1080}
        )

        page = context.new_page()
        page.goto("http://127.0.0.1:5000/?clean=true", wait_until="networkidle")
        page.evaluate(CURSOR_SCRIPT)
        time.sleep(0.8) # Intro silence buffer

        start_time = time.monotonic()

        # ==========================================
        # SEGMENT 1: Introduction & Vision (27.82s + 1.0s gap)
        # ==========================================
        print("[>] Executing Segment 1: Introduction & Vision...")
        seg1_start = time.monotonic()
        
        move_cursor(page, 200, 50, 0.8)
        pulse(page, "header")
        time.sleep(2.0)

        # Move across sponsor pills
        move_cursor(page, 720, 50, 1.0) # Guardrail badge
        move_cursor(page, 950, 50, 1.0) # neatlogs Open Traces badge
        move_cursor(page, 1180, 50, 1.0) # Entire Checkpoints badge
        time.sleep(2.5)

        # Move to mission quote
        move_cursor(page, 350, 90, 1.2)
        time.sleep(4.0)

        # Pan across dashboard overview
        move_cursor(page, 300, 300, 1.2)
        time.sleep(4.0)
        move_cursor(page, 900, 300, 1.2)
        
        # Wait remainder of seg 1 + 1.0s gap
        target_s1 = TIMELINE[0]["duration"] + 1.0
        elapsed_s1 = time.monotonic() - seg1_start
        if elapsed_s1 < target_s1:
            time.sleep(target_s1 - elapsed_s1)

        # ==========================================
        # SEGMENT 2: Local AI Guardrail Layer (34.34s + 1.0s gap)
        # ==========================================
        print("[>] Executing Segment 2: Local AI Guardrail Layer...")
        seg2_start = time.monotonic()

        # Focus on Guardrail card
        move_cursor(page, 300, 500, 1.0)
        pulse(page, "#redactionBadge")
        time.sleep(2.0)

        # Move cursor into raw incident logs terminal
        move_cursor(page, 350, 600, 1.0)
        time.sleep(2.5)

        # Select/highlight sensitive line in rawLogs
        page.evaluate("""
            const el = document.getElementById('rawLogs');
            el.focus();
            el.setSelectionRange(75, 142);
        """)
        time.sleep(3.5)

        # Move cursor to sanitized preview box
        move_cursor(page, 350, 780, 1.0)
        pulse(page, "#sanitizedPreview")
        time.sleep(4.0)

        # Unselect textarea
        page.evaluate("document.getElementById('rawLogs').blur();")

        # Highlight zero leaks badge & confidence scoring
        move_cursor(page, 450, 740, 1.0)
        time.sleep(3.0)

        # Point to Redacted 4 Secret(s) Locally badge
        move_cursor(page, 440, 480, 1.0)
        pulse(page, "#redactionBadge")

        # Wait remainder of seg 2 + 1.0s gap
        target_s2 = TIMELINE[1]["duration"] + 1.0
        elapsed_s2 = time.monotonic() - seg2_start
        if elapsed_s2 < target_s2:
            time.sleep(target_s2 - elapsed_s2)

        # ==========================================
        # SEGMENT 3: Trigger & Remediation Swarm (20.71s + 1.0s gap)
        # ==========================================
        print("[>] Executing Segment 3: Trigger & Swarm Execution...")
        seg3_start = time.monotonic()

        # Move to Scenario selector
        move_cursor(page, 280, 260, 0.8)
        time.sleep(1.5)

        # Move to auto-correct toggle
        move_cursor(page, 200, 385, 0.8)
        time.sleep(1.5)

        # Move to Execute Autonomous Remediation button
        move_cursor(page, 300, 920, 1.0)
        time.sleep(1.5)

        # Click the button with ripple!
        click_cursor(page, 300, 920, 0.4)
        page.click("#runBtn")

        # Move to status progression cards on right
        move_cursor(page, 700, 220, 0.8)
        time.sleep(2.0)
        move_cursor(page, 850, 220, 0.8)
        time.sleep(2.0)
        move_cursor(page, 1000, 220, 0.8)
        time.sleep(2.0)
        move_cursor(page, 1150, 220, 0.8)

        # Wait remainder of seg 3 + 1.0s gap
        target_s3 = TIMELINE[2]["duration"] + 1.0
        elapsed_s3 = time.monotonic() - seg3_start
        if elapsed_s3 < target_s3:
            time.sleep(target_s3 - elapsed_s3)

        # ==========================================
        # SEGMENT 4: Meta-Agent Closed-Loop Self-Healing (37.42s + 1.0s gap)
        # ==========================================
        print("[>] Executing Segment 4: Meta-Agent Closed Loop...")
        seg4_start = time.monotonic()

        # Click Meta-Agent Tab
        move_cursor(page, 720, 480, 0.8)
        click_cursor(page, 720, 480, 0.3)
        page.click("#btnTabMeta")
        time.sleep(1.5)

        # Scroll right column to view Investigator Diagnosis
        move_cursor(page, 800, 580, 1.0)
        pulse(page, "#investigatorDiagnosis")
        time.sleep(3.0)

        # Move to Meta-Agent Self-Correction Box (Purple Card)
        move_cursor(page, 850, 720, 1.0)
        pulse(page, "#metaCorrectionBox")
        time.sleep(4.0)

        # Highlight Failure Detected reason
        move_cursor(page, 850, 750, 1.0)
        time.sleep(3.5)

        # Highlight Corrective Guidance fed to Fixer
        move_cursor(page, 850, 820, 1.0)
        time.sleep(4.5)

        # Scroll down to show Verifier Test logs
        page.evaluate("window.scrollBy({top: 250, behavior: 'smooth'})")
        time.sleep(1.5)
        move_cursor(page, 850, 880, 1.0)
        pulse(page, "#verifierLogs")
        time.sleep(4.0)

        # Scroll back to tab bar
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(1.0)

        # Wait remainder of seg 4 + 1.0s gap
        target_s4 = TIMELINE[3]["duration"] + 1.0
        elapsed_s4 = time.monotonic() - seg4_start
        if elapsed_s4 < target_s4:
            time.sleep(target_s4 - elapsed_s4)

        # ==========================================
        # SEGMENT 5: neatlogs Observability & Trace Diff (32.42s + 1.0s gap)
        # ==========================================
        print("[>] Executing Segment 5: neatlogs Evidence Tab...")
        seg5_start = time.monotonic()

        # Click neatlogs Evidence tab
        move_cursor(page, 890, 480, 0.8)
        click_cursor(page, 890, 480, 0.3)
        page.click("#btnTabTraces")
        time.sleep(1.5)

        # Move across Project ID and neatlogs Cloud links
        move_cursor(page, 850, 550, 1.0)
        pulse(page, "#liveNeatlogsBanner")
        time.sleep(2.5)

        # Point to Trace 1: Failed Attempt
        move_cursor(page, 850, 630, 1.0)
        time.sleep(3.0)

        # Scroll down slightly to show Trace 2: Self-Corrected Attempt
        page.evaluate("window.scrollBy({top: 180, behavior: 'smooth'})")
        time.sleep(1.0)
        move_cursor(page, 850, 680, 1.0)
        time.sleep(3.5)

        # Scroll to Before vs After Trace Comparison table
        page.evaluate("window.scrollBy({top: 240, behavior: 'smooth'})")
        time.sleep(1.2)
        move_cursor(page, 850, 750, 1.0)
        time.sleep(4.5)

        # Scroll back to top
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(1.0)

        # Wait remainder of seg 5 + 1.0s gap
        target_s5 = TIMELINE[4]["duration"] + 1.0
        elapsed_s5 = time.monotonic() - seg5_start
        if elapsed_s5 < target_s5:
            time.sleep(target_s5 - elapsed_s5)

        # ==========================================
        # SEGMENT 6: GitHub PR & Entire Checkpoints (21.22s + 1.0s gap)
        # ==========================================
        print("[>] Executing Segment 6: GitHub PR & Entire Tab...")
        seg6_start = time.monotonic()

        # Click GitHub PR tab
        move_cursor(page, 1050, 480, 0.8)
        click_cursor(page, 1050, 480, 0.3)
        page.click("#btnTabPr")
        time.sleep(1.5)

        # Highlight PR Title
        move_cursor(page, 850, 560, 1.0)
        time.sleep(2.5)

        # Scroll down through PR diff
        page.evaluate("window.scrollBy({top: 200, behavior: 'smooth'})")
        time.sleep(1.2)
        move_cursor(page, 850, 650, 1.0) # Hover over diff patch
        time.sleep(4.0)

        # Scroll back up
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(1.0)

        # Wait remainder of seg 6 + 1.0s gap
        target_s6 = TIMELINE[5]["duration"] + 1.0
        elapsed_s6 = time.monotonic() - seg6_start
        if elapsed_s6 < target_s6:
            time.sleep(target_s6 - elapsed_s6)

        # ==========================================
        # SEGMENT 7: cfo.ai Unit Economics & Business Value (28.92s + 1.0s gap)
        # ==========================================
        print("[>] Executing Segment 7: cfo.ai Economics Tab...")
        seg7_start = time.monotonic()

        # Click cfo.ai Economics tab
        move_cursor(page, 1200, 480, 0.8)
        click_cursor(page, 1200, 480, 0.3)
        page.click("#btnTabCfo")
        time.sleep(1.5)

        # Highlight $0.028 / fix vs $75 / triage
        move_cursor(page, 850, 580, 1.0)
        time.sleep(3.0)

        # Move to Incidents Slider and smoothly drag it
        move_cursor(page, 850, 720, 1.0)
        # Drag slider value from 150 to 240
        for val in range(150, 245, 10):
            page.evaluate(f"""
                const s = document.getElementById('incidentsSlider');
                s.value = {val};
                s.dispatchEvent(new Event('input'));
            """)
            time.sleep(0.15)
        time.sleep(1.5)

        # Move to Rate Slider and smoothly drag it
        move_cursor(page, 850, 810, 1.0)
        for r_val in range(100, 130, 5):
            page.evaluate(f"""
                const r = document.getElementById('rateSlider');
                r.value = {r_val};
                r.dispatchEvent(new Event('input'));
            """)
            time.sleep(0.15)
        time.sleep(1.5)

        # Highlight Monthly Savings & +99.9% Margin
        move_cursor(page, 1050, 880, 1.0)
        pulse(page, "#cfoSavings")
        time.sleep(4.0)

        # Scroll to top
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(1.0)

        # Wait remainder of seg 7 + 1.0s gap
        target_s7 = TIMELINE[6]["duration"] + 1.0
        elapsed_s7 = time.monotonic() - seg7_start
        if elapsed_s7 < target_s7:
            time.sleep(target_s7 - elapsed_s7)

        # ==========================================
        # SEGMENT 8: Conclusion & Outro (15.48s + 2.0s buffer)
        # ==========================================
        print("[>] Executing Segment 8: Conclusion...")
        seg8_start = time.monotonic()

        # Move cursor to hero branding
        move_cursor(page, 200, 50, 1.0)
        pulse(page, "header")
        time.sleep(3.0)

        # Pan across to neatHack badge and live telemetry
        move_cursor(page, 800, 200, 1.5)
        time.sleep(4.0)

        # Move cursor gently off center
        move_cursor(page, 1700, 950, 1.5)

        # Wait remainder of seg 8 + 2.0s buffer
        target_s8 = TIMELINE[7]["duration"] + 2.0
        elapsed_s8 = time.monotonic() - seg8_start
        if elapsed_s8 < target_s8:
            time.sleep(target_s8 - elapsed_s8)

        total_elapsed = time.monotonic() - start_time
        print(f"Recorded actions completed in {total_elapsed:.2f}s (Audio: {total_audio_duration:.2f}s)")

        # Ensure page video is finalized
        time.sleep(0.5)
        video_path = page.video.path()
        context.close()
        browser.close()

    print(f"Raw video saved at: {video_path}")

    # ==========================================
    # FINAL STEP: Muxing with FFmpeg
    # ==========================================
    print("Muxing video with master audio using FFmpeg...")
    mux_cmd = [
        FFMPEG_EXE, "-y",
        "-i", str(video_path),
        "-i", str(MASTER_AUDIO),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(FINAL_VIDEO)
    ]
    subprocess.run(mux_cmd, check=True)
    final_duration = get_duration(FINAL_VIDEO)
    final_size = FINAL_VIDEO.stat().st_size / (1024 * 1024)
    print(f"\n=== FINAL DEMO VIDEO CREATED ===")
    print(f"Path: {FINAL_VIDEO.resolve()}")
    print(f"Duration: {final_duration:.2f} seconds ({final_duration/60:.2f} mins)")
    print(f"File Size: {final_size:.2f} MB")

if __name__ == "__main__":
    run_choreography()
