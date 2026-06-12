import os
import sys
import io

# Ensure stdout handles utf-8 properly

def run_elevenlabs(audio_path, language_code=None, keywords=None):
    from elevenlabs.client import ElevenLabs
    import os
    
    # NOTE: mostly accurate
    # Read API key from environment or local .env
    api_key = os.environ.get('ELEVENLABS_API_KEY')
    if not api_key:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('ELEVENLABS_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break

    # Initialize the client
    client = ElevenLabs(api_key=api_key)

    print(f"Transcribing: {audio_path}")
    print("Using ElevenLabs Scribe API...\n")
    
    # Prepare kwargs
    kwargs = {"model_id": "scribe_v2"}
    if language_code:
        kwargs["language_code"] = language_code
    if keywords:
        # Currently, ElevenLabs doesn't have a direct 'keywords' param in python SDK docs shown,
        # but we'll try to add it if they support it, or leave it out if they don't.
        # It's actually 'keyterms' in scribe_v2
        kwargs["keyterms"] = [k.strip() for k in keywords.split(',') if k.strip()]

    with open(audio_path, "rb") as audio_file:
        result = client.speech_to_text.convert(file=audio_file, **kwargs)

    return result.text

if __name__ == "__main__":
    pass
