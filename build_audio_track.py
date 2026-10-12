import subprocess
from pathlib import Path

FFMPEG = r"C:\Users\mugun\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
FFPROBE = r"C:\Users\mugun\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffprobe.exe"
OUT_DIR = Path("demo_generation")
AUDIO_DIR = OUT_DIR / "audio"

def create_master_audio():
    # Create silence audio files
    subprocess.run([FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "0.8", "-q:a", "2", str(OUT_DIR / "silence_intro.mp3")], check=True)
    subprocess.run([FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "1.0", "-q:a", "2", str(OUT_DIR / "silence_1s.mp3")], check=True)
    subprocess.run([FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "2.0", "-q:a", "2", str(OUT_DIR / "silence_outro.mp3")], check=True)

    concat_file = OUT_DIR / "concat_list.txt"
    files = [
        OUT_DIR / "silence_intro.mp3",
        AUDIO_DIR / "seg1_intro.mp3",
        OUT_DIR / "silence_1s.mp3",
        AUDIO_DIR / "seg2_guardrail.mp3",
        OUT_DIR / "silence_1s.mp3",
        AUDIO_DIR / "seg3_trigger.mp3",
        OUT_DIR / "silence_1s.mp3",
        AUDIO_DIR / "seg4_meta_agent.mp3",
        OUT_DIR / "silence_1s.mp3",
        AUDIO_DIR / "seg5_neatlogs.mp3",
        OUT_DIR / "silence_1s.mp3",
        AUDIO_DIR / "seg6_github_entire.mp3",
        OUT_DIR / "silence_1s.mp3",
        AUDIO_DIR / "seg7_cfo.mp3",
        OUT_DIR / "silence_1s.mp3",
        AUDIO_DIR / "seg8_outro.mp3",
        OUT_DIR / "silence_outro.mp3",
    ]

    with open(concat_file, "w", encoding="utf-8") as f:
        for p in files:
            escaped = p.resolve().as_posix()
            f.write(f"file '{escaped}'\n")

    out_master = OUT_DIR / "master_voiceover.mp3"
    # Re-encode slightly to ensure smooth concat without timestamp gaps
    subprocess.run([
        FFMPEG, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(out_master)
    ], check=True)

    # Get duration
    cmd = [
        FFPROBE,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(out_master)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    duration = float(res.stdout.strip())
    print(f"Master voiceover created: {out_master} (Total Duration: {duration:.2f}s = {duration/60:.2f} mins)")
    return duration

if __name__ == "__main__":
    create_master_audio()
