import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def rewrite_music_prompt(user_input: str) -> str:
    """
    Enhances a user's raw input into a detailed prompt for AI music generation.
    """
    prompt = f"""
    Take the following user input describing their mood or intention and turn it into a single liner vivid prompt for generating relaxing music using an AI music model. 
    Be specific about instruments, tempo, atmosphere, and emotion.

    User input: "{user_input}"
    Enhanced music prompt:
    """
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text.strip()


if __name__ == "__main__":
    user_input = input("Enter your mood or what you'd like to feel in the music: ")
    enhanced_prompt = rewrite_music_prompt(user_input)
    print("\nEnhanced music prompt:\n", enhanced_prompt)