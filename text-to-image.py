from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import random
from IPython.display import display
import os
from dotenv import load_dotenv

load_dotenv()

user_prompt = "floating sky island nature"

def enhance_prompt(user_prompt):
    """Enhances the user's prompt for better image generation results."""
    keywords_3d = ["3D render", "octane render", "ray traced", "highly detailed", "8k resolution"]
    keywords_cozy = ["warm lighting", "soft textures", "comfortable"]
    keywords_meditative = ["serene", "peaceful", "tranquil", "calm", "minimalism", "natural light", "meditation", "zen"]
    keywords_style = ["artstation trending", "Greg Rutkowski", "artgerm"]

    num_keywords = 3

    enhanced_prompt = user_prompt + ", "
    enhanced_prompt += ", ".join(random.sample(keywords_3d, min(num_keywords, len(keywords_3d)))) + ", "
    enhanced_prompt += ", ".join(random.sample(keywords_cozy, min(num_keywords, len(keywords_cozy)))) + ", "
    enhanced_prompt += ", ".join(random.sample(keywords_meditative, min(num_keywords, len(keywords_meditative)))) + ", "
    enhanced_prompt += ", ".join(random.sample(keywords_style, min(num_keywords, len(keywords_style))))

    return enhanced_prompt

# make user prompt better
client = genai.Client(api_key=os.getenv("API_KEY"))

# generate text
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[f"Refine and enhance the following user-provided scene description to create a highly detailed and evocative prompt suitable for a state-of-the-art image generation AI like Imagen 3. Make the middle of the scene a vast, open relaxing area where a person could sit and meditate BUT DONT PLACE A PERSON THERE. Focus on elements that will create a rich and immersive meditative experience. Consider details related to lighting, atmosphere, sensory details (visual, auditory, and even subtle tactile or olfactory hints if appropriate), artistic style, and overall mood. Ensure the prompt is specific and avoids ambiguity. DO NOT GIVE ME ANYTHING ELSE, JUST THE PROMPT TO FEED INTO THE IMAGE MODEL, DO NOT SAY OK HERE'S YOUR PROMPT OR WHY ITS EFFECTIVE OR  CONSIDERATIONS JUST GIVE ME THE PROMPT TO FEED INTO THE OTHER MODEL. nUser's Initial Scene: {user_prompt}"]
)
filler_response = response.text

# add tags
image_prompt = enhance_prompt(filler_response)
print(image_prompt)

# generate image
response = client.models.generate_images(
    model='imagen-3.0-generate-002',
    prompt=image_prompt,
    config=types.GenerateImagesConfig(
        number_of_images= 1,
        aspect_ratio='16:9',
        personGeneration="DONT_ALLOW",
    )
)


generated_image = response.generated_images[0]
image_bytes = generated_image.image.image_bytes
image = Image.open(BytesIO(image_bytes))
# image.save("generated_image.png")  # Save the image
# display(Image.open("generated_image.png")) # Display the saved image
image.show()
