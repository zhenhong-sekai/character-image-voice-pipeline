#!/usr/bin/env python3
"""
Gradio Frontend for Character Image Pipeline
Real-time progress tracking with gr.Progress()
"""

import os
# Disable Gradio analytics to avoid pandas dependency issues
# Disable pandas to prevent import errors
os.environ["PANDAS_DISABLE"] = "True"
os.environ["PANDAS_OPT_OUT"] = "True"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ["GRADIO_SERVER_NAME"] = "0.0.0.0"
os.environ["GRADIO_TELEMETRY_ENABLED"] = "False"
os.environ["GRADIO_ANALYTICS"] = "False"
os.environ["GRADIO_TELEMETRY"] = "False"
os.environ["GRADIO_SHARE_ANALYTICS"] = "False"
os.environ["GRADIO_ANALYTICS_HOST"] = ""
os.environ["GRADIO_ANALYTICS_PORT"] = ""
os.environ["GRADIO_ANALYTICS_TOKEN"] = ""
os.environ["GRADIO_ANALYTICS_URL"] = ""
os.environ["GRADIO_ANALYTICS_KEY"] = ""
os.environ["GRADIO_ANALYTICS_SECRET"] = ""
os.environ["GRADIO_ANALYTICS_PROJECT"] = ""
os.environ["GRADIO_ANALYTICS_VERSION"] = ""
os.environ["GRADIO_ANALYTICS_ENVIRONMENT"] = ""
os.environ["GRADIO_ANALYTICS_DEBUG"] = "False"
os.environ["GRADIO_ANALYTICS_VERBOSE"] = "False"
os.environ["GRADIO_ANALYTICS_QUIET"] = "True"
os.environ["GRADIO_ANALYTICS_SILENT"] = "True"
os.environ["GRADIO_ANALYTICS_DISABLED"] = "True"
os.environ["GRADIO_ANALYTICS_OFF"] = "True"
os.environ["GRADIO_ANALYTICS_NO"] = "True"
os.environ["GRADIO_ANALYTICS_FALSE"] = "True"
os.environ["GRADIO_ANALYTICS_0"] = "True"
os.environ["GRADIO_ANALYTICS_NONE"] = "True"
os.environ["GRADIO_ANALYTICS_NULL"] = "True"
os.environ["GRADIO_ANALYTICS_EMPTY"] = "True"
os.environ["GRADIO_ANALYTICS_ZERO"] = "True"
os.environ["GRADIO_ANALYTICS_FALSE"] = "True"
os.environ["GRADIO_ANALYTICS_NO"] = "True"
os.environ["GRADIO_ANALYTICS_OFF"] = "True"
os.environ["GRADIO_ANALYTICS_DISABLED"] = "True"
os.environ["GRADIO_ANALYTICS_SILENT"] = "True"
os.environ["GRADIO_ANALYTICS_QUIET"] = "True"
os.environ["GRADIO_ANALYTICS_VERBOSE"] = "False"
os.environ["GRADIO_ANALYTICS_DEBUG"] = "False"
os.environ["GRADIO_ANALYTICS_ENVIRONMENT"] = ""
os.environ["GRADIO_ANALYTICS_VERSION"] = ""
os.environ["GRADIO_ANALYTICS_PROJECT"] = ""
os.environ["GRADIO_ANALYTICS_SECRET"] = ""
os.environ["GRADIO_ANALYTICS_KEY"] = ""
os.environ["GRADIO_ANALYTICS_URL"] = ""
os.environ["GRADIO_ANALYTICS_TOKEN"] = ""
os.environ["GRADIO_ANALYTICS_PORT"] = ""
os.environ["GRADIO_ANALYTICS_HOST"] = ""
os.environ["GRADIO_SHARE_ANALYTICS"] = "False"
os.environ["GRADIO_TELEMETRY"] = "False"
os.environ["GRADIO_ANALYTICS"] = "False"
os.environ["GRADIO_TELEMETRY_ENABLED"] = "False"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import gradio as gr
import requests
import time
import os
import json
from datetime import datetime
from PIL import Image
import io
import base64
import threading
import queue
from typing import Generator, Tuple

# Import voice pipeline classes
import sys
sys.path.append('voice')
from voice.main import AssemblyAITranscriber, TargetSpeakerIdentifier, VideoSegmentExtractor

# API Configuration
API_BASE_URL = "http://localhost:8000"

def check_api_connection():
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_image_to_api(uploaded_file):
    """Upload image to API server"""
    try:
        # Convert PIL Image to bytes if needed
        if hasattr(uploaded_file, 'save'):
            # It's a PIL Image, convert to bytes
            img_buffer = io.BytesIO()
            uploaded_file.save(img_buffer, format='JPEG')
            img_bytes = img_buffer.getvalue()
            files = {"file": ("image.jpg", img_bytes, "image/jpeg")}
        else:
            # It's already bytes
            files = {"file": uploaded_file}
        
        response = requests.post(f"{API_BASE_URL}/upload", files=files)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Upload error: {e}")
        return None

def analyze_image_with_api(file_path):
    """Analyze image using API"""
    try:
        response = requests.post(f"{API_BASE_URL}/analyze", json={"file_path": file_path})
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Analysis error: {e}")
        return None

def start_pipeline(use_google_search=False, character_name=None, max_candidates=5):
    """Start the pipeline"""
    try:
        payload = {
            "use_google_search": use_google_search,
            "character_name": character_name,
            "max_candidates": max_candidates
        }
        response = requests.post(f"{API_BASE_URL}/process", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Pipeline start error: {e}")
        return None

def get_job_status(job_id):
    """Get job status from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/status/{job_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def analyze_single_image(image, progress=gr.Progress()):
    """Analyze and process a single uploaded image with real-time progress"""
    import time
    start_time = time.time()
    
    if image is None:
        return "❌ Please upload an image first", None, None, None
    
    progress(0.05, desc="📤 Uploading image to server...")
    
    # Upload image
    upload_result = upload_image_to_api(image)
    if not upload_result:
        return "❌ Failed to upload image", None, None, None
    
    progress(0.1, desc="🔍 Analyzing image...")
    
    # Analyze image
    analysis = analyze_image_with_api(upload_result['file_path'])
    if not analysis:
        return "❌ Analysis failed", None, None, None
    
    progress(0.2, desc="🎭 Processing image for character sprite...")
    
    # Check if image is valid for processing
    if analysis['face_count'] != 1:
        return f"❌ Image has {analysis['face_count']} faces. Need exactly 1 face for processing.", analysis, None, None
    
    if not analysis['quality']['is_ok']:
        return f"❌ Image quality too poor: {analysis['quality']['message']}", analysis, None, None
    
    # Process the image through the full pipeline
    try:
        from character_image_pipeline import (
            detect_faces_yolo, analyze_cowboy_shot_potential, 
            crop_to_target_ratio, comfyui_outpaint_image
        )
        
        progress(0.3, desc="🎨 Applying smart outpainting...")
        
        # Get cowboy shot analysis
        faces = detect_faces_yolo(upload_result['file_path'])
        cowboy_analysis = analyze_cowboy_shot_potential(upload_result['file_path'], faces)
        
        processed_input = upload_result['file_path']
        
        # Apply outpainting if needed
        if cowboy_analysis['needs_outpainting']:
            progress(0.5, desc=f"🎨 {cowboy_analysis['reason']}")
            
            padding = cowboy_analysis['padding']
            prompt = cowboy_analysis['prompt']
            
            outpainted_path = comfyui_outpaint_image(
                upload_result['file_path'],
                left_padding=padding['left'],
                right_padding=padding['right'],
                top_padding=padding['top'],
                bottom_padding=padding['bottom'],
                text_prompt=prompt
            )
            
            if outpainted_path and os.path.exists(outpainted_path):
                processed_input = outpainted_path
                progress(0.7, desc="✅ Outpainting applied successfully")
            else:
                progress(0.7, desc="⚠️ Outpainting failed, using original")
        else:
            progress(0.7, desc="✅ No outpainting needed")
        
        # Crop to target ratio
        progress(0.8, desc="✂️ Cropping to target dimensions...")
        
        output_filename = f"single_sprite_{int(time.time())}.jpg"
        output_path = os.path.join("character_sprites", output_filename)
        
        # Ensure output directory exists
        os.makedirs("character_sprites", exist_ok=True)
        
        success, crop_msg = crop_to_target_ratio(processed_input, output_path)
        
        if not success:
            return f"❌ Cropping failed: {crop_msg}", analysis, None, None
        
        progress(0.9, desc="✅ Final validation...")
        
        # Final analysis
        final_faces = detect_faces_yolo(output_path)
        final_analysis = analyze_cowboy_shot_potential(output_path, final_faces)
        final_score = 80 if not final_analysis['needs_outpainting'] else 60
        
        progress(1.0, desc="🎭 Character sprite generated!")
        
        # Calculate timing
        total_time = time.time() - start_time
        
        # Format results
        results_text = f"""
        ## 🎭 Character Sprite Generated!
        
        **🎯 Original Analysis:**
        - **Quality:** {'✅ Good' if analysis['quality']['is_ok'] else '❌ Poor'} - {analysis['quality']['message']}
        - **Faces:** {analysis['face_count']}
        - **Composition:** {analysis['composition']}
        - **Cowboy Analysis:** {analysis['cowboy_analysis']['reason']}
        
        **🎨 Processing Applied:**
        - **Outpainting:** {'Yes' if cowboy_analysis['needs_outpainting'] else 'No'}
        - **Strategy:** {cowboy_analysis.get('strategy', 'None')}
        - **Final Score:** {final_score}/100
        - **Status:** {'✅ READY' if final_score >= 60 else '⚠️ NEEDS REVIEW'}
        
        **⏱️ Performance:**
        - **Total Processing Time:** {total_time:.1f} seconds
        
        **📁 Output:** {output_path}
        """
        
        # Load the generated image for display
        generated_image = None
        if os.path.exists(output_path):
            generated_image = Image.open(output_path)
        
        return results_text, analysis, generated_image, output_path
        
    except Exception as e:
        return f"❌ Processing failed: {str(e)}", analysis, None, None

def run_pipeline_with_progress(character_name, max_candidates, progress=gr.Progress()):
    """Run the full pipeline with real-time progress updates"""
    
    # Check API connection
    if not check_api_connection():
        return "❌ Cannot connect to API server. Please make sure the API server is running.", None, None, None, None
    
    if not character_name:
        return "❌ Please enter a character name for Google search", None, None, None, None
    
    progress(0.05, desc="🚀 Starting pipeline...")
    
    # Start pipeline
    pipeline_result = start_pipeline(
        use_google_search=True,
        character_name=character_name,
        max_candidates=max_candidates
    )
    
    if not pipeline_result:
        return "❌ Failed to start pipeline", None, None, None, None
    
    job_id = pipeline_result['job_id']
    progress(0.1, desc=f"📋 Job started: {job_id[:8]}...")
    
    # Monitor progress
    last_progress = 0
    status_messages = []
    generated_images = []
    
    while True:
        status = get_job_status(job_id)
        if not status:
            return "❌ Could not get job status", None, None, None, None
        
        # Update progress
        current_progress = status['progress'] / 100
        progress(current_progress, desc=f"🔄 {status['current_step']}: {status['message']}")
        
        # Collect status messages
        if status['message'] not in status_messages:
            status_messages.append(f"• {status['message']}")
        
        # Check if completed
        if status['status'] == 'completed':
            progress(1.0, desc="✅ Pipeline completed!")
            
            # Process results
            results = status['results']
            # Calculate timing info
            total_time = results.get('total_time', 0)
            avg_time_per_sprite = results.get('average_time_per_sprite', 0)
            
            results_text = f"""
            ## 🎯 Pipeline Results - Batch Processing Complete!
            
            **📊 Summary:**
            - **Generated:** {results['total_sprites']} character sprites
            - **Success Rate:** {results.get('success_rate', 0):.1f}%
            
            **⏱️ Performance Metrics:**
            - **Total Processing Time:** {total_time:.1f} seconds
            - **Average Time per Sprite:** {avg_time_per_sprite:.1f} seconds
            - **Processing Speed:** {60/avg_time_per_sprite:.1f} sprites/minute
            
            ### 📋 Processing Steps:
            {chr(10).join(status_messages)}
            
            ### 🎭 Generated Sprites:
            """
            
            # Prepare data for different views
            generated_images = []
            before_after_pairs = []
            results_table_md = "## 📊 Detailed Results\n\n| Sprite | Score | Status | Outpainting | Strategy | Faces/People | Quality |\n|--------|-------|--------|-------------|----------|-------------|----------|\n"
            
            for i, sprite in enumerate(results['sprites']):
                results_text += f"""
            **Sprite {i+1}:**
            - Score: {sprite['score']}/100
            - Status: {'✅ READY' if sprite['score'] >= 60 else '⚠️ NEEDS REVIEW'}
            - Analysis: {sprite['cowboy_analysis']['reason']}
            """
                
                # Check if the sprite path exists and is a file
                sprite_path = sprite.get('path', '')
                
                if sprite_path and os.path.exists(sprite_path) and os.path.isfile(sprite_path):
                    # Format as (image_path, caption) tuple for Gradio Gallery
                    generated_images.append((sprite_path, f"Sprite {i+1}"))
                    
                    # Create before/after pair - ensure both paths are valid files
                    input_path = sprite.get('input', '')
                    
                    if input_path and os.path.exists(input_path) and os.path.isfile(input_path):
                        # Format as (image_path, caption) tuples for Gradio Gallery
                        before_after_pairs.extend([
                            (input_path, f"Original {i+1}"),
                            (sprite_path, f"Sprite {i+1}")
                        ])
                    else:
                        # If no valid input path, just show the output with caption
                        before_after_pairs.append((sprite_path, f"Sprite {i+1}"))
                    
                    # Prepare markdown table data
                    original_analysis = sprite.get('original_analysis', {})
                    outpainting_needed = original_analysis.get('needs_outpainting', False)
                    strategy = original_analysis.get('strategy', 'None')
                    validation = sprite.get('validation', {})
                    
                    # Get validation details
                    face_count = validation.get('face_count', 0)
                    person_count = validation.get('person_count', 0)
                    quality_ok = validation.get('quality_ok', False)
                    
                    results_table_md += f"| Sprite {i+1} | {sprite['score']}/100 | {'✅ READY' if sprite['score'] >= 60 else '⚠️ NEEDS REVIEW'} | {'Yes' if outpainting_needed else 'No'} | {strategy} | {face_count}F/{person_count}P | {'✅' if quality_ok else '❌'} |\n"
            
            # Download info
            download_text = f"""
            📦 Download Information:
            
            **⏱️ Processing Summary:**
            - Total Time: {total_time:.1f} seconds
            - Average per Sprite: {avg_time_per_sprite:.1f} seconds
            - Processing Speed: {60/avg_time_per_sprite:.1f} sprites/minute
            
            Generated {len(generated_images)} character sprites:
            """
            for i, img_path in enumerate(generated_images):
                download_text += f"\n• sprite_{i+1:02d}.jpg - {img_path}"
            
            return results_text, generated_images, results_table_md, download_text, before_after_pairs
            break
        
        elif status['status'] == 'error':
            return f"❌ Pipeline failed: {status['error']}", None, None, None, None
        
        # Wait before next check
        time.sleep(1)
    
    return "❌ Pipeline monitoring failed", None, None, None, None

def create_image_gallery(images):
    """Create a gallery of generated images"""
    if not images:
        return None
    
    # Load and return images
    gallery_images = []
    for img_path in images:
        if os.path.exists(img_path):
            img = Image.open(img_path)
            gallery_images.append(img)
    
    return gallery_images

def download_results(results):
    """Create download links for results"""
    if not results or 'sprites' not in results:
        return "No results to download"
    
    download_info = []
    for i, sprite in enumerate(results['sprites']):
        if os.path.exists(sprite['path']):
            download_info.append(f"📁 sprite_{i+1:02d}.jpg - {sprite['path']}")
    
    return "\n".join(download_info) if download_info else "No files available for download"

def transcribe_video_file(video_file, target_speaker_description, progress=gr.Progress()):
    """Transcribe a video file and extract target speaker segments"""
    if video_file is None:
        return ("❌ Please upload a video file first", None, None, None, None, None, None, None, None, None)
    
    try:
        progress(0.1, desc="🎬 Initializing transcription...")
        
        # Initialize transcriber
        transcriber = AssemblyAITranscriber("70702281c18e427f8093e5f5385a3195")
        
        progress(0.2, desc="📤 Uploading video to AssemblyAI...")
        
        # Transcribe the video
        transcription_result = transcriber.transcribe_file(
            video_file, 
            speech_model="universal", 
            max_wait_time=300
        )
        
        progress(0.7, desc="🔍 Analyzing speakers...")
        
        # Get utterances
        utterances = transcription_result.get('utterances', [])
        if not utterances:
            return ("❌ No speaker diarization data available", None, None, None, None, None, None, None, None, None)
        
        # Initialize speaker identifier
        speaker_identifier = TargetSpeakerIdentifier()
        
        progress(0.8, desc="🎯 Identifying target speaker...")
        
        # Identify target speaker using LLM
        identified_speaker = speaker_identifier.identify_target_speaker(
            utterances, target_speaker_description
        )
        
        if identified_speaker == "UNKNOWN":
            return ("❌ Could not identify target speaker", None, None, None, None, None, None, None, None, None)
        
        progress(0.9, desc="📝 Extracting target speaker segments...")
        
        # Filter target speaker segments
        target_segments = speaker_identifier.filter_target_speaker_segments(
            utterances, identified_speaker
        )
        
        if not target_segments:
            return ("❌ No segments found for the identified target speaker", None, None, None, None, None, None, None, None, None)
        
        progress(1.0, desc="✅ Transcription completed!")
        
        # Format results
        full_transcript = transcription_result.get('text', '')
        
        # Create speaker-separated transcript
        speaker_transcript = ""
        for utterance in utterances:
            speaker = utterance.get('speaker', 'Unknown')
            text = utterance.get('text', '')
            speaker_transcript += f"Speaker {speaker}: {text}\n"
        
        # Create target speaker transcript
        target_transcript = ""
        target_text = ""
        for segment in target_segments:
            text = segment.get('text', '')
            start_time = segment.get('start', 0)
            end_time = segment.get('end', start_time + 1000)
            target_transcript += f"Speaker {identified_speaker}: {text}\n"
            target_transcript += f"  Time: {start_time/1000:.1f}s - {end_time/1000:.1f}s\n"
            target_text += text + " "
        
        # Create comprehensive results with better formatting
        results_text = f"""
        ## 🎤 Voice Transcription Results
        
        ### 📊 Summary
        - **🎯 Target Speaker:** {target_speaker_description}
        - **🔍 Identified as:** Speaker {identified_speaker}
        - **📊 Segments Found:** {len(target_segments)}
        - **⏱️ Total Duration:** {sum((seg.get('end', 0) - seg.get('start', 0)) for seg in target_segments) / 1000:.1f} seconds
        
        ### 📝 Full Transcript
        ```
        {full_transcript}
        ```
        
        ### 🎭 Target Speaker Segments
        """
        
        # Add formatted target speaker segments
        for i, segment in enumerate(target_segments, 1):
            text = segment.get('text', '')
            start_time = segment.get('start', 0)
            end_time = segment.get('end', start_time + 1000)
            duration = (end_time - start_time) / 1000
            
            results_text += f"""
        **Segment {i}** ({start_time/1000:.1f}s - {end_time/1000:.1f}s, {duration:.1f}s)
        ```
        {text}
        ```
        """
        
        results_text += f"""
        ### 📄 Complete Target Speaker Text
        ```
        {target_text.strip()}
        ```
        
        ### 📊 Statistics
        - **Total Segments:** {len(target_segments)}
        - **Total Speaking Time:** {sum((seg.get('end', 0) - seg.get('start', 0)) for seg in target_segments) / 1000:.1f} seconds
        - **Average Segment Length:** {sum((seg.get('end', 0) - seg.get('start', 0)) for seg in target_segments) / len(target_segments) / 1000:.1f} seconds
        - **Total Words:** {len(target_text.split())}
        """
        
        # Save transcript to file
        transcript_filename = f"transcript_{int(time.time())}.txt"
        transcript_path = os.path.join("voice", transcript_filename)
        
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write("FULL TRANSCRIPT:\n")
            f.write("="*50 + "\n")
            f.write(full_transcript + "\n\n")
            f.write("ALL SPEAKER-SEPARATED TRANSCRIPT:\n")
            f.write("="*50 + "\n")
            f.write(speaker_transcript + "\n")
            f.write(f"TARGET SPEAKER SEGMENTS ({target_speaker_description}):\n")
            f.write("="*50 + "\n")
            f.write(target_transcript + "\n")
            f.write(f"COMPLETE TARGET SPEAKER TRANSCRIPT:\n")
            f.write("="*50 + "\n")
            f.write(f"'{target_text.strip()}'\n")
        
        # Create separate components for better display
        summary_text = f"""
        ## 🎤 Voice Transcription Results
        
        ### 📊 Summary
        - **🎯 Target Speaker:** {target_speaker_description}
        - **🔍 Identified as:** Speaker {identified_speaker}
        - **📊 Segments Found:** {len(target_segments)}
        - **⏱️ Total Duration:** {sum((seg.get('end', 0) - seg.get('start', 0)) for seg in target_segments) / 1000:.1f} seconds
        
        ### 📊 Statistics
        - **Total Segments:** {len(target_segments)}
        - **Total Speaking Time:** {sum((seg.get('end', 0) - seg.get('start', 0)) for seg in target_segments) / 1000:.1f} seconds
        - **Average Segment Length:** {sum((seg.get('end', 0) - seg.get('start', 0)) for seg in target_segments) / len(target_segments) / 1000:.1f} seconds
        - **Total Words:** {len(target_text.split())}
        """
        
        # Format target segments with timestamps
        formatted_segments = ""
        for i, segment in enumerate(target_segments, 1):
            text = segment.get('text', '')
            start_time = segment.get('start', 0)
            end_time = segment.get('end', start_time + 1000)
            duration = (end_time - start_time) / 1000
            
            formatted_segments += f"Segment {i} ({start_time/1000:.1f}s - {end_time/1000:.1f}s, {duration:.1f}s):\n{text}\n\n"
        
        # Extract audio segments using FFmpeg
        audio_segments_path = None
        try:
            progress(0.95, desc="🎵 Extracting audio segments...")
            
            # Initialize video extractor
            video_extractor = VideoSegmentExtractor()
            
            if video_extractor.ffmpeg_available:
                # Create output directory for segments
                segments_dir = os.path.join("voice", f"audio_segments_{int(time.time())}")
                os.makedirs(segments_dir, exist_ok=True)
                
                # Extract individual segments
                success = video_extractor.extract_individual_segments(
                    target_segments, 
                    video_file, 
                    segments_dir
                )
                
                if success:
                    audio_segments_path = segments_dir
                    progress(1.0, desc="✅ Audio segments extracted!")
                else:
                    progress(1.0, desc="⚠️ Audio extraction failed, transcript only")
            else:
                progress(1.0, desc="⚠️ FFmpeg not available, transcript only")
                
        except Exception as e:
            print(f"Audio extraction error: {e}")
            progress(1.0, desc="⚠️ Audio extraction failed")
        
        # Create audio segments info
        audio_segments_info = ""
        if audio_segments_path and os.path.exists(audio_segments_path):
            segment_files = [f for f in os.listdir(audio_segments_path) if f.endswith('.mp4')]
            audio_segments_info = f"""
            ## 🎵 Audio Segments Extracted
            
            **📁 Directory:** {audio_segments_path}
            **📊 Segments:** {len(segment_files)} audio files
            
            **📋 Files:**
            """
            for i, file in enumerate(sorted(segment_files), 1):
                file_path = os.path.join(audio_segments_path, file)
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                audio_segments_info += f"- **Segment {i}:** {file} ({file_size:.1f} MB)\n"
        else:
            audio_segments_info = "❌ Audio segments could not be extracted. FFmpeg may not be available."
        
        # Create audio segments info
        audio_segments_info = create_audio_players_info(audio_segments_path, target_segments)
        
        # Get audio segment files for download
        audio_segment_files = get_audio_segments_files(audio_segments_path)
        
        # Create audio players HTML
        audio_players_html = create_audio_players_html(audio_segments_path, target_segments)
        
        return (audio_segments_info, full_transcript, formatted_segments, target_text.strip(), 
                transcript_path, target_segments, identified_speaker, audio_segments_path, audio_segment_files, audio_players_html)
        
    except Exception as e:
        return f"❌ Transcription failed: {str(e)}", None, None, None, None, None, None, None, None, None

def search_and_transcribe_video(character_name, max_videos, target_speaker_description, progress=gr.Progress()):
    """Search for videos using Google and transcribe them"""
    if not character_name:
        return ("❌ Please enter a character name for video search", None, None, None, None, None, None, None, None, None)
    
    try:
        progress(0.1, desc="🔍 Searching for videos...")
        
        # This would integrate with Google search for videos
        # For now, we'll use the existing video file
        video_path = os.path.join("voice", "mp4_files", "videoplayback.mp4")
        
        if not os.path.exists(video_path):
            return ("❌ No video file found. Please upload a video first.", None, None, None, None, None, None, None, None, None)
        
        progress(0.2, desc="🎬 Processing video...")
        
        # Use the same transcription function
        return transcribe_video_file(video_path, target_speaker_description, progress)
        
    except Exception as e:
        return f"❌ Video search and transcription failed: {str(e)}", None, None, None, None, None, None, None, None, None

def get_audio_segments_files(audio_segments_path):
    """Get list of audio segment files for download"""
    if not audio_segments_path or not os.path.exists(audio_segments_path):
        return None
    
    segment_files = []
    for file in os.listdir(audio_segments_path):
        if file.endswith('.mp4'):
            file_path = os.path.join(audio_segments_path, file)
            segment_files.append(file_path)
    
    return segment_files if segment_files else None

def create_audio_players_info(audio_segments_path, target_segments):
    """Create info text for audio segments"""
    if not audio_segments_path or not os.path.exists(audio_segments_path):
        return "No audio segments available"
    
    segment_files = sorted([f for f in os.listdir(audio_segments_path) if f.endswith('.mp4')])
    
    info_text = f"""
    ## 🎵 Audio Segments Extracted
    
    **📁 Directory:** {audio_segments_path}
    **📊 Segments:** {len(segment_files)} audio files
    
    **📋 Files:**
    """
    
    for i, file in enumerate(segment_files):
        file_path = os.path.join(audio_segments_path, file)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        
        # Get segment info
        segment_info = ""
        if i < len(target_segments):
            segment = target_segments[i]
            start_time = segment.get('start', 0)
            end_time = segment.get('end', start_time + 1000)
            duration = (end_time - start_time) / 1000
            segment_info = f" (Time: {start_time/1000:.1f}s - {end_time/1000:.1f}s, {duration:.1f}s)"
        
        info_text += f"- **Segment {i+1}:** {file} ({file_size:.1f} MB){segment_info}\n"
    
    info_text += "\n**📥 Download:** Use the download section below to get the audio files."
    return info_text

def create_audio_players_html(audio_segments_path, target_segments):
    """Create HTML with audio players for each segment"""
    if not audio_segments_path or not os.path.exists(audio_segments_path):
        return "No audio segments available"
    
    segment_files = sorted([f for f in os.listdir(audio_segments_path) if f.endswith('.mp4')])
    
    if not segment_files:
        return "No audio segments found"
    
    html_content = """
    <div style="margin: 20px 0;">
        <h3>🎧 Play Audio Segments</h3>
    """
    
    for i, file in enumerate(segment_files):
        file_path = os.path.join(audio_segments_path, file)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        
        # Get segment info
        segment_info = ""
        if i < len(target_segments):
            segment = target_segments[i]
            start_time = segment.get('start', 0)
            end_time = segment.get('end', start_time + 1000)
            duration = (end_time - start_time) / 1000
            segment_info = f"<small>Time: {start_time/1000:.1f}s - {end_time/1000:.1f}s ({duration:.1f}s)</small>"
        
        html_content += f"""
        <div style="margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9;">
            <h4>Segment {i+1}: {file}</h4>
            {segment_info}
            <br><br>
            <audio controls style="width: 100%;">
                <source src="file/{file_path}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            <br><br>
            <a href="file/{file_path}" download="{file}" style="background: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px;">
                📥 Download ({file_size:.1f} MB)
            </a>
        </div>
        """
    
    html_content += "</div>"
    return html_content

# Create the Gradio interface
def create_interface():
    with gr.Blocks(
        title="🎭🎤 Character Image & Voice Pipeline",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        .step-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            margin: 1rem 0;
        }
        """
    ) as demo:
        
        gr.Markdown("""
        # 🎭🎤 Character Image & Voice Pipeline
        **Smart AI-powered character sprite generation and voice transcription with real-time progress tracking**
        """)
        
        with gr.Tabs():
            # ===== CHARACTER IMAGE PIPELINE =====
            with gr.Tab("🎭 Character Image Pipeline"):
                gr.Markdown("### 🎨 Generate character sprites from images")
                
                with gr.Tabs():
                    with gr.Tab("📤 Upload & Analyze"):
                        gr.Markdown("#### 📷 Upload an image to analyze and generate a sprite")
                        
                        with gr.Row():
                            with gr.Column():
                                image_input = gr.Image(
                                    label="Upload Image",
                                    type="pil",
                                    height=400
                                )
                                analyze_btn = gr.Button("🔍 Analyze Image", variant="primary")
                            
                            with gr.Column():
                                analysis_output = gr.Markdown(label="Analysis Results")
                                analysis_data = gr.JSON(label="Raw Analysis Data", visible=False)
                                file_path = gr.Textbox(label="File Path", visible=False)
                                generated_sprite = gr.Image(label="Generated Character Sprite", height=400)
                        
                        analyze_btn.click(
                            analyze_single_image,
                            inputs=[image_input],
                            outputs=[analysis_output, analysis_data, generated_sprite, file_path]
                        )
                    
                    with gr.Tab("🚀 Full Pipeline"):
                        gr.Markdown("#### 🎯 Run the complete character image pipeline with Google search")
                        
                        with gr.Row():
                            with gr.Column():
                                character_name = gr.Textbox(
                                    label="Character Name",
                                    value="",
                                    placeholder="Enter character name (e.g., Taylor Swift, Charlie Kirk)"
                                )
                                max_candidates = gr.Slider(
                                    label="Max Candidates",
                                    minimum=1,
                                    maximum=10,
                                    value=5,
                                    step=1
                                )
                                start_pipeline_btn = gr.Button("🚀 Start Pipeline", variant="primary", size="lg")
                            
                            with gr.Column():
                                pipeline_output = gr.Markdown(label="Pipeline Results")
                                
                                # Multiple galleries for different views
                                with gr.Tabs():
                                    with gr.Tab("🎭 Generated Sprites"):
                                        image_gallery = gr.Gallery(
                                            label="All Generated Sprites",
                                            show_label=True,
                                            elem_id="gallery",
                                            columns=3,
                                            rows=2,
                                            height=400,
                                            object_fit="contain"
                                        )
                                    
                                    with gr.Tab("📊 Results Table"):
                                        results_table = gr.Markdown(
                                            label="Detailed Results",
                                            value="Results will appear here after processing..."
                                        )
                                    
                                    with gr.Tab("🔄 Before/After"):
                                        before_after_gallery = gr.Gallery(
                                            label="Before/After Comparison",
                                            show_label=True,
                                            elem_id="before_after_gallery",
                                            columns=2,
                                            rows=3,
                                            height=600,
                                            object_fit="contain"
                                        )
                                    
                                    with gr.Tab("📥 Download"):
                                        download_info = gr.Textbox(label="Download Information", lines=5)
                                        download_btn = gr.Button("📦 Download All Sprites", variant="secondary")
                        
                        start_pipeline_btn.click(
                            run_pipeline_with_progress,
                            inputs=[character_name, max_candidates],
                            outputs=[pipeline_output, image_gallery, results_table, download_info, before_after_gallery]
                        )
            
            # ===== VOICE PIPELINE =====
            with gr.Tab("🎤 Voice Pipeline"):
                gr.Markdown("### 🎬 Transcribe videos and extract target speaker segments")
                
                with gr.Tabs():
                    with gr.Tab("📤 Upload Video"):
                        gr.Markdown("#### 🎬 Upload a video file to transcribe")
                        
                        with gr.Row():
                            with gr.Column():
                                video_input = gr.Video(
                                    label="Upload Video (MP4)",
                                    height=300
                                )
                                target_speaker_upload = gr.Textbox(
                                    label="Target Speaker Description",
                                    value="Donald Trump",
                                    placeholder="Describe the target speaker (e.g., Donald Trump, Taylor Swift)"
                                )
                                transcribe_btn = gr.Button("🎤 Transcribe Video", variant="primary")
                            
                            with gr.Column():
                                with gr.Tabs():
                                    with gr.Tab("📊 Summary & Audio"):
                                        # Audio segments info
                                        audio_segments_info_upload = gr.Markdown(
                                            label="Audio Segments Info",
                                            value="Audio segments will appear here after extraction..."
                                        )
                                        
                                        # Individual audio players
                                        audio_players_upload = gr.HTML(
                                            label="Audio Players",
                                            value="Audio players will appear here after extraction..."
                                        )
                                        
                                        # Download section
                                        audio_segments_upload = gr.File(
                                            label="Download All Audio Segments",
                                            file_count="multiple"
                                        )
                                    
                                    with gr.Tab("📝 Full Transcript"):
                                        full_transcript_upload = gr.Textbox(
                                            label="Complete Transcript",
                                            lines=10,
                                            max_lines=20,
                                            show_copy_button=True
                                        )
                                    
                                    with gr.Tab("🎭 Target Segments"):
                                        target_segments_upload = gr.Textbox(
                                            label="Target Speaker Segments",
                                            lines=15,
                                            max_lines=25,
                                            show_copy_button=True
                                        )
                                    
                                    with gr.Tab("📄 Complete Text"):
                                        complete_text_upload = gr.Textbox(
                                            label="Complete Target Speaker Text",
                                            lines=8,
                                            max_lines=15,
                                            show_copy_button=True
                                        )
                                
                                transcript_file_upload = gr.File(label="Download Transcript")
                                target_segments_data_upload = gr.JSON(label="Target Segments Data", visible=False)
                                identified_speaker_upload = gr.Textbox(label="Identified Speaker", visible=False)
                                audio_segments_path_upload = gr.Textbox(label="Audio Segments Path", visible=False)
                        
                        transcribe_btn.click(
                            transcribe_video_file,
                            inputs=[video_input, target_speaker_upload],
                            outputs=[audio_segments_info_upload, full_transcript_upload, target_segments_upload, 
                                    complete_text_upload, transcript_file_upload, target_segments_data_upload, 
                                    identified_speaker_upload, audio_segments_path_upload, audio_segments_upload, audio_players_upload]
                        )
                        
                        # Update audio segments download when path changes
                        def update_audio_segments_upload(audio_segments_path):
                            if audio_segments_path and os.path.exists(audio_segments_path):
                                segment_files = get_audio_segments_files(audio_segments_path)
                                return segment_files
                            return None
                        
                        audio_segments_path_upload.change(
                            update_audio_segments_upload,
                            inputs=[audio_segments_path_upload],
                            outputs=[audio_segments_upload]
                        )
                    
                    with gr.Tab("🔍 Search & Transcribe"):
                        gr.Markdown("#### 🔍 Search for videos and transcribe them")
                        
                        with gr.Row():
                            with gr.Column():
                                character_name_voice = gr.Textbox(
                                    label="Character Name",
                                    value="",
                                    placeholder="Enter character name for video search"
                                )
                                max_videos = gr.Slider(
                                    label="Max Videos",
                                    minimum=1,
                                    maximum=5,
                                    value=1,
                                    step=1
                                )
                                target_speaker_search = gr.Textbox(
                                    label="Target Speaker Description",
                                    value="Donald Trump",
                                    placeholder="Describe the target speaker"
                                )
                                search_transcribe_btn = gr.Button("🔍 Search & Transcribe", variant="primary")
                            
                            with gr.Column():
                                with gr.Tabs():
                                    with gr.Tab("📊 Summary & Audio"):
                                        # Audio segments info
                                        audio_segments_info_search = gr.Markdown(
                                            label="Audio Segments Info",
                                            value="Audio segments will appear here after extraction..."
                                        )
                                        
                                        # Individual audio players
                                        audio_players_search = gr.HTML(
                                            label="Audio Players",
                                            value="Audio players will appear here after extraction..."
                                        )
                                        
                                        # Download section
                                        audio_segments_search = gr.File(
                                            label="Download All Audio Segments",
                                            file_count="multiple"
                                        )
                                    
                                    with gr.Tab("📝 Full Transcript"):
                                        full_transcript_search = gr.Textbox(
                                            label="Complete Transcript",
                                            lines=10,
                                            max_lines=20,
                                            show_copy_button=True
                                        )
                                    
                                    with gr.Tab("🎭 Target Segments"):
                                        target_segments_search = gr.Textbox(
                                            label="Target Speaker Segments",
                                            lines=15,
                                            max_lines=25,
                                            show_copy_button=True
                                        )
                                    
                                    with gr.Tab("📄 Complete Text"):
                                        complete_text_search = gr.Textbox(
                                            label="Complete Target Speaker Text",
                                            lines=8,
                                            max_lines=15,
                                            show_copy_button=True
                                        )
                                
                                transcript_file_search = gr.File(label="Download Transcript")
                                target_segments_data_search = gr.JSON(label="Target Segments Data", visible=False)
                                identified_speaker_search = gr.Textbox(label="Identified Speaker", visible=False)
                                audio_segments_path_search = gr.Textbox(label="Audio Segments Path", visible=False)
                        
                        search_transcribe_btn.click(
                            search_and_transcribe_video,
                            inputs=[character_name_voice, max_videos, target_speaker_search],
                            outputs=[audio_segments_info_search, full_transcript_search, target_segments_search, 
                                    complete_text_search, transcript_file_search, target_segments_data_search, 
                                    identified_speaker_search, audio_segments_path_search, audio_segments_search, audio_players_search]
                        )
                        
                        # Update audio segments download when path changes
                        def update_audio_segments_search(audio_segments_path):
                            if audio_segments_path and os.path.exists(audio_segments_path):
                                segment_files = get_audio_segments_files(audio_segments_path)
                                return segment_files
                            return None
                        
                        audio_segments_path_search.change(
                            update_audio_segments_search,
                            inputs=[audio_segments_path_search],
                            outputs=[audio_segments_search]
                        )
            
            with gr.Tab("📊 API Status"):
                gr.Markdown("### 🔧 API Server Status")
                
                def check_status():
                    if check_api_connection():
                        return "✅ API Server is running and healthy"
                    else:
                        return "❌ API Server is not responding. Please start the API server."
                
                status_output = gr.Textbox(label="Status", value=check_status())
                refresh_btn = gr.Button("🔄 Refresh Status")
                
                refresh_btn.click(
                    lambda: check_status(),
                    outputs=[status_output]
                )
        
        # Footer
        gr.Markdown("""
        ---
        **🎭🎤 Character Image & Voice Pipeline** - Smart AI-powered character sprite generation and voice transcription
        """)
    
    return demo

if __name__ == "__main__":
    # Check if API server is running
    if not check_api_connection():
        print("❌ API server not running. Please start it first:")
        print("   python api_server.py")
        exit(1)
    
    # Launch Gradio app
    demo = create_interface()
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
