#!/usr/bin/env python3
"""
ComfyUI Outpainting Module
Replaces LightX outpainting with ComfyUI API
"""

import os
import base64
import json
import requests
import websocket
import uuid
import random
import time
import logging
from datetime import datetime
from threading import Thread

# ComfyUI Configuration
HTTP_SERVER = "http://18.189.25.28:8004"
WS_SERVER = "ws://18.189.25.28:8004/ws"
WORKFLOW_FILE = "working.json"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def comfyui_outpaint_image(image_path, left_padding=0, right_padding=0, top_padding=0, bottom_padding=0, text_prompt=None):
    """
    Use ComfyUI to outpaint an image
    
    Args:
        image_path: Path to the input image
        left_padding, right_padding, top_padding, bottom_padding: Padding in pixels
        text_prompt: Optional text prompt to guide the outpainting
    
    Returns:
        Path to outpainted image or None if failed
    """
    print(f"  🎨 Outpainting with ComfyUI...")
    
    try:
        # Load and encode image
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Load workflow
        with open(WORKFLOW_FILE, "r") as f:
            workflow_data = json.load(f)
        
        # Update image input
        for node_id, node_data in workflow_data.items():
            if node_data.get("class_type") == "ETN_LoadImageBase64":
                node_data["inputs"]["image"] = img_b64
                break
        
        # Update padding in ImagePadForOutpaint node
        for node_id, node_data in workflow_data.items():
            if node_data.get("class_type") == "ImagePadForOutpaint":
                node_data["inputs"]["left"] = left_padding
                node_data["inputs"]["top"] = top_padding
                node_data["inputs"]["right"] = right_padding
                node_data["inputs"]["bottom"] = bottom_padding
                break
        
        # Update text prompt if provided
        if text_prompt:
            for node_id, node_data in workflow_data.items():
                if node_data.get("class_type") == "CLIPTextEncode" and "positive" in str(node_data.get("_meta", {}).get("title", "")):
                    node_data["inputs"]["text"] = text_prompt
                    break
        
        # Generate random seed
        random_seed = random.randint(1, 999999999)
        for node_id, node_data in workflow_data.items():
            if node_data.get("class_type") == "KSampler":
                node_data["inputs"]["seed"] = random_seed
                break
        
        # Submit to ComfyUI
        client_id = str(uuid.uuid4())
        payload = {"prompt": workflow_data, "client_id": client_id}
        
        # Submit workflow
        resp = requests.post(f"{HTTP_SERVER}/prompt", json=payload)
        if resp.status_code != 200:
            print(f"  ❌ ComfyUI submission failed: {resp.status_code}")
            return None
        
        response_data = resp.json()
        prompt_id = response_data.get("prompt_id")
        
        # Wait for completion
        print(f"  ⏳ Waiting for ComfyUI execution...")
        timeout = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check queue status
            queue_response = requests.get(f"{HTTP_SERVER}/queue")
            if queue_response.status_code == 200:
                queue_data = queue_response.json()
                if not queue_data.get('queue_running') and not queue_data.get('queue_pending'):
                    break
            time.sleep(2)
        
        # Wait for server to save image
        time.sleep(5)
        
        # Retrieve output image
        history_response = requests.get(f"{HTTP_SERVER}/history")
        if history_response.status_code == 200:
            history_data = history_response.json()
            if prompt_id and prompt_id in history_data:
                entry = history_data[prompt_id]
                outputs = entry.get('outputs', {})
                
                for node_id, node_output in outputs.items():
                    if 'images' in node_output:
                        for img_info in node_output['images']:
                            filename = img_info.get('filename', '')
                            if filename:
                                # Download the image
                                img_response = requests.get(f"{HTTP_SERVER}/view", params={
                                    "filename": filename,
                                    "subfolder": "",
                                    "type": "output"
                                })
                                
                                if img_response.status_code == 200:
                                    # Save outpainted image
                                    outpainted_path = image_path.replace('.jpg', '_outpainted.jpg').replace('.jpeg', '_outpainted.jpg').replace('.png', '_outpainted.jpg')
                                    with open(outpainted_path, 'wb') as f:
                                        f.write(img_response.content)
                                    print(f"  ✅ ComfyUI outpainting complete!")
                                    print(f"  💾 Saved: {os.path.basename(outpainted_path)}")
                                    return outpainted_path
        
        print(f"  ❌ ComfyUI outpainting failed")
        return None
        
    except Exception as e:
        print(f"  ❌ ComfyUI outpainting error: {e}")
        return None
