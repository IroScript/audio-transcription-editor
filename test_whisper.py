from faster_whisper import WhisperModel

audio_path = "Jun 11 at 1-25 PM_cut_0-60_cleaned.wav"
print("Loading model...")
model = WhisperModel("large-v3", device="cpu", compute_type="int8")

configs = [
    {
        "name": "1. No prompt, VAD True, condition False",
        "kwargs": {
            "language": "bn",
            "beam_size": 5,
            "condition_on_previous_text": False,
            "vad_filter": True,
            "vad_parameters": dict(min_silence_duration_ms=500)
        }
    },
    {
        "name": "2. No prompt, VAD False, condition False",
        "kwargs": {
            "language": "bn",
            "beam_size": 5,
            "condition_on_previous_text": False,
            "vad_filter": False,
        }
    },
    {
        "name": "3. No prompt, VAD True, condition False, repetition_penalty=1.2",
        "kwargs": {
            "language": "bn",
            "beam_size": 5,
            "condition_on_previous_text": False,
            "vad_filter": True,
            "vad_parameters": dict(min_silence_duration_ms=500),
            "repetition_penalty": 1.2
        }
    },
    {
        "name": "4. No prompt, VAD True, condition False, no_repeat_ngram_size=3",
        "kwargs": {
            "language": "bn",
            "beam_size": 5,
            "condition_on_previous_text": False,
            "vad_filter": True,
            "vad_parameters": dict(min_silence_duration_ms=500),
            "no_repeat_ngram_size": 3
        }
    },
    {
        "name": "5. Prompt English, condition True, VAD False (Original setup roughly)",
        "kwargs": {
            "language": "bn",
            "beam_size": 5,
            "condition_on_previous_text": True,
            "vad_filter": False,
            "initial_prompt": "This is a Bangladeshi office meeting. collection, adjust, MPO, dipo, practice, daily basis, message, amount, taka. How much money did they collect? It's a daily practice."
        }
    }
]

for config in configs:
    print(f"\n--- Running: {config['name']} ---")
    try:
        segments, info = model.transcribe(audio_path, **config['kwargs'])
        texts = []
        for segment in segments:
            texts.append(segment.text.strip())
        print(" ".join(texts))
    except Exception as e:
        print(f"Failed: {e}")

