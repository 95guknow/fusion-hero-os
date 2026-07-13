#!/usr/bin/env python3
"""
PC to Phone Audio Bridge with Automatic Latency Compensation
- Streams PC system audio over UDP (raw PCM for low latency).
- Supports calibration to measure real delay.
- Automatically recommends/uses compensation (jitter buffer on phone).
- Option to apply compensation delay on sender for testing/sync.
"""

import subprocess
import sys
import json
import time
import argparse
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "audio_bridge_config.json"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"measured_delay_ms": None}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def calibrate():
    """Run test tones and let user input measured delay."""
    print("=== Latency Calibration Mode ===")
    print("This will play test tones. Record on your phone.")
    print("Measure the time between PC 'BEEP' print and when you hear it.")
    input("Press Enter to start calibration (Ctrl+C to cancel)...")

    cfg = load_config()
    delays = []

    try:
        for i in range(5):
            ts = time.time()
            print(f"[{ts:.3f}] BEEP {i+1}/5")
            subprocess.run([
                "ffplay", "-f", "lavfi",
                "-i", "sine=frequency=1000:duration=0.1",
                "-nodisp", "-autoexit", "-loglevel", "quiet"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.5)

            measured = input(f"Measured delay for beep {i+1} (ms, or empty to skip): ").strip()
            if measured:
                try:
                    delays.append(float(measured))
                except ValueError:
                    pass
    except KeyboardInterrupt:
        print("\nCalibration cancelled.")

    if delays:
        avg_delay = sum(delays) / len(delays)
        cfg["measured_delay_ms"] = round(avg_delay, 1)
        save_config(cfg)
        print(f"\nSaved average measured delay: {cfg['measured_delay_ms']} ms")
        recommended_buffer = int(avg_delay * 1.2 + 15)  # margin for jitter
        print(f"Recommended VLC --audio-buffer: {recommended_buffer}")
    else:
        print("No measurements recorded.")

def main():
    parser = argparse.ArgumentParser(description="PC to Phone Audio Bridge with auto compensation")
    parser.add_argument("--phone-ip", help="Phone IP address")
    parser.add_argument("--device", default="StereoMix", help="dshow audio device name")
    parser.add_argument("--port", type=int, default=12345, help="UDP port")
    parser.add_argument("--calibrate", action="store_true", help="Run latency calibration")
    parser.add_argument("--compensate", type=float, default=0,
                        help="Add this many ms delay on sender (for compensation testing)")
    args = parser.parse_args()

    if args.calibrate:
        calibrate()
        return

    cfg = load_config()
    phone_ip = args.phone_ip or input("Phone IP: ").strip()
    device = args.device
    port = args.port
    compensate_ms = args.compensate

    if compensate_ms == 0 and cfg.get("measured_delay_ms"):
        print(f"Using saved measured delay: {cfg['measured_delay_ms']} ms for recommendation")
        recommended = int(cfg["measured_delay_ms"] * 1.2 + 15)
        print(f"Recommended phone buffer: --audio-buffer={recommended}")

    # Build ffmpeg command with low latency + optional compensation
    cmd = [
        "ffmpeg",
        "-f", "dshow",
        "-i", f"audio={device}",
        "-ac", "2",
        "-ar", "48000",
        "-fflags", "nobuffer",
        "-flags", "low_delay",
        "-probesize", "32",
        "-analyzeduration", "0",
    ]

    if compensate_ms > 0:
        # Add delay on sender side (increases total latency but can be used for sync compensation)
        cmd += ["-af", f"adelay={int(compensate_ms)}|{int(compensate_ms)}"]

    cmd += [
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        f"udp://{phone_ip}:{port}"
    ]

    print(f"=== PC to Phone Audio Bridge (Auto Compensation Mode) ===")
    print(f"Streaming to udp://{phone_ip}:{port}")
    print(f"Device: {device}")
    if compensate_ms > 0:
        print(f"Compensation delay applied on sender: {compensate_ms} ms")
    print("\nOn phone (VLC low latency command):")
    buffer = recommended if 'recommended' in locals() else 20
    print(f"vlc --demux=rawaud --rawaud-channels=2 --rawaud-samplerate=48000 --audio-buffer={buffer} udp://@:{port}")
    print("\nPress Ctrl+C to stop.\n")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopped by user.")

if __name__ == "__main__":
    main()
