"""
Local Bangla-English transcription using faster-whisper (CPU).
Uses the same Whisper large-v3 model but runs LOCALLY without
Groq's speed-optimized shortcuts that destroy accuracy.
"""


from faster_whisper import WhisperModel
import os

def run_local_whisper(audio_path, language_code="bn", keywords=None):
    from faster_whisper import WhisperModel
    import os
    
    model_size = "large-v3"
    print(f"Loading Whisper {model_size} model on CPU (int8 quantized)...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    print(f"Transcribing: {audio_path}")
    print("Processing on CPU...\n")
    
    kwargs = {
        "beam_size": 5,
        "best_of": 5,
        "temperature": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],  # Enables temperature fallback to break loops
        "condition_on_previous_text": False,
        "vad_filter": True,
        "vad_parameters": dict(min_silence_duration_ms=500),
        "repetition_penalty": 1.2,           # Heavily penalizes looping text
        "no_repeat_ngram_size": 3,           # Prevents exact phrase repetition
        "compression_ratio_threshold": 2.4   # Helps trigger fallback if output becomes repetitive garbage
    }
    
    if language_code:
        kwargs["language"] = language_code
        
    prompt = ""
    if language_code == "bn":
        # Using a mixed-language Bengali/English prompt helps the model understand code-switching
        prompt = "এটি একটি বাংলাদেশি অফিস মিটিং। collection, adjust, MPO, dipo, practice, daily basis, message, amount, taka ইত্যাদি নিয়ে আলোচনা হচ্ছে।"
    if keywords:
        prompt += f" Keywords: {keywords}"
        
    if prompt:
        kwargs["initial_prompt"] = prompt

    segments, info = model.transcribe(audio_path, **kwargs)
    
    print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})\n")
    
    results = []
    full_text = []
    for segment in segments:
        line = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text.strip()}"
        print(line)
        full_text.append(segment.text.strip())
        results.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
    
    return " ".join(full_text)

if __name__ == "__main__":
    pass
