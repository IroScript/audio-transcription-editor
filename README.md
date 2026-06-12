# Audio Transcription Engine & Editor

An Audacity-like visual waveform editor and transcription utility built in Python (Tkinter). It allows you to visualize audio, crop specific regions visually (zooming/panning), clean background noise, and transcribe using local CPU models (Faster-Whisper) or cloud services (Groq, ElevenLabs).

## Features
- **Visual Waveform Editor**: Load large audio files, zoom (Ctrl + Mouse Wheel), and pan (Right-Click Drag or Shift + Mouse Wheel).
- **Audio Clean-up**: Background noise reduction and optimization (using `pedalboard` & `noisereduce`).
- **CPU-Optimized Transcription**:
  - Local Whisper (Faster-Whisper on CPU)
  - Groq Whisper Cloud API
  - ElevenLabs Scribe API
- **Cropping & Exporting**: Select a range and transcribe only the cropped segment. Option to delete temporary clips afterwards.

## Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Audio
   ```

2. **Install dependencies**:
   Make sure you have Python 3.10+ and `ffmpeg` installed on your system. Then run:
   ```bash
   pip install -r requirements.txt
   ```
   *(Ensure libraries like `pygame`, `matplotlib`, `numpy`, `soundfile`, `pedalboard`, `noisereduce`, `faster-whisper`, `groq`, `elevenlabs`, and `imageio-ffmpeg` are installed).*

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory and add your API keys:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```

4. **Run the Application**:
   ```bash
   python transcribe_gui.py
   ```
