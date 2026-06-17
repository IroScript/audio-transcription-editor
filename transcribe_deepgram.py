import os
import requests

def run_deepgram(audio_path, language_code=None, keywords=None):
    # Read API key from environment or local .env
    api_key = os.environ.get('DEEPGRAM_API_KEY')
    if not api_key:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('DEEPGRAM_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break

    if not api_key:
        raise ValueError("Deepgram API key not found in .env")

    print(f"Transcribing: {audio_path}")
    print("Using Deepgram API...\n")
    
    url = "https://api.deepgram.com/v1/listen"
    
    params = {
        "model": "nova-3",
        "smart_format": "true"
    }
    
    if language_code:
        params["language"] = language_code
        
    if keywords:
        params["keyterm"] = [k.strip() for k in keywords.split(',') if k.strip()]

    headers = {
        "Authorization": f"Token {api_key}"
    }

    with open(audio_path, "rb") as audio_file:
        response = requests.post(url, params=params, headers=headers, data=audio_file)

    if response.status_code != 200:
        raise Exception(f"Deepgram API Error: {response.status_code} - {response.text}")

    result = response.json()
    try:
        text = result['results']['channels'][0]['alternatives'][0]['transcript']
        return text
    except KeyError:
        return str(result)

if __name__ == "__main__":
    pass
