#!/usr/bin/env python3
"""
Test Tone for Audio Bridge Latency Measurement + Compensation
Plays 1kHz beeps with timestamps. Use with 'python bridge.py --calibrate'
"""

import time
import subprocess

def main():
    print('=== Audio Bridge Test Tone ===')
    print('Playing 1000Hz tone (100ms) every 1.5s.')
    print('Timestamps help measure delay for automatic compensation.')
    print('Ctrl+C to stop.\n')
    try:
        while True:
            ts = time.time()
            print(f'[{ts:.3f}] BEEP')
            subprocess.run([
                'ffplay', '-f', 'lavfi',
                '-i', 'sine=frequency=1000:duration=0.1',
                '-nodisp', '-autoexit', '-loglevel', 'quiet'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.4)
    except KeyboardInterrupt:
        print('\nStopped.')

if __name__ == '__main__':
    main()
"""
Test Tone Generator for Audio Bridge Latency Measurement
Plays a short 1kHz beep every ~1.5s and prints timestamp.
Use this to measure delay between PC and phone.

Usage:
  python test_tone.py

On phone: Record audio (Voice Recorder or VLC) while running this.
Compare timestamps on PC print vs. when you hear the beep on recording.

To compensate: Note the average delay (e.g. 80ms) and use in players/editors if possible.
"""
import time
import subprocess

def main():
    print('=== Audio Bridge Test Tone ===')
    print('Playing 1000Hz tone (100ms) every 1.5 seconds.')
    print('Watch the timestamps below.')
    print('Record on phone and measure delay.')
    print('Ctrl+C to stop.\n')
    
    try:
        while True:
            ts = time.time()
            print(f'[{ts:.3f}] BEEP')
            # Generate and play 1000Hz sine for 0.1s using ffplay (low latency)
            subprocess.run([
                'ffplay', '-f', 'lavfi',
                '-i', 'sine=frequency=1000:duration=0.1',
                '-nodisp', '-autoexit', '-loglevel', 'quiet'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.4)  # ~1.5s interval
    except KeyboardInterrupt:
        print('\nTest stopped.')

if __name__ == '__main__':
    main()
