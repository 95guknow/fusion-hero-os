# Audio Bridge: PC to Phone (Low Latency Focus)

Stream system audio from PC (Windows) to your phone (Android) over local WiFi **with minimal delay**.

## Key for Low/No Delay or Compensation
- **Raw UDP + low buffer flags**: Current setup uses raw PCM (no heavy encoding) + ffmpeg low_delay.
- **Typical latency**: 20-100ms depending on hardware/network (capture + network + playout).
- **Compensation**:
  - Tune VLC --audio-buffer=10 to 50 (lower = less delay, risk of dropouts).
  - Test delay: Play a sharp sound (clap) on PC, record on phone, measure in audio editor.
  - If consistent delay D ms, some players allow negative delay or you can use tools like sox on phone to delay if needed (rare).
  - For pro: Use ASIO drivers + low buffer virtual cable (VB-Audio has settings).

## Optimized ffmpeg (in start.bat)
ffmpeg ... -fflags nobuffer -flags low_delay -probesize 32 -analyzeduration 0 ...

## Best Practices to Minimize Delay
1. **Virtual Audio Cable**: Install free [VB-Audio Virtual Cable](https://vb-audio.com/Cable/).
   - Set as default playback in Windows for the apps you want to hear.
   - Set DEVICE=CABLE Output (VB-Audio Virtual Cable) in start.bat.
   - In VB-Audio control panel: Set buffer to lowest (e.g. 128 or 256 samples).
2. **Network**: 5GHz WiFi or Ethernet. Close bandwidth hogs.
3. **Phone player**:
   - VLC: lc --demux=rawaud --rawaud-channels=2 --rawaud-samplerate=48000 --audio-buffer=20 udp://@ :12345
   - Lower buffer = lower delay.
4. **Capture**: Use 48kHz if possible.
5. **Test**: Use a metronome app or clap test. Adjust buffer until stable.

## Usage
1. Edit start.bat (set correct DEVICE).
2. Run start.bat on PC.
3. Enter phone IP.
4. On phone VLC open udp://@:12345 (or advanced command above).

Press Ctrl+C to stop.

## Automatic Latency Compensation
The bridge now supports **automatic compensation**:

1. Calibrate (measure real delay once):
   ```
   python bridge.py --calibrate
   ```
   Plays test tones. You input measured delays from phone recording.
   Saves average to `audio_bridge_config.json`.

2. Run with auto-recommendations + compensation:
   ```
   python bridge.py --phone-ip 192.168.1.42 --compensate 65
   ```
   - Uses saved delay for recommendations.
   - `--compensate X` applies X ms delay on PC sender (for sync testing or lip-sync with PC video).

3. Normal run loads config and prints best VLC buffer.

## Test Tone (used by calibration)
Run:
  python test_tone.py

Plays 1kHz beeps with timestamps. Use with --calibrate or manually.

## If you want even lower latency
- Custom Android app with AudioTrack + small buffer + Opus decoder (we can build if needed).
- Hardware: USB audio interface with low latency drivers.

Part of the heroic tools suite.
