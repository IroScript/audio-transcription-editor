

import os
from groq import Groq

def run_groq(audio_path, language_code=None, keywords=None):
    import os
    from groq import Groq
    
    # Read API key from environment or local .env
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('GROQ_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break

    client = Groq(api_key=api_key)

    print(f"Transcribing: {audio_path}")
    print(f"Model: whisper-large-v3-turbo")
    print(f"Using Groq Python SDK...\n")
    
    kwargs = {
        "model": "whisper-large-v3-turbo",
        "temperature": 0,
        "response_format": "verbose_json"
    }
    
    if language_code:
        kwargs["language"] = language_code
        
    prompt = ""
    if language_code == "bn":
        prompt = "This is a Bangladeshi office meeting in Bengali and English. Common words: collection, adjust, MPO, dipo, practice, daily basis, message, amount, taka, collection, how much money did they collect?"
    if keywords:
        prompt += f" Keywords: {keywords}"
    
    if prompt:
        kwargs["prompt"] = prompt

    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), file.read()),
            **kwargs
        )

    return transcription.text

if __name__ == "__main__":
    pass
