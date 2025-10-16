#!/usr/bin/env python3
"""
Run Character Image Pipeline with Google Search
"""

from character_image_pipeline import process_character_pipeline

def main():
    # Search for images and process them through the full pipeline
    character_name = "charlie kirk"  # Change this to any character you want
    
    print(f"🎭 Running Character Image Pipeline with Google Search")
    print(f"Character: {character_name}")
    print("=" * 60)
    
    # This will:
    # 1. Search Google for images of the character
    # 2. Download them to downloaded_images folder
    # 3. Process them through the full pipeline (face detection, cropping, outpainting)
    # 4. Generate character sprites
    process_character_pipeline(
        character_name=character_name, 
        use_google_search=True
    )

if __name__ == "__main__":
    main()
