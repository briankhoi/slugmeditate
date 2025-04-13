from src.services.api_client import APIClient
from src.utils.file_utils import generate_filename, save_audio_file
from src.utils.validation_utils import validate_music_prompt
from src.utils.rewrite_prompt import rewrite_music_prompt, record_audio_from_mic, transcribe_speech_to_text

def main():
    """
    Main function to run the Google Music FX application.
    Prompts the user for input, generates music, and saves the audio files.
    
    Handles exceptions and provides user feedback.
    """
    try:
        api_client = APIClient()
        input_mode = input("Would you like to [t]ype or [s]peak your prompt? (t/s): ").strip().lower()

        if input_mode == 's':
            record_audio_from_mic()
            user_input = transcribe_speech_to_text()
            print(f"Transcribed text: {user_input}")
        else:
            user_input = input("Please enter how you're feeling or what vibe you want the music to reflect: ")

        music_prompt = rewrite_music_prompt(user_input)
        print("\nEnhanced music prompt:\n", music_prompt)
        validate_music_prompt(music_prompt)
        
        sounds = api_client.generate_music(music_prompt)
        
        for idx, sound in enumerate(sounds, start=1):
            file_name = f"static/{generate_filename('generated_music')}"
            save_audio_file(sound["data"], file_name, sound["audioContainer"].lower())
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()