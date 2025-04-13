from flask import Flask, render_template, request, jsonify
from src.services.api_client import APIClient
from src.utils.validation_utils import validate_music_prompt
from src.utils.rewrite_prompt import rewrite_music_prompt, record_audio_from_mic, transcribe_speech_to_text
from src.utils.file_utils import save_audio_file, generate_filename

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate-music', methods=['POST'])
def generate_music():
    data = request.json
    mode = data.get('mode', 'text')

    try:
        if mode == 'speech':
            record_audio_from_mic()
            user_input = transcribe_speech_to_text()
        else:
            user_input = data.get('prompt')

        if not user_input:
            return jsonify({"error": "Prompt is required"}), 400

        music_prompt = rewrite_music_prompt(user_input)
        validate_music_prompt(music_prompt)

        api_client = APIClient()
        sounds = api_client.generate_music(music_prompt)

        urls = []
        for idx, sound in enumerate(sounds, start=1):
            file_name = f"static/{generate_filename('generated_music')}"
            save_audio_file(sound["data"], file_name, sound["audioContainer"].lower())
            urls.append(f"/{file_name}")

        return jsonify({"music_urls": urls})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
