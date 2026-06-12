import noisereduce as nr
import soundfile as sf
import os
from pedalboard import Pedalboard, Compressor, HighpassFilter, LowpassFilter, NoiseGate, PeakFilter, Gain

def enhance_audio(input_path, output_path, start_sec=None, end_sec=None):
    import tempfile
    import subprocess
    import imageio_ffmpeg
    
    print(f"Loading {input_path} (supporting all formats via ffmpeg)...")
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    temp_wav = os.path.join(tempfile.gettempdir(), "temp_enhance.wav")
    
    # Convert any audio to wav directly using the embedded ffmpeg
    cmd = [ffmpeg_exe, "-y", "-i", input_path]
    
    if start_sec is not None and end_sec is not None:
        # Cut using ffmpeg directly to save RAM and time!
        duration = end_sec - start_sec
        cmd.extend(["-ss", str(start_sec), "-t", str(duration)])
        
    cmd.append(temp_wav)
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # Read the wav using soundfile
    data, rate = sf.read(temp_wav)
    os.remove(temp_wav)
    
    # Transpose if stereo: soundfile reads as (samples, channels), nr expects (channels, samples)
    if len(data.shape) > 1:
        data = data.T

    print("Step 1: Performing mild Spectral Gating Noise Reduction...")
    # prop_decrease=0.6 keeps some natural background noise but prevents ALL robotic artifacts
    reduced_noise = nr.reduce_noise(y=data, sr=rate, prop_decrease=0.6, stationary=True)
    
    print("Step 2: Applying EQ and Compression...")
    # Build a mastering chain
    board = Pedalboard([
        # 1. Remove extreme low rumble and extreme high frequency hiss
        HighpassFilter(cutoff_frequency_hz=80),
        LowpassFilter(cutoff_frequency_hz=8000),
        
        # 3. Equalizer (EQ) for Clarity:
        # Bass boost (warmth/body)
        PeakFilter(cutoff_frequency_hz=150, gain_db=5.0, q=1.0),
        # Vocal presence boost
        PeakFilter(cutoff_frequency_hz=2500, gain_db=5.0, q=1.0),
        # Treble boost (crispness/clarity)
        PeakFilter(cutoff_frequency_hz=5000, gain_db=6.0, q=1.0),
        
        # 4. Dynamic Range Compression: Make quiet voices loud
        Compressor(threshold_db=-25.0, ratio=3.0, attack_ms=10.0, release_ms=100.0),
        
        # 5. Gain: Add volume makeup
        Gain(gain_db=15.0)
    ])
    
    # Process audio through the pedalboard chain
    # Pedalboard expects (channels, samples)
    if len(reduced_noise.shape) == 1:
        reduced_noise = reduced_noise.reshape(1, -1)
        
    enhanced_audio = board(reduced_noise, rate)
    
    # Transpose back before saving
    if len(enhanced_audio.shape) > 1 and enhanced_audio.shape[0] < enhanced_audio.shape[1]:
        enhanced_audio = enhanced_audio.T
        
    sf.write(output_path, enhanced_audio, rate, subtype='PCM_16')
    print(f"Success! Highly Enhanced audio saved to {output_path}")

if __name__ == "__main__":
    base_dir = r"c:\Users\Irak\Desktop\Audio"
    input_file = os.path.join(base_dir, "audio_clip.wav")
    output_file = os.path.join(base_dir, "cleaned_clip.wav")
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
    else:
        enhance_audio(input_file, output_file)
