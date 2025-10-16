#!/usr/bin/env python3
"""
FastAPI Server for Character Image Pipeline
Provides API endpoints for the Streamlit frontend
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Import our pipeline functions
from character_image_pipeline import (
    detect_faces_yolo, detect_body_parts, analyze_shot_composition,
    analyze_cowboy_shot_potential, check_image_quality, detect_person_count,
    crop_to_target_ratio, comfyui_outpaint_image, archive_previous_images,
    comprehensive_image_validation
)
from google_search_integration import search_and_download_images

app = FastAPI(title="Character Image Pipeline API", version="1.0.0")

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for job status
job_status = {}
UPLOAD_DIR = "uploaded_images"
OUTPUT_DIR = "character_sprites"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "processing", "completed", "error"
    progress: int  # 0-100
    current_step: str
    message: str
    results: Optional[Dict] = None
    error: Optional[str] = None

class PipelineRequest(BaseModel):
    use_google_search: bool = False
    character_name: Optional[str] = None
    max_candidates: int = 5

@app.get("/")
async def root():
    return {"message": "Character Image Pipeline API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image for processing"""
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{file_id}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "file_id": file_id,
            "filename": filename,
            "file_path": file_path,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

class AnalyzeRequest(BaseModel):
    file_path: str

@app.post("/analyze")
async def analyze_image(request: AnalyzeRequest):
    """Analyze a single image and return detailed information"""
    try:
        file_path = request.file_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Quality check
        is_quality_ok, quality_msg = check_image_quality(file_path)
        
        # Person count
        person_count = detect_person_count(file_path)
        
        # Face detection
        faces = detect_faces_yolo(file_path)
        
        # Body parts detection
        body_parts = detect_body_parts(file_path)
        
        # Smart cowboy shot analysis
        cowboy_analysis = analyze_cowboy_shot_potential(file_path, faces)
        
        # Composition analysis
        composition = analyze_shot_composition(body_parts, faces[0]['bbox'] if faces else None)
        
        return {
            "file_path": file_path,
            "quality": {
                "is_ok": is_quality_ok,
                "message": quality_msg
            },
            "person_count": person_count,
            "face_count": len(faces),
            "faces": faces,
            "body_parts": body_parts,
            "composition": composition,
            "cowboy_analysis": cowboy_analysis,
            "analysis_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/process")
async def process_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    """Start the full character image pipeline"""
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    job_status[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        current_step="Initializing",
        message="Starting pipeline..."
    )
    
    # Start background processing
    background_tasks.add_task(run_pipeline_background, job_id, request)
    
    return {"job_id": job_id, "status": "started"}

async def run_pipeline_background(job_id: str, request: PipelineRequest):
    """Background task to run the full pipeline"""
    import time
    start_time = time.time()
    
    try:
        # Update status
        job_status[job_id].status = "processing"
        job_status[job_id].progress = 10
        job_status[job_id].current_step = "Loading images"
        job_status[job_id].message = "Scanning for images..."
        
        # Step 1: Find images
        image_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".avif")
        downloaded_images = []
        
        # Check if Google search is requested
        if request.use_google_search and request.character_name:
            job_status[job_id].progress = 5
            job_status[job_id].current_step = "Google Search"
            job_status[job_id].message = f"Archiving previous images and searching for: {request.character_name}"
            
            # Archive previous images first when using Google search
            archive_path, archived_count = archive_previous_images(request.character_name)
            if archived_count > 0:
                job_status[job_id].message = f"Archived {archived_count} previous images, searching for: {request.character_name}"
            
            try:
                # Use Google search to download exactly max_candidates images
                search_results = search_and_download_images(
                    request.character_name, 
                    num_images=request.max_candidates, 
                    download_dir=UPLOAD_DIR
                )
                if search_results:
                    downloaded_images.extend(search_results)
                    job_status[job_id].message = f"Downloaded {len(search_results)} fresh images from Google"
                else:
                    job_status[job_id].message = "No images found via Google search"
            except Exception as e:
                job_status[job_id].message = f"Google search failed: {str(e)}"
        else:
            # Check uploaded images only when NOT using Google search
            if os.path.exists(UPLOAD_DIR):
                for file in os.listdir(UPLOAD_DIR):
                    if file.lower().endswith(image_extensions):
                        filepath = os.path.join(UPLOAD_DIR, file)
                        downloaded_images.append(filepath)
        
        if not downloaded_images:
            job_status[job_id].status = "error"
            job_status[job_id].error = "No images found for processing. Please upload images or check Google search settings."
            return
        
        job_status[job_id].progress = 20
        job_status[job_id].current_step = "Analyzing images"
        elapsed_time = time.time() - start_time
        job_status[job_id].message = f"Found {len(downloaded_images)} images, analyzing... (⏱️ {elapsed_time:.1f}s elapsed)"
        
        # Step 2: Comprehensive image analysis and validation
        valid_candidates = []
        for i, img_path in enumerate(downloaded_images):
            job_status[job_id].message = f"Analyzing image {i+1}/{len(downloaded_images)}: {os.path.basename(img_path)}"
            job_status[job_id].progress = 20 + (i * 30 // len(downloaded_images))
            
            # Comprehensive validation
            validation = comprehensive_image_validation(img_path)
            
            if not validation['is_valid']:
                print(f"❌ Skipped {os.path.basename(img_path)}: {', '.join(validation['issues'])}")
                continue
            
            # Smart cowboy shot analysis
            faces = validation['face_details']
            cowboy_analysis = analyze_cowboy_shot_potential(img_path, faces)
            
            valid_candidates.append({
                'path': img_path,
                'faces': faces,
                'cowboy_analysis': cowboy_analysis,
                'positioning_score': validation['score'],
                'validation': validation
            })
            
            print(f"✅ Valid candidate: {os.path.basename(img_path)} (score: {validation['score']}/100)")
        
        job_status[job_id].progress = 50
        job_status[job_id].current_step = "Processing candidates"
        elapsed_time = time.time() - start_time
        job_status[job_id].message = f"Found {len(valid_candidates)} valid candidates, processing... (⏱️ {elapsed_time:.1f}s elapsed)"
        
        # Step 3: Process ALL candidates in parallel (true parallel processing)
        processed_sprites = []
        candidates_to_process = valid_candidates[:request.max_candidates]
        
        job_status[job_id].progress = 50
        job_status[job_id].current_step = "Parallel Processing"
        elapsed_time = time.time() - start_time
        job_status[job_id].message = f"Processing {len(candidates_to_process)} candidates in parallel... (⏱️ {elapsed_time:.1f}s elapsed)"
        
        import concurrent.futures
        import threading
        
        def process_single_candidate(candidate_data):
            i, candidate = candidate_data
            input_path = candidate['path']
            output_filename = f"sprite_{i+1:02d}.jpg"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            try:
                # Smart outpainting
                cowboy_analysis = candidate['cowboy_analysis']
                if cowboy_analysis['needs_outpainting']:
                    padding = cowboy_analysis['padding']
                    prompt = cowboy_analysis['prompt']
                    
                    outpainted_path = comfyui_outpaint_image(
                        input_path,
                        left_padding=padding['left'],
                        right_padding=padding['right'],
                        top_padding=padding['top'],
                        bottom_padding=padding['bottom'],
                        text_prompt=prompt
                    )
                    
                    if outpainted_path and os.path.exists(outpainted_path):
                        processed_input = outpainted_path
                    else:
                        processed_input = input_path
                else:
                    processed_input = input_path
                
                # Crop to target ratio
                success, crop_msg = crop_to_target_ratio(processed_input, output_path)
                
                if success:
                    return {
                        'input': input_path,
                        'output': output_path,
                        'score': candidate['positioning_score'],
                        'cowboy_analysis': cowboy_analysis,
                        'candidate_id': i+1,
                        'original_analysis': candidate.get('cowboy_analysis', {}),
                        'validation': candidate.get('validation', {})
                    }
                else:
                    return None
                    
            except Exception as e:
                print(f"Error processing candidate {i+1}: {e}")
                return None
        
        # Process ALL candidates in parallel with ThreadPoolExecutor
        parallel_start_time = time.time()
        max_workers = min(10, len(candidates_to_process))  # Limit to 10 concurrent workers
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks at once
            future_to_candidate = {
                executor.submit(process_single_candidate, (i, candidate)): (i, candidate) 
                for i, candidate in enumerate(candidates_to_process)
            }
            
            # Collect results as they complete
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_candidate):
                completed_count += 1
                result = future.result()
                if result:
                    processed_sprites.append(result)
                
                # Update progress in real-time
                progress_pct = 50 + (completed_count * 40 // len(candidates_to_process))
                elapsed_time = time.time() - start_time
                job_status[job_id].progress = progress_pct
                job_status[job_id].message = f"Completed {completed_count}/{len(candidates_to_process)} candidates (⏱️ {elapsed_time:.1f}s elapsed)"
        
        parallel_elapsed = time.time() - parallel_start_time
        total_elapsed = time.time() - start_time
        job_status[job_id].message = f"Parallel processing completed: {len(processed_sprites)} successful out of {len(candidates_to_process)} candidates (⏱️ parallel: {parallel_elapsed:.1f}s, total: {total_elapsed:.1f}s)"
        
        # Step 4: Final validation
        job_status[job_id].progress = 90
        job_status[job_id].current_step = "Final validation"
        job_status[job_id].message = "Validating final sprites..."
        
        final_sprites = []
        for sprite in processed_sprites:
            output_path = sprite['output']
            img = cv2.imread(output_path)
            if img is not None:
                height, width = img.shape[:2]
                if width == 1024 and height == 1536:
                    faces = detect_faces_yolo(output_path)
                    if faces:
                        final_cowboy_analysis = analyze_cowboy_shot_potential(output_path, faces)
                        final_score = 80 if not final_cowboy_analysis['needs_outpainting'] else 60
                        
                        final_sprites.append({
                            'path': output_path,
                            'input': sprite.get('input', ''),
                            'score': final_score,
                            'cowboy_analysis': final_cowboy_analysis,
                            'original_analysis': sprite.get('cowboy_analysis', {}),
                            'validation': sprite.get('validation', {})
                        })
        
        # Complete
        total_elapsed = time.time() - start_time
        job_status[job_id].status = "completed"
        job_status[job_id].progress = 100
        job_status[job_id].current_step = "Completed"
        job_status[job_id].message = f"Pipeline completed! Generated {len(final_sprites)} character sprites. (⏱️ Total time: {total_elapsed:.1f}s)"
        job_status[job_id].results = {
            "total_sprites": len(final_sprites),
            "sprites": final_sprites,
            "output_directory": OUTPUT_DIR,
            "total_time": total_elapsed,
            "average_time_per_sprite": total_elapsed / max(len(final_sprites), 1)
        }
        
    except Exception as e:
        job_status[job_id].status = "error"
        job_status[job_id].error = str(e)
        job_status[job_id].message = f"Pipeline failed: {str(e)}"

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a pipeline job"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status[job_id].model_dump()

@app.get("/jobs")
async def list_jobs():
    """List all jobs"""
    return {"jobs": list(job_status.keys())}

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del job_status[job_id]
    return {"message": "Job deleted"}

if __name__ == "__main__":
    import cv2
    uvicorn.run(app, host="0.0.0.0", port=8000)
