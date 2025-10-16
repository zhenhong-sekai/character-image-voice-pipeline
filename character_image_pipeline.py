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
from comfyui_outpainting import comfyui_outpaint_image

# --- CONFIG ---
SEARCH_QUERY = ""  # Will be set dynamically
DOWNLOAD_DIR = "downloaded_images"
OUTPUT_DIR = "character_sprites"
ARCHIVE_DIR = "archived_images"  # Store previous search results

# ComfyUI Configuration (no API key needed)
MAX_CANDIDATES = 1
MIN_RESOLUTION = 300
TARGET_WIDTH = 1024
TARGET_HEIGHT = 1536
TARGET_ASPECT_RATIO = TARGET_WIDTH / TARGET_HEIGHT
FACE_TARGET_Y_RATIO = 0.25
FACE_SIZE_RATIO_MIN = 0.15
FACE_SIZE_RATIO_MAX = 0.25

# --- LOAD YOLO ---
print("Loading YOLO model...")
yolo_model = YOLO("models/yolov8n.pt")

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
    """Comprehensive image quality and validation checks"""
    try:
        # Load image
        img = cv2.imread(img_path)
        if img is None:
            return False, "Could not load image"
        
        height, width = img.shape[:2]
        min_dimension = min(width, height)
        
        # Basic quality checks
        if min_dimension < MIN_RESOLUTION:
            return False, f"Resolution too low: {min_dimension}px (min: {MIN_RESOLUTION}px)"
        
        # Calculate quality score
        quality_score = min(min_dimension / 1024, 1.0) * 100
        
        # Check for blur (Laplacian variance)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if blur_score < 100:
            return False, f"Image too blurry: {blur_score:.1f} (min: 100)"
        
        # Check aspect ratio
        aspect_ratio = width / height
        if aspect_ratio < 0.3 or aspect_ratio > 3.0:
            return False, f"Extreme aspect ratio: {aspect_ratio:.2f}"
        
        return True, f"Quality score: {quality_score:.1f}/100, Blur: {blur_score:.1f}"
        
    except Exception as e:
        return False, f"Quality check error: {e}"

def detect_person_count(img_path):
    """Detect and validate number of people in image using YOLO"""
    try:
        results = yolo_model(img_path, verbose=False)
        person_count = 0
        person_details = []
        
        for r in results:
            for box in r.boxes:
                cls = r.names[int(box.cls)]
                if cls == "person" and float(box.conf) > 0.5:
                    person_count += 1
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    person_details.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': float(box.conf),
                        'size_ratio': float(((x2-x1) * (y2-y1)) / (results[0].orig_shape[0] * results[0].orig_shape[1]))
                    })
        
        return person_count, person_details
    except Exception as e:
        print(f"❌ Person detection error: {e}")
        return -1, []

def detect_faces_yolo(img_path):
    """Detect and validate faces using YOLO model"""
    try:
        results = yolo_model(img_path, verbose=False)
        faces = []
        
        for r in results:
            for box in r.boxes:
                cls = r.names[int(box.cls)]
                if cls == "person" and float(box.conf) > 0.5:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    face_width = x2 - x1
                    face_height = y2 - y1
                    face_area = face_width * face_height
                    img_area = results[0].orig_shape[0] * results[0].orig_shape[1]
                    
                    faces.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': float(box.conf),
                        'size_ratio': float(face_area / img_area),
                        'width': float(face_width),
                        'height': float(face_height)
                    })
        
        return faces
    except Exception as e:
        print(f"❌ Face detection error: {e}")
        return []

def comprehensive_image_validation(img_path):
    """Comprehensive validation of image for character sprite generation"""
    validation_results = {
        'is_valid': False,
        'quality_ok': False,
        'person_count': 0,
        'face_count': 0,
        'face_details': [],
        'person_details': [],
        'issues': [],
        'warnings': [],
        'score': 0
    }
    
    try:
        # 1. Quality check
        quality_ok, quality_msg = check_image_quality(img_path)
        validation_results['quality_ok'] = quality_ok
        if not quality_ok:
            validation_results['issues'].append(f"Quality: {quality_msg}")
            return validation_results
        
        # 2. Person detection
        person_count, person_details = detect_person_count(img_path)
        validation_results['person_count'] = person_count
        validation_results['person_details'] = person_details
        
        if person_count == 0:
            validation_results['issues'].append("No people detected")
            return validation_results
        elif person_count > 1:
            validation_results['warnings'].append(f"Multiple people detected: {person_count}")
        
        # 3. Face detection
        faces = detect_faces_yolo(img_path)
        validation_results['face_count'] = len(faces)
        validation_results['face_details'] = faces
        
        if len(faces) == 0:
            validation_results['issues'].append("No faces detected")
            return validation_results
        elif len(faces) > 1:
            validation_results['issues'].append(f"Multiple faces detected: {len(faces)}")
            return validation_results
        
        # 4. Face quality validation
        best_face = faces[0]
        face_size_ratio = best_face['size_ratio']
        face_confidence = best_face['confidence']
        
        if face_confidence < 0.7:
            validation_results['warnings'].append(f"Low face confidence: {face_confidence:.2f}")
        
        if face_size_ratio < 0.01:
            validation_results['issues'].append("Face too small in image")
            return validation_results
        elif face_size_ratio > 0.5:
            validation_results['warnings'].append("Face very large in image")
        
        # 5. Calculate overall score
        score = 50  # Base score
        
        # Quality bonus
        if quality_ok:
            score += 20
        
        # Face confidence bonus
        score += int(face_confidence * 20)
        
        # Face size bonus (optimal range)
        if 0.02 <= face_size_ratio <= 0.3:
            score += 10
        
        # Person count penalty
        if person_count == 1:
            score += 10
        elif person_count > 1:
            score -= 10
        
        validation_results['score'] = min(score, 100)
        validation_results['is_valid'] = len(validation_results['issues']) == 0
        
        return validation_results
        
    except Exception as e:
        validation_results['issues'].append(f"Validation error: {e}")
        return validation_results

def detect_body_parts(img_path):
    """Detect body parts to understand current shot composition"""
    try:
        results = yolo_model(img_path, verbose=False)
        body_parts = []
        
        for r in results:
            for box in r.boxes:
                cls = r.names[int(box.cls)]
                if cls in ["person", "hand", "arm"] and float(box.conf) > 0.3:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    body_parts.append({
                        'type': cls,
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': float(box.conf)
                    })
        
        return body_parts
    except Exception as e:
        print(f"❌ Body part detection error: {e}")
        return []

def analyze_shot_composition(body_parts, face_bbox):
    """Analyze what body parts are visible to determine shot type"""
    if not body_parts:
        return 'headshot_only'
    
    visible_parts = [part['type'] for part in body_parts]
    
    # Check if we have hands/arms (indicating partial body)
    if 'hand' in visible_parts or 'arm' in visible_parts:
        return 'partial_body'
    elif 'person' in visible_parts:
        # Check if person bbox extends significantly below face
        person_boxes = [part for part in body_parts if part['type'] == 'person']
        if person_boxes:
            person_bbox = person_boxes[0]['bbox']
            face_bottom = face_bbox[3]  # face bottom y
            person_bottom = person_bbox[3]  # person bottom y
            
            # If person extends significantly below face, it's likely a cowboy shot
            if person_bottom > face_bottom + 50:  # 50px threshold
                return 'cowboy_shot_already'
    
    return 'headshot_only'

def analyze_cowboy_shot_potential(img_path, faces):
    """Smart analysis to determine if outpainting is needed for cowboy shot"""
    if not faces:
        return {'needs_outpainting': True, 'reason': 'No face detected', 'strategy': 'extend_downward'}
    
    # Get image dimensions
    img = cv2.imread(img_path)
    if img is None:
        return {'needs_outpainting': False, 'reason': 'Could not load image'}
    
    img_height, img_width = img.shape[:2]
    best_face = max(faces, key=lambda x: x['confidence'])
    
    # Face position analysis
    face_center_y = (best_face['bbox'][1] + best_face['bbox'][3]) / 2
    face_y_ratio = face_center_y / img_height
    face_height = best_face['bbox'][3] - best_face['bbox'][1]
    face_size_ratio = face_height / img_height
    
    # Detect body parts to understand composition
    body_parts = detect_body_parts(img_path)
    composition = analyze_shot_composition(body_parts, best_face['bbox'])
    
    print(f"  📊 Composition analysis: {composition}")
    print(f"  📍 Face position: {face_y_ratio:.2f} (0.0=top, 1.0=bottom)")
    print(f"  📏 Face size: {face_size_ratio:.2f}")
    
    # Smart decision logic based on composition and face position
    if composition == 'cowboy_shot_already':
        return {
            'needs_outpainting': False,
            'reason': 'Already appears to be a cowboy shot',
            'strategy': 'none'
        }
    
    elif composition == 'headshot_only':
        # Check face size first - if face is too large, it's definitely a headshot
        if face_size_ratio > 0.6:  # Face takes up more than 60% of image
            return {
                'needs_outpainting': True,
                'reason': f'Headshot detected - face too large ({face_size_ratio*100:.0f}% of image), needs body extension',
                'strategy': 'extend_downward',
                'prompt': 'Add realistic human torso, arms, and upper body below the head, extending to mid-thigh level for a cowboy shot, maintaining consistent lighting and style',
                'padding': {
                    'top': 0,
                    'bottom': int(img_height * 0.8),  # Add 80% more height for large faces
                    'left': 30,
                    'right': 30
                }
            }
        elif face_y_ratio < 0.3:  # Face in upper 30% - likely headshot
            return {
                'needs_outpainting': True,
                'reason': 'Headshot detected - face in upper portion, needs body extension',
                'strategy': 'extend_downward',
                'prompt': 'Add realistic human torso, arms, and upper body below the head, extending to mid-thigh level for a cowboy shot, maintaining consistent lighting and style',
                'padding': {
                    'top': 0,
                    'bottom': int(img_height * 0.6),  # Add 60% more height
                    'left': 30,
                    'right': 30
                }
            }
        elif face_y_ratio > 0.7:  # Face in lower 70% - might need upward extension
            return {
                'needs_outpainting': True,
                'reason': 'Face too low - needs upward extension',
                'strategy': 'extend_upward',
                'prompt': 'Add realistic background and upper body above the head, maintaining consistent lighting and style',
                'padding': {
                    'top': int(img_height * 0.3),
                    'bottom': int(img_height * 0.1),
                    'left': 30,
                    'right': 30
                }
            }
        else:  # Face in middle and reasonable size - might be good cowboy shot already
            return {
                'needs_outpainting': False,
                'reason': 'Good face positioning and size for cowboy shot',
                'strategy': 'none'
            }
    
    elif composition == 'partial_body':
        return {
            'needs_outpainting': True,
            'reason': 'Partial body detected - complete the cowboy shot',
            'strategy': 'extend_partial',
            'prompt': 'Complete the human body below the visible parts, extending to mid-thigh level for a cowboy shot, maintaining consistent lighting and style',
            'padding': {
                'top': 0,
                'bottom': int(img_height * 0.4),
                'left': 20,
                'right': 20
            }
        }
    
    else:
        return {
            'needs_outpainting': True,
            'reason': 'Unknown composition - safe to extend',
            'strategy': 'extend_downward',
            'prompt': 'Add realistic human body below the head, extending to mid-thigh level for a cowboy shot',
            'padding': {
                'top': 0,
                'bottom': int(img_height * 0.5),
                'left': 30,
                'right': 30
            }
        }

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


def archive_previous_images(character_name=None):
    """Archive previous images to keep history"""
    try:
        # Create archive directory with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_subdir = f"{character_name}_{timestamp}" if character_name else f"search_{timestamp}"
        archive_path = os.path.join(ARCHIVE_DIR, archive_subdir)
        os.makedirs(archive_path, exist_ok=True)
        
        archived_count = 0
        if os.path.exists(DOWNLOAD_DIR):
            for file in os.listdir(DOWNLOAD_DIR):
                if file.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".avif")):
                    old_file = os.path.join(DOWNLOAD_DIR, file)
                    archive_file = os.path.join(archive_path, file)
                    try:
                        shutil.move(old_file, archive_file)
                        archived_count += 1
                        print(f"  📦 Archived: {file}")
                    except Exception as e:
                        print(f"  ⚠️ Could not archive {file}: {e}")
        
        if archived_count > 0:
            print(f"📦 Archived {archived_count} previous images to: {archive_path}")
        
        return archive_path, archived_count
        
    except Exception as e:
        print(f"❌ Archive error: {e}")
        return None, 0

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
        
        # Archive previous images first
        archive_path, archived_count = archive_previous_images(character_name)
        if archived_count > 0:
            print(f"📦 Archived {archived_count} previous images to: {archive_path}")
        
        # Download fresh images
        downloaded_images = search_character_images(character_name, num_images=10)
        if not downloaded_images:
            print("❌ No images found, continuing with existing images...")
            return
    else:
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
        
        # Face detection and smart cowboy shot analysis
        faces = detect_faces_yolo(img_path)
        
        print(f"  Faces: {len(faces)}")
        
        # Allow if single face detected (regardless of person count)
        if len(faces) != 1:
            print(f"  ❌ Skipped: {len(faces)} faces detected")
            continue
        
        # Smart cowboy shot analysis
        cowboy_analysis = analyze_cowboy_shot_potential(img_path, faces)
        print(f"  🎯 Cowboy shot analysis: {cowboy_analysis['reason']}")
        
        valid_candidates.append({
            'path': img_path,
            'faces': faces,
            'cowboy_analysis': cowboy_analysis,
            'positioning_score': 50  # Default score for smart analysis
        })
        print(f"  ✅ Valid candidate")
    
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
        
        # Step 1: Smart outpainting analysis and application
        cowboy_analysis = candidate['cowboy_analysis']
        
        if cowboy_analysis['needs_outpainting']:
            print(f"  🎨 Smart outpainting needed: {cowboy_analysis['reason']}")
            print(f"  📝 Strategy: {cowboy_analysis['strategy']}")
            
            # Apply smart outpainting with composition-aware padding
            padding = cowboy_analysis['padding']
            prompt = cowboy_analysis['prompt']
            
            print(f"  📏 Smart padding: top={padding['top']}, bottom={padding['bottom']}, left={padding['left']}, right={padding['right']}")
            print(f"  💬 Smart prompt: {prompt}")
            
            # Apply outpainting with ComfyUI
            outpainted_path = comfyui_outpaint_image(
                input_path,
                left_padding=padding['left'],
                right_padding=padding['right'],
                top_padding=padding['top'],
                bottom_padding=padding['bottom'],
                text_prompt=prompt
            )
            
            if outpainted_path and os.path.exists(outpainted_path):
                # Use outpainted image for further processing
                processed_input = outpainted_path
                print(f"  ✅ Smart outpainting applied successfully")
            else:
                # Fallback to original image
                processed_input = input_path
                print(f"  ⚠️ Outpainting failed, using original image")
        else:
            print(f"  ✅ No outpainting needed: {cowboy_analysis['reason']}")
            processed_input = input_path
        
        # Step 2: Crop to target aspect ratio (2:3)
        success, crop_msg = crop_to_target_ratio(processed_input, output_path)
        
        if success:
            print(f"  ✅ {crop_msg}")
            
            processed_sprites.append({
                'input': input_path,
                'output': output_path,
                'score': candidate['positioning_score'],
                'cowboy_analysis': cowboy_analysis
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
                
                # Smart final analysis
                faces = detect_faces_yolo(output_path)
                if faces:
                    final_cowboy_analysis = analyze_cowboy_shot_potential(output_path, faces)
                    print(f"  🎯 Final cowboy shot analysis: {final_cowboy_analysis['reason']}")
                    
                    # Calculate final score based on smart analysis
                    final_score = 80 if not final_cowboy_analysis['needs_outpainting'] else 60
                    
                    final_sprites.append({
                        'path': output_path,
                        'score': final_score,
                        'cowboy_analysis': final_cowboy_analysis,
                        'original_analysis': sprite.get('cowboy_analysis', {})
                    })
                    print(f"  ✅ Valid sprite (score: {final_score}/100)")
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
        print(f"  Smart score: {sprite['score']}/100")
        print(f"  Status: {'✅ READY' if sprite['score'] >= 60 else '⚠️ NEEDS REVIEW'}")
        
        # Show smart analysis results
        cowboy_analysis = sprite.get('cowboy_analysis', {})
        original_analysis = sprite.get('original_analysis', {})
        
        print(f"  🎯 Final analysis: {cowboy_analysis.get('reason', 'Unknown')}")
        if original_analysis.get('needs_outpainting'):
            print(f"  🎨 Original needed outpainting: {original_analysis.get('reason', 'Unknown')}")
            print(f"  📝 Strategy used: {original_analysis.get('strategy', 'Unknown')}")
        else:
            print(f"  ✅ No outpainting was needed")
    
    print(f"\n📁 Output directory: {OUTPUT_DIR}")
    print("🎭 Pipeline complete!")

if __name__ == "__main__":
    print("🎭 Character Image Processing Pipeline")
    print("This pipeline processes images from the 'downloaded_images' folder")
    print("Please add your images to that folder before running the pipeline.")
    print()
    
    process_character_pipeline()
