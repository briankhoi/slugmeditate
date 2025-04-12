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

    num_keywords = 3

    enhanced_prompt = user_prompt + ", "
    enhanced_prompt += ", ".join(random.sample(keywords_3d, min(num_keywords, len(keywords_3d)))) + ", "
    enhanced_prompt += ", ".join(random.sample(keywords_cozy, min(num_keywords, len(keywords_cozy)))) + ", "
    enhanced_prompt += ", ".join(random.sample(keywords_meditative, min(num_keywords, len(keywords_meditative)))) + ", "
    # enhanced_prompt = "" + enhanced_prompt
    return enhanced_prompt

# Initialize client
client = genai.Client(api_key=os.getenv("API_KEY"))

# Generate text prompt
try:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[f"REQUIRED: THE POV/CAMERA IS SITTING IN THE MIDDLE OF A LANDSCAPE WITH 90 DEGREES FIELD OF VIEW. NOT AN OVERHEAD SHOT OF THE SCENE BUT THE PERSPECTIVE OF SITTING DIRECTLY IN THE SCENE 90 DEGREES FIELD OF VIEW. DO NOT INCLUDE ANY PEOPLE INSIDE OF THE IMAGE. do not include asterisks in your prompt or any colons, just normal characters. Refine and enhance the following user-provided scene description to create a highly detailed and evocative prompt suitable for a state-of-the-art image generation AI like Imagen 3. Make the middle of the scene a vast, open relaxing area where a person could sit and meditate BUT DONT PLACE A PERSON THERE. REQUIRED: The scene should be the PERSPECTIVE of a person sitting in the middle with a 90 degree field of view. Focus on elements that will create a rich and immersive meditative experience. Consider details related to lighting, atmosphere, sensory details (visual, auditory, and even subtle tactile or olfactory hints if appropriate), artistic style, and overall mood. Ensure the prompt is specific and avoids ambiguity. DO NOT GIVE ME ANYTHING ELSE, JUST THE PROMPT TO FEED INTO THE IMAGE MODEL, DO NOT SAY OK HERE'S YOUR PROMPT OR WHY ITS EFFECTIVE OR  CONSIDERATIONS JUST GIVE ME THE PROMPT TO FEED INTO THE OTHER MODEL. \nUser's Initial Scene: {user_prompt}"]
    )
    filler_response = response.text
    print("Text prompt generated successfully:")
    print(filler_response)
except Exception as e:
    print(f"Error generating text prompt: {e}")
    exit(1)

# Enhance the prompt
image_prompt = enhance_prompt(filler_response)
print("\nFinal image prompt:")
print(image_prompt)

# Generate image
try:
    print("\nGenerating image...")
    image_response = client.models.generate_images(
        model='imagen-3.0-generate-002',
        prompt=image_prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio='16:9',
            personGeneration="DONT_ALLOW",
        )
    )
    
    # Debug information
    print(f"Response type: {type(image_response)}")
    print(f"Response attributes: {dir(image_response)}")
    
    # Check if generated_images exists and has elements
    if hasattr(image_response, 'generated_images') and image_response.generated_images:
        print(f"Number of generated images: {len(image_response.generated_images)}")
        
        generated_image = image_response.generated_images[0]
        print(f"Image object attributes: {dir(generated_image)}")
        
        if hasattr(generated_image, 'image') and hasattr(generated_image.image, 'image_bytes'):
            image_bytes = generated_image.image.image_bytes
            image = Image.open(BytesIO(image_bytes))
            image.save("generated_image.png")  # Save the image
            print("Image saved successfully as 'generated_image.png'")
            display(Image.open("generated_image.png")) # Display the saved image
            image.show()
        else:
            print("Image object does not have expected 'image' or 'image_bytes' attributes")
    else:
        print("No generated images found in response")
        print("Full response:", image_response)
except Exception as e:
    print(f"Error generating image: {e}")
    import traceback
    traceback.print_exc()