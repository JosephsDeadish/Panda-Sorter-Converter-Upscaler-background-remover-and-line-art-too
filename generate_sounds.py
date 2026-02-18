#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate synthetic WAV sound files for the PS2 Texture Sorter
Creates all missing sound files referenced in sound_manager.py
"""

import sys
import wave
import struct
import math
import os
from pathlib import Path

# Fix Unicode encoding issues on Windows
# This prevents UnicodeEncodeError when printing emojis to console
if sys.platform == 'win32':
    import codecs
    # Reconfigure stdout and stderr to use UTF-8 encoding
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    # Also set environment variable for child processes
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Constants
SAMPLE_RATE = 44100
BITS_PER_SAMPLE = 16
CHANNELS = 1

def generate_sine_wave(frequency, duration_ms, amplitude=0.5):
    """Generate a sine wave"""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        value = amplitude * math.sin(2 * math.pi * frequency * t)
        samples.append(int(value * 32767))
    return samples

def generate_square_wave(frequency, duration_ms, amplitude=0.3):
    """Generate a square wave (harsher sound)"""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        value = amplitude if math.sin(2 * math.pi * frequency * t) > 0 else -amplitude
        samples.append(int(value * 32767))
    return samples

def generate_sawtooth_wave(frequency, duration_ms, amplitude=0.4):
    """Generate a sawtooth wave"""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        value = amplitude * (2 * (t * frequency - math.floor(t * frequency + 0.5)))
        samples.append(int(value * 32767))
    return samples

def generate_triangle_wave(frequency, duration_ms, amplitude=0.4):
    """Generate a triangle wave"""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        phase = (t * frequency) % 1.0
        value = amplitude * (4 * abs(phase - 0.5) - 1)
        samples.append(int(value * 32767))
    return samples

def apply_envelope(samples, attack_ms=10, decay_ms=50, sustain_level=0.7, release_ms=100):
    """Apply ADSR envelope to samples"""
    attack_samples = int(SAMPLE_RATE * attack_ms / 1000)
    decay_samples = int(SAMPLE_RATE * decay_ms / 1000)
    release_samples = int(SAMPLE_RATE * release_ms / 1000)
    
    result = []
    for i, sample in enumerate(samples):
        if i < attack_samples:
            # Attack
            envelope = i / attack_samples
        elif i < attack_samples + decay_samples:
            # Decay
            decay_progress = (i - attack_samples) / decay_samples
            envelope = 1.0 - (1.0 - sustain_level) * decay_progress
        elif i < len(samples) - release_samples:
            # Sustain
            envelope = sustain_level
        else:
            # Release
            release_progress = (i - (len(samples) - release_samples)) / release_samples
            envelope = sustain_level * (1.0 - release_progress)
        
        result.append(int(sample * envelope))
    return result

def generate_chord(frequencies, duration_ms, amplitude=0.3):
    """Generate multiple frequencies mixed together"""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    samples = [0] * num_samples
    
    for freq in frequencies:
        for i in range(num_samples):
            t = i / SAMPLE_RATE
            value = (amplitude / len(frequencies)) * math.sin(2 * math.pi * freq * t)
            samples[i] += int(value * 32767)
    
    return samples

def generate_sweep(start_freq, end_freq, duration_ms, amplitude=0.4):
    """Generate a frequency sweep (whoosh effect)"""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        progress = i / num_samples
        freq = start_freq + (end_freq - start_freq) * progress
        value = amplitude * math.sin(2 * math.pi * freq * t)
        samples.append(int(value * 32767))
    return samples

def save_wav(filename, samples):
    """Save samples to a WAV file"""
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(BITS_PER_SAMPLE // 8)
        wav_file.setframerate(SAMPLE_RATE)
        
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', max(-32768, min(32767, sample))))

def main():
    sounds_dir = Path(__file__).parent / "src" / "resources" / "sounds"
    sounds_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating sound files in: {sounds_dir}")
    
    # Define all sounds to generate
    sounds = {
        # Complete sounds
        "complete_chime.wav": lambda: apply_envelope(generate_sine_wave(880, 300)),
        "complete_bell.wav": lambda: apply_envelope(generate_chord([523, 659, 784], 400)),
        "complete_fanfare.wav": lambda: apply_envelope(generate_chord([523, 659, 784, 1047], 500)),
        "complete_ding.wav": lambda: apply_envelope(generate_sine_wave(1047, 200), 5, 30),
        "complete_orchestra.wav": lambda: apply_envelope(generate_chord([262, 330, 392, 523], 600)),
        "complete_harp.wav": lambda: apply_envelope(generate_triangle_wave(659, 500)),
        "complete_synth.wav": lambda: apply_envelope(generate_sweep(400, 1200, 400)),
        
        # Error sounds
        "error_buzz.wav": lambda: generate_square_wave(100, 300, 0.3),
        "error_bonk.wav": lambda: apply_envelope(generate_square_wave(80, 150), 1, 20, 0.5, 80),
        "error_glass.wav": lambda: apply_envelope(generate_chord([1200, 1800, 2400], 200), 1, 150),
        "error_scratch.wav": lambda: generate_sweep(800, 200, 250, 0.3),
        "error_trombone.wav": lambda: generate_sweep(250, 100, 600, 0.4),
        "error_alarm.wav": lambda: generate_square_wave(440, 400, 0.25),
        
        # Achievement sounds
        "achievement_trumpet.wav": lambda: apply_envelope(generate_chord([523, 659, 784], 500)),
        "achievement_levelup.wav": lambda: apply_envelope(generate_sweep(400, 1200, 500)),
        "achievement_sparkle.wav": lambda: apply_envelope(generate_chord([1047, 1319, 1568], 400)),
        "achievement_victory.wav": lambda: apply_envelope(generate_chord([523, 659, 784, 1047], 600)),
        "achievement_coins.wav": lambda: apply_envelope(generate_chord([880, 1047, 1319], 300)),
        
        # Milestone sounds
        "milestone_chime.wav": lambda: apply_envelope(generate_sine_wave(784, 400)),
        "milestone_star.wav": lambda: apply_envelope(generate_chord([1047, 1319, 1568], 350)),
        "milestone_whoosh.wav": lambda: generate_sweep(200, 1200, 400),
        
        # Warning sounds
        "warning_alert.wav": lambda: generate_square_wave(880, 200, 0.3),
        "warning_siren.wav": lambda: generate_sweep(440, 880, 500, 0.3),
        "warning_caution.wav": lambda: generate_square_wave(660, 300, 0.25),
        
        # Start sounds
        "start_engine.wav": lambda: generate_sweep(100, 400, 400, 0.4),
        "start_go.wav": lambda: apply_envelope(generate_chord([440, 554, 659], 300)),
        "start_whoosh.wav": lambda: generate_sweep(200, 800, 300),
        "start_click.wav": lambda: apply_envelope(generate_sine_wave(1200, 50), 1, 20),
        
        # Pause sounds
        "pause_click.wav": lambda: apply_envelope(generate_sine_wave(440, 80), 1, 30),
        "pause_soft.wav": lambda: generate_sweep(600, 300, 200),
        
        # Resume sounds
        "resume_click.wav": lambda: apply_envelope(generate_sine_wave(660, 80), 1, 30),
        "resume_unpause.wav": lambda: generate_sweep(300, 600, 200),
        
        # Stop sounds
        "stop_hard.wav": lambda: generate_square_wave(220, 200, 0.3),
        "stop_brake.wav": lambda: generate_sweep(500, 100, 250),
        
        # Button clicks
        "click_soft.wav": lambda: apply_envelope(generate_sine_wave(800, 40), 1, 15),
        "click_crisp.wav": lambda: apply_envelope(generate_sine_wave(1200, 35), 1, 10),
        "click_pop.wav": lambda: apply_envelope(generate_sine_wave(900, 50), 2, 20),
        "click_tap.wav": lambda: apply_envelope(generate_sine_wave(1000, 45), 1, 15),
        "click_typewriter.wav": lambda: apply_envelope(generate_square_wave(1100, 40), 1, 15),
        "click_bubble.wav": lambda: apply_envelope(generate_chord([800, 1200], 60)),
        
        # Notifications
        "notification_ping.wav": lambda: apply_envelope(generate_sine_wave(1047, 150)),
        "notification_chime.wav": lambda: apply_envelope(generate_chord([880, 1047], 250)),
        "notification_bubble.wav": lambda: apply_envelope(generate_triangle_wave(1200, 200)),
        "notification_bell.wav": lambda: apply_envelope(generate_chord([659, 784, 1047], 300)),
        "notification_dingdong.wav": lambda: apply_envelope(generate_chord([659, 523], 400)),
        
        # Panda sounds
        "panda_munch.wav": lambda: generate_square_wave(200, 150, 0.2),
        "panda_chomp.wav": lambda: generate_square_wave(180, 120, 0.25),
        "panda_nom.wav": lambda: generate_square_wave(220, 100, 0.2),
        "panda_crunch.wav": lambda: generate_square_wave(160, 180, 0.3),
        "panda_slurp.wav": lambda: generate_sweep(300, 600, 200, 0.25),
        
        "panda_chirp.wav": lambda: apply_envelope(generate_sine_wave(1200, 150)),
        "panda_purr.wav": lambda: generate_triangle_wave(150, 300, 0.3),
        "panda_squeal.wav": lambda: apply_envelope(generate_sine_wave(1500, 250)),
        "panda_giggle.wav": lambda: apply_envelope(generate_chord([800, 1000, 1200], 300)),
        
        "panda_whimper.wav": lambda: generate_sweep(400, 200, 400, 0.3),
        "panda_sigh.wav": lambda: generate_sweep(300, 150, 500, 0.25),
        "panda_cry.wav": lambda: generate_sweep(500, 200, 600, 0.3),
        
        "panda_slide.wav": lambda: generate_sweep(400, 200, 300),
        "panda_drag_whoosh.wav": lambda: generate_sweep(300, 800, 250),
        "panda_shuffle.wav": lambda: generate_sawtooth_wave(220, 200, 0.25),
        
        "panda_thud.wav": lambda: generate_sweep(200, 50, 200, 0.5),
        "panda_bounce.wav": lambda: apply_envelope(generate_sine_wave(300, 150)),
        "panda_plop.wav": lambda: generate_sweep(250, 100, 180, 0.4),
        
        "panda_snore.wav": lambda: generate_triangle_wave(120, 600, 0.3),
        "panda_zzz.wav": lambda: generate_sine_wave(100, 500, 0.25),
        "panda_breath.wav": lambda: generate_sweep(80, 120, 800, 0.2),
        
        "panda_wake_yawn.wav": lambda: generate_sweep(200, 400, 500, 0.3),
        "panda_stretch.wav": lambda: generate_sweep(150, 350, 400, 0.3),
        "panda_wake_alert.wav": lambda: apply_envelope(generate_sine_wave(800, 200)),
        
        "panda_boop.wav": lambda: apply_envelope(generate_sine_wave(900, 80)),
        "panda_poke.wav": lambda: apply_envelope(generate_sine_wave(1000, 70)),
        "panda_squeak.wav": lambda: apply_envelope(generate_sine_wave(1400, 100)),
        
        "panda_pet_purr.wav": lambda: generate_triangle_wave(130, 400, 0.3),
        "panda_content.wav": lambda: generate_sine_wave(200, 300, 0.25),
        "panda_relaxed.wav": lambda: generate_triangle_wave(140, 500, 0.25),
        
        "panda_playful.wav": lambda: apply_envelope(generate_chord([600, 800, 1000], 300)),
        "panda_excited.wav": lambda: apply_envelope(generate_chord([800, 1200], 250)),
        "panda_energetic.wav": lambda: apply_envelope(generate_sweep(400, 1000, 300)),
        
        "panda_pitter.wav": lambda: generate_square_wave(400, 100, 0.2),
        "panda_footsteps.wav": lambda: generate_square_wave(350, 150, 0.25),
        "panda_tiptoe.wav": lambda: apply_envelope(generate_sine_wave(600, 80)),
        
        "panda_boing.wav": lambda: apply_envelope(generate_sweep(300, 800, 250)),
        "panda_hop.wav": lambda: apply_envelope(generate_sweep(350, 700, 200)),
        "panda_leap.wav": lambda: apply_envelope(generate_sweep(300, 900, 300)),
        
        "panda_dance_beat.wav": lambda: generate_square_wave(300, 200, 0.3),
        "panda_groove.wav": lambda: generate_chord([300, 400, 500], 250, 0.25),
        "panda_boogie.wav": lambda: apply_envelope(generate_chord([400, 600, 800], 300)),
        
        "panda_achoo.wav": lambda: apply_envelope(generate_sweep(600, 200, 200)),
        "panda_sneeze_loud.wav": lambda: apply_envelope(generate_sweep(700, 150, 250)),
        "panda_atishoo.wav": lambda: apply_envelope(generate_sweep(650, 180, 220)),
        
        "panda_big_yawn.wav": lambda: generate_sweep(250, 450, 600, 0.3),
        "panda_tired_yawn.wav": lambda: generate_sweep(200, 400, 700, 0.25),
        "panda_sleepy_yawn.wav": lambda: generate_sweep(180, 380, 800, 0.25),
    }
    
    # Generate all sound files
    count = 0
    for filename, generator in sounds.items():
        filepath = sounds_dir / filename
        if not filepath.exists():
            print(f"  Generating: {filename}")
            samples = generator()
            save_wav(str(filepath), samples)
            count += 1
        else:
            print(f"  Skipping (exists): {filename}")
    
    print(f"\n✅ Generated {count} new sound files!")
    print(f"Total files in {sounds_dir}: {len(list(sounds_dir.glob('*.wav')))}")

if __name__ == "__main__":
    main()
