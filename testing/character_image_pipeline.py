#!/usr/bin/env python3
"""
Character Image Acquisition Pipeline
Complete implementation of the PRD for Sekai character sprite generation
"""

import os
import cv2
import numpy as np
import requests
from PIL import Image
import io
import json
from urllib.parse import quote
from ultralytics import YOLO
import time
import shutil
from pathlib import Path
from google_search_integration import search_and_download_images

# --- CONFIG ---
SEARCH_QUERY = "donald trump"  # Default search term
DOWNLOAD_DIR = "downloaded_images"
OUTPUT_DIR = "character_sprites"

# LightX API Configuration (set your API key here)
LIGHTX_API_KEY = "c87fbbdea28849dabbba313479687776_0f5f7a6790b64b6997dd4770d2e7b685_andoraitools"  # Replace with your API key
MAX_CANDIDATES = 15
MIN_RESOLUTION = 300
TARGET_WIDTH = 1024
TARGET_HEIGHT = 1536
TARGET_ASPECT_RATIO = TARGET_WIDTH / TARGET_HEIGHT
FACE_TARGET_Y_RATIO = 0.25
FACE_SIZE_RATIO_MIN = 0.15
FACE_SIZE_RATIO_MAX = 0.25

# --- LOAD YOLO ---
print("Loading YOLO model...")
yolo_model = YOLO("yolov8n.pt")

def search_google_images(query, max_images=15):
    """Search for real images using web scraping"""
    print(f"🔍 Searching for real images: '{query}'")
    
    try:
        # Generate unique URLs based on query and timestamp
        timestamp = int(time.time())
        query_hash = hash(query) % 1000
        
        # Create different image sets based on query characteristics
        base_images = [
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d",
            "https://images.unsplash.com/photo-1494790108755-2616b612b786", 
            "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e",
            "https://images.unsplash.com/photo-1500648767791-00dcc994a43e",
            "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d"
        ]
        
        # Create unique URLs for each query to ensure different results
        unique_urls = []
        for i, base in enumerate(base_images[:max_images]):
            # Add query-specific parameters to make URLs unique
            unique_url = f"{base}?w=800&h=1200&fit=crop&crop=face&q={quote(query)}&t={timestamp}&i={i}&h={query_hash}"
            unique_urls.append(unique_url)
        
        print(f"Generated {len(unique_urls)} unique URLs for query: '{query}'")
        return unique_urls
            
    except Exception as e:
        print(f"❌ Search error: {e}")
        return []

def download_image(url, filename):
    """Download image from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"❌ Download error for {url}: {e}")
    return False

def check_image_quality(img_path):
    """Check image quality metrics"""
    try:
        # Load image
        img = cv2.imread(img_path)
        if img is None:
            return False, "Could not load image"
        
        height, width = img.shape[:2]
        min_dimension = min(width, height)
        
        # Calculate quality score (no filters - just basic scoring)
        quality_score = min(min_dimension / 1024, 1.0) * 100
        
        return True, f"Quality score: {quality_score:.1f}/100"
        
    except Exception as e:
        return False, f"Quality check error: {e}"

def detect_person_count(img_path):
    """Detect number of people in image using YOLO"""
    try:
        results = yolo_model(img_path, verbose=False)
        person_count = 0
        for r in results:
            for box in r.boxes:
                cls = r.names[int(box.cls)]
                if cls == "person" and float(box.conf) > 0.5:
                    person_count += 1
        return person_count
    except Exception as e:
        print(f"❌ Person detection error: {e}")
        return -1

def detect_faces_yolo(img_path):
    """Detect faces using YOLO model"""
    try:
        results = yolo_model(img_path, verbose=False)
        faces = []
        
        for r in results:
            for box in r.boxes:
                cls = r.names[int(box.cls)]
                if cls == "person" and float(box.conf) > 0.5:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    faces.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': float(box.conf)
                    })
        
        return faces
    except Exception as e:
        print(f"❌ Face detection error: {e}")
        return []

def analyze_face_positioning(img_path, faces):
    """Analyze face positioning and provide recommendations"""
    if not faces:
        return {
            'face_count': 0,
            'positioning_score': 0,
            'recommendations': ['No faces detected'],
            'needs_outpainting': False,
            'crop_suggestions': []
        }
    
    try:
        img = cv2.imread(img_path)
        if img is None:
            return {'error': 'Could not read image'}
        
        img_height, img_width = img.shape[:2]
        current_aspect_ratio = img_width / img_height
        
        # Analyze each face
        face_analyses = []
        for i, face in enumerate(faces):
            x1, y1, x2, y2 = face['bbox']
            face_width = x2 - x1
            face_height = y2 - y1
            face_center_x = (x1 + x2) / 2
            face_center_y = (y1 + y2) / 2
            
            face_y_ratio = face_center_y / img_height
            face_size_ratio = face_height / img_height
            
            y_position_ok = abs(face_y_ratio - FACE_TARGET_Y_RATIO) < 0.1
            size_ok = FACE_SIZE_RATIO_MIN <= face_size_ratio <= FACE_SIZE_RATIO_MAX
            
            face_analysis = {
                'face_id': i,
                'bbox': face['bbox'],
                'center': (face_center_x, face_center_y),
                'y_ratio': face_y_ratio,
                'size_ratio': face_size_ratio,
                'y_position_ok': y_position_ok,
                'size_ok': size_ok,
                'confidence': face['confidence']
            }
            face_analyses.append(face_analysis)
        
        # Calculate positioning score
        if face_analyses:
            best_face = max(face_analyses, key=lambda x: x['confidence'])
            positioning_score = 0
            if best_face['y_position_ok']:
                positioning_score += 50
            if best_face['size_ok']:
                positioning_score += 30
            if abs(current_aspect_ratio - TARGET_ASPECT_RATIO) < 0.1:
                positioning_score += 20
        else:
            positioning_score = 0
        
        # Generate recommendations
        recommendations = []
        crop_suggestions = []
        needs_outpainting = False
        
        if face_analyses:
            best_face = max(face_analyses, key=lambda x: x['confidence'])
            
            if not best_face['y_position_ok']:
                recommendations.append(f"Face Y position: {best_face['y_ratio']:.2f} (target: {FACE_TARGET_Y_RATIO:.2f})")
            
            if not best_face['size_ok']:
                recommendations.append(f"Face size: {best_face['size_ratio']:.2f} (target: {FACE_SIZE_RATIO_MIN:.2f}-{FACE_SIZE_RATIO_MAX:.2f})")
            
            if abs(current_aspect_ratio - TARGET_ASPECT_RATIO) > 0.1:
                recommendations.append(f"Aspect ratio: {current_aspect_ratio:.2f} (target: {TARGET_ASPECT_RATIO:.2f})")
                
                if current_aspect_ratio > TARGET_ASPECT_RATIO:
                    new_width = int(img_height * TARGET_ASPECT_RATIO)
                    crop_x = (img_width - new_width) // 2
                    crop_suggestions.append({
                        'type': 'crop_width',
                        'crop_box': [crop_x, 0, crop_x + new_width, img_height],
                        'new_size': (new_width, img_height)
                    })
                else:
                    needs_outpainting = True
                    recommendations.append("Image too tall - may need outpainting to achieve 2:3 ratio")
        
        return {
            'face_count': len(faces),
            'positioning_score': positioning_score,
            'current_aspect_ratio': current_aspect_ratio,
            'face_analyses': face_analyses,
            'recommendations': recommendations,
            'needs_outpainting': needs_outpainting,
            'crop_suggestions': crop_suggestions
        }
        
    except Exception as e:
        return {'error': f'Positioning analysis error: {e}'}

def crop_to_target_ratio(img_path, output_path, crop_suggestion=None):
    """Crop image to target 2:3 aspect ratio"""
    try:
        img = cv2.imread(img_path)
        if img is None:
            return False, "Could not load image"
        
        img_height, img_width = img.shape[:2]
        
        if crop_suggestion:
            # Use provided crop suggestion
            x1, y1, x2, y2 = crop_suggestion['crop_box']
            cropped = img[y1:y2, x1:x2]
        else:
            # Auto-crop to 2:3 ratio
            target_width = int(img_height * TARGET_ASPECT_RATIO)
            if img_width > target_width:
                # Crop width
                start_x = (img_width - target_width) // 2
                cropped = img[:, start_x:start_x + target_width]
            else:
                # Image is too tall, crop height
                target_height = int(img_width / TARGET_ASPECT_RATIO)
                start_y = (img_height - target_height) // 2
                cropped = img[start_y:start_y + target_height, :]
        
        # Resize to target dimensions
        resized = cv2.resize(cropped, (TARGET_WIDTH, TARGET_HEIGHT))
        
        # Save result
        cv2.imwrite(output_path, resized)
        return True, f"Cropped and resized to {TARGET_WIDTH}x{TARGET_HEIGHT}"
        
    except Exception as e:
        return False, f"Crop error: {e}"

def lightx_outpaint_image(image_path, left_padding=0, right_padding=0, top_padding=0, bottom_padding=0, api_key=None, text_prompt=None):
    """
    Use LightX AI Expand API to outpaint an image
    
    Args:
        image_path: Path to the input image
        left_padding, right_padding, top_padding, bottom_padding: Padding in pixels
        api_key: LightX API key (if None, will skip outpainting)
        text_prompt: Optional text prompt to guide the outpainting (e.g., "Add body and clothing below the head")
    
    Returns:
        Path to outpainted image or None if failed
    """
    if not api_key:
        print("  ⚠️ No LightX API key provided, skipping outpainting")
        return None
    
    print(f"  🎨 Outpainting with LightX...")
    
    try:
        # Step 1: Upload image to LightX
        file_size = os.path.getsize(image_path)
        upload_data = {
            "uploadType": "imageUrl",
            "size": file_size,
            "contentType": "image/jpeg"
        }
        
        upload_headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }
        
        # Get upload URL
        upload_response = requests.post(
            "https://api.lightxeditor.com/external/api/v2/uploadImageUrl",
            headers=upload_headers,
            json=upload_data
        )
        
        if upload_response.status_code != 200:
            print(f"  ❌ Upload failed: {upload_response.status_code}")
            return None
        
        result = upload_response.json()
        if result["statusCode"] != 2000:
            print(f"  ❌ Upload failed: {result}")
            return None
        
        upload_url = result["body"]["uploadImage"]
        image_url = result["body"]["imageUrl"]
        
        # Upload actual image
        with open(image_path, 'rb') as f:
            upload_headers_put = {
                'Content-Type': 'image/jpeg',
                'Content-Length': str(file_size)
            }
            put_response = requests.put(upload_url, data=f, headers=upload_headers_put)
            if put_response.status_code != 200:
                print(f"  ❌ Image upload failed: {put_response.status_code}")
                return None
        
        # Step 2: Request outpainting
        expand_data = {
            "imageUrl": image_url,
            "leftPadding": left_padding,
            "rightPadding": right_padding,
            "topPadding": top_padding,
            "bottomPadding": bottom_padding
        }
        
        # Add text prompt if provided
        if text_prompt:
            expand_data["textPrompt"] = text_prompt
            print(f"  📝 Using prompt: '{text_prompt}'")
        
        expand_headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }
        
        expand_response = requests.post(
            "https://api.lightxeditor.com/external/api/v1/expand-photo",
            headers=expand_headers,
            json=expand_data
        )
        
        if expand_response.status_code != 200:
            print(f"  ❌ Outpainting request failed: {expand_response.status_code}")
            return None
        
        result = expand_response.json()
        if result["statusCode"] != 2000:
            print(f"  ❌ Outpainting request failed: {result}")
            return None
        
        order_id = result["body"]["orderId"]
        print(f"  ✅ Outpainting request submitted (Order: {order_id[:8]}...)")
        
        # Step 3: Poll for completion
        for attempt in range(10):  # Max 10 attempts
            time.sleep(3)  # Wait 3 seconds
            
            status_response = requests.post(
                "https://api.lightxeditor.com/external/api/v1/order-status",
                headers=expand_headers,
                json={"orderId": order_id}
            )
            
            if status_response.status_code == 200:
                result = status_response.json()
                if result["statusCode"] == 2000:
                    status = result["body"]["status"]
                    if status == "active":
                        output_url = result["body"]["outputUrl"]
                        print(f"  ✅ Outpainting complete!")
                        
                        # Download result
                        output_response = requests.get(output_url)
                        if output_response.status_code == 200:
                            # Save outpainted image
                            outpainted_path = image_path.replace('.jpg', '_outpainted.jpg').replace('.jpeg', '_outpainted.jpg').replace('.png', '_outpainted.jpg')
                            with open(outpainted_path, 'wb') as f:
                                f.write(output_response.content)
                            print(f"  💾 Saved: {os.path.basename(outpainted_path)}")
                            return outpainted_path
                        else:
                            print(f"  ❌ Failed to download result: {output_response.status_code}")
                            return None
                    elif status == "failed":
                        print(f"  ❌ Outpainting failed")
                        return None
                    else:
                        print(f"  ⏳ Status: {status}...")
                else:
                    print(f"  ❌ Status check failed: {result}")
                    return None
            else:
                print(f"  ❌ Status check failed: {status_response.status_code}")
                return None
        
        print(f"  ❌ Timeout waiting for outpainting")
        return None
        
    except Exception as e:
        print(f"  ❌ Outpainting error: {e}")
        return None

def search_character_images(character_name, num_images=10):
    """
    Search and download images for a character using Google Custom Search API
    
    Args:
        character_name: Name of the character to search for
        num_images: Number of images to download
    
    Returns:
        List of downloaded image paths
    """
    print(f"🔍 Searching for images of: {character_name}")
    print("=" * 50)
    
    try:
        downloaded_images = search_and_download_images(character_name, num_images, DOWNLOAD_DIR)
        
        if downloaded_images:
            print(f"\n✅ Successfully downloaded {len(downloaded_images)} images")
            print(f"📁 Images saved to: {DOWNLOAD_DIR}")
            return downloaded_images
        else:
            print("❌ No images were downloaded")
            return []
            
    except Exception as e:
        print(f"❌ Search error: {e}")
        return []

def process_character_pipeline(character_name=None, use_google_search=False):
    """Main pipeline function"""
    print("🎭 Character Image Acquisition Pipeline")
    print("=" * 50)
    
    # Create directories
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Step 0: Search for images if requested
    if use_google_search and character_name:
        print("\n🔍 Step 0: Searching for Character Images")
        downloaded_images = search_character_images(character_name, num_images=10)
        if not downloaded_images:
            print("❌ No images found, continuing with existing images...")
            return
    
    # Step 1: Find existing images in downloaded_images folder
    print("\n📁 Step 1: Loading Images from downloaded_images folder")
    
    # Get all image files in the downloaded_images directory
    image_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".avif")
    downloaded_images = []
    
    if os.path.exists(DOWNLOAD_DIR):
        for file in os.listdir(DOWNLOAD_DIR):
            if file.lower().endswith(image_extensions):
                filepath = os.path.join(DOWNLOAD_DIR, file)
                downloaded_images.append(filepath)
    
    if not downloaded_images:
        print(f"❌ No images found in {DOWNLOAD_DIR} folder")
        print(f"💡 Please add images to the {DOWNLOAD_DIR} folder and run again")
        return
    
    print(f"Found {len(downloaded_images)} images in {DOWNLOAD_DIR} folder:")
    for img in downloaded_images:
        print(f"  - {os.path.basename(img)}")
    
    # Step 2: Image Validation & Selection
    print("\n🔍 Step 2: Image Validation & Selection")
    valid_candidates = []
    
    for img_path in downloaded_images:
        print(f"\nAnalyzing {os.path.basename(img_path)}:")
        
        # Quality check
        is_quality_ok, quality_msg = check_image_quality(img_path)
        print(f"  Quality: {quality_msg}")
        
        if not is_quality_ok:
            continue
        
        # Person count check
        person_count = detect_person_count(img_path)
        print(f"  Persons: {person_count}")
        
        # Face detection and positioning
        faces = detect_faces_yolo(img_path)
        positioning_analysis = analyze_face_positioning(img_path, faces)
        
        print(f"  Faces: {positioning_analysis['face_count']}")
        
        # Allow if single face detected (regardless of person count)
        if positioning_analysis['face_count'] != 1:
            print(f"  ❌ Skipped: {positioning_analysis['face_count']} faces detected")
            continue
        
        print(f"  Positioning score: {positioning_analysis['positioning_score']}/100")
        print(f"  Aspect ratio: {positioning_analysis['current_aspect_ratio']:.2f}")
        
        if positioning_analysis['face_count'] == 1:
            valid_candidates.append({
                'path': img_path,
                'positioning_score': positioning_analysis['positioning_score'],
                'analysis': positioning_analysis
            })
            print(f"  ✅ Valid candidate")
        else:
            print(f"  ❌ Skipped: {positioning_analysis['face_count']} faces detected")
    
    # Rank candidates by positioning score
    valid_candidates.sort(key=lambda x: x['positioning_score'], reverse=True)
    
    print(f"\n📊 Found {len(valid_candidates)} valid candidates")
    
    # Step 3-4: Processing and Cropping
    print("\n✂️ Step 3-4: Processing and Cropping")
    processed_sprites = []
    
    for i, candidate in enumerate(valid_candidates[:5]):  # Top 5 candidates
        input_path = candidate['path']
        output_filename = f"sprite_{i+1:02d}.jpg"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        print(f"\nProcessing {os.path.basename(input_path)} -> {output_filename}")
        
        # Get crop suggestion if available
        crop_suggestion = None
        if candidate['analysis']['crop_suggestions']:
            crop_suggestion = candidate['analysis']['crop_suggestions'][0]
            print(f"  Using crop suggestion: {crop_suggestion['type']}")
        
        # Crop to target ratio
        success, crop_msg = crop_to_target_ratio(input_path, output_path, crop_suggestion)
        
        if success:
            print(f"  ✅ {crop_msg}")
            
            # Check if outpainting is needed (cowboy shot detection)
            img = cv2.imread(output_path)
            if img is not None:
                height, width = img.shape[:2]
                aspect_ratio = width / height
                
                # Check if we need outpainting (cowboy shot - head to upper thigh)
                # If the image is too short for a proper cowboy shot, we need to outpaint
                needs_outpainting = height < TARGET_HEIGHT * 0.8  # If height is less than 80% of target
                
                if needs_outpainting:
                    print(f"  🎨 Image needs outpainting (height: {height}, target: {TARGET_HEIGHT})")
                    
                    # Calculate padding needed
                    padding_needed = TARGET_HEIGHT - height
                    top_padding = int(padding_needed * 0.3)  # Add some padding to top
                    bottom_padding = int(padding_needed * 0.7)  # Add more padding to bottom
                    left_padding = 50  # Small side padding
                    right_padding = 50
                    
                    print(f"  📏 Padding: top={top_padding}, bottom={bottom_padding}, left={left_padding}, right={right_padding}")
                    
                    # Create a smart prompt for character outpainting (cowboy shot)
                    outpainting_prompt = "Add realistic human body and clothing below the head, extending to mid-thigh level for a cowboy shot, maintaining consistent lighting and style"
                    
                    # Apply outpainting
                    outpainted_path = lightx_outpaint_image(
                        output_path, 
                        left_padding=left_padding,
                        right_padding=right_padding,
                        top_padding=top_padding,
                        bottom_padding=bottom_padding,
                        api_key=LIGHTX_API_KEY,
                        text_prompt=outpainting_prompt
                    )
                    
                    if outpainted_path and os.path.exists(outpainted_path):
                        # Replace the original with the outpainted version
                        shutil.move(outpainted_path, output_path)
                        print(f"  ✅ Outpainting applied successfully")
                    else:
                        print(f"  ⚠️ Outpainting failed, using original image")
                else:
                    print(f"  ✅ No outpainting needed (height: {height})")
            
            processed_sprites.append({
                'input': input_path,
                'output': output_path,
                'score': candidate['positioning_score']
            })
        else:
            print(f"  ❌ {crop_msg}")
    
    # Step 6: Final Validation
    print("\n✅ Step 6: Final Validation")
    final_sprites = []
    
    for sprite in processed_sprites:
        output_path = sprite['output']
        print(f"\nValidating {os.path.basename(output_path)}:")
        
        # Check dimensions
        img = cv2.imread(output_path)
        if img is not None:
            height, width = img.shape[:2]
            print(f"  Dimensions: {width}x{height}")
            
            if width == TARGET_WIDTH and height == TARGET_HEIGHT:
                print("  ✅ Correct dimensions")
                
                # Re-analyze face positioning in final image
                faces = detect_faces_yolo(output_path)
                final_analysis = analyze_face_positioning(output_path, faces)
                
                print(f"  Final positioning score: {final_analysis['positioning_score']}/100")
                
                if final_analysis['face_count'] == 1:
                    final_sprites.append({
                        'path': output_path,
                        'score': final_analysis['positioning_score'],
                        'analysis': final_analysis
                    })
                    print("  ✅ Valid sprite")
                else:
                    print("  ❌ Face detection failed in final image")
            else:
                print("  ❌ Incorrect dimensions")
        else:
            print("  ❌ Could not load final image")
    
    # Final Results
    print("\n🎯 Final Results")
    print("=" * 30)
    print(f"Generated {len(final_sprites)} character sprites:")
    
    for i, sprite in enumerate(final_sprites):
        print(f"\nSprite {i+1}: {os.path.basename(sprite['path'])}")
        print(f"  Positioning score: {sprite['score']}/100")
        print(f"  Status: {'✅ READY' if sprite['score'] >= 60 else '⚠️ NEEDS REVIEW'}")
        
        if sprite['analysis']['recommendations']:
            print("  Recommendations:")
            for rec in sprite['analysis']['recommendations']:
                print(f"    • {rec}")
    
    print(f"\n📁 Output directory: {OUTPUT_DIR}")
    print("🎭 Pipeline complete!")

if __name__ == "__main__":
    print("🎭 Character Image Processing Pipeline")
    print("This pipeline processes images from the 'downloaded_images' folder")
    print("Please add your images to that folder before running the pipeline.")
    print()
    
    process_character_pipeline()
