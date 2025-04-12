import time
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from IPython import display

# Import functions from text-to-image.py
# Assuming the refactored file is named text_to_image.py (with underscore to follow Python conventions)
from text_to_image import generate_text_prompt, enhance_prompt, generate_image, save_and_display_image

load_dotenv()

def generate_video_from_image(client, image_response):
    """
    Generates videos from an image using Google's Veo model.
    
    Args:
        client: Google Generative AI client
        image_response: Response from Imagen image generation
    
    Returns:
        List of filenames of saved videos
    """
    # Extract the image from the image_response
    if not hasattr(image_response, 'generated_images') or not image_response.generated_images:
        print("No image available to generate video from")
        return []
    
    generated_image = image_response.generated_images[0]
    
    if not hasattr(generated_image, 'image') or not hasattr(generated_image.image, 'image_bytes'):
        print("Image object does not have expected attributes")
        return []
    
    # Initialize operation for video generation
    operation = client.models.generate_videos(
        model="veo-2.0-generate-001",
        prompt="using the image scene to create a video of panning left and right over the scene",
        image=generated_image.image,  # Pass the generated image object directly
        config=types.GenerateVideosConfig(
            aspect_ratio="16:9",  # "16:9" or "9:16"
            number_of_videos=1,
        ),
    )
    
    print("Video generation initiated. Waiting for completion...")
    
    # Wait for videos to generate
    while not operation.done:
        time.sleep(20)
        operation = client.operations.get(operation)

    for n, generated_video in enumerate(operation.result.generated_videos):
        fname = f'with_image_input{n}.mp4'
        print(fname)
        # generated_video.video.save(fname)
        display(generated_video.video.show())
    
    return None

def main():
    # User prompt for image generation
    user_prompt = "floating sky island nature"
    
    # Initialize client
    client = genai.Client(api_key=os.getenv("API_KEY"))
    
    # Generate text prompt
    print("Generating text prompt...")
    text_prompt = generate_text_prompt(client, user_prompt)
    
    if text_prompt:
        print("Text prompt generated successfully.")
        
        # Enhance the prompt
        image_prompt = enhance_prompt(text_prompt)
        print("Enhanced prompt for image generation.")
        
        # Generate image
        print("Generating image...")
        image_response = generate_image(client, image_prompt)
        
        if image_response:
            print("Image generated successfully.")
            
            # Save the image (optional)
            save_and_display_image(image_response)
            
            # Generate videos from the image
            print("Starting video generation process...")
            generate_video_from_image(client, image_response)
            
            # if video_files:
            #     print(f"Video generation complete. Generated {len(video_files)} videos:")
            #     for file in video_files:
            #         print(f"- {file}")
            # else:
            #     print("Video generation failed or produced no videos.")
        else:
            print("Failed to generate image. Cannot proceed to video generation.")
    else:
        print("Failed to generate text prompt. Process aborted.")

if __name__ == "__main__":
    main()