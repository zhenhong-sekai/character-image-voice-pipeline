import websocket
import requests
import json
import base64
import uuid
import logging
import os
import random
from datetime import datetime
from threading import Thread

# === Configuration ===
HTTP_SERVER = "http://18.189.25.28:8004"
WS_SERVER = "ws://18.189.25.28:8004/ws"
WORKFLOW_FILE = "working.json"
IMAGE_PATH = "input.jpeg"

# === Setup Logging ===
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("comfyui_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("=== ComfyUI API Test Started ===")

# === Load and encode image ===
if not os.path.exists(IMAGE_PATH):
    raise FileNotFoundError(f"Image file not found: {IMAGE_PATH}")

with open(IMAGE_PATH, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("utf-8")

logger.info(f"Image encoded: {len(img_b64)} characters")

# === Load workflow JSON ===
if not os.path.exists(WORKFLOW_FILE):
    raise FileNotFoundError(f"Workflow not found: {WORKFLOW_FILE}")

with open(WORKFLOW_FILE, "r") as f:
    workflow_data = json.load(f)

# Handle ComfyUI format (workflow2.json) vs simple format (workflow.json)
if "nodes" in workflow_data:
    # ComfyUI format - find image input node automatically
    logger.info("Detected ComfyUI format workflow")
    image_node = None
    for node in workflow_data["nodes"]:
        node_type = node.get("type", "")
        if node_type in ["ETN_LoadImageBase64", "LoadImage"]:
            image_node = node
            break
    
    if not image_node:
        raise KeyError("No image input node found in ComfyUI workflow")
    
    # Handle different image node types
    node_type = image_node.get("type", "")
    if node_type == "ETN_LoadImageBase64":
        # Update the node's widgets_values to include the base64 image
        if "widgets_values" not in image_node:
            image_node["widgets_values"] = []
        
        # Set the base64 image as the first widget value
        if len(image_node["widgets_values"]) == 0:
            image_node["widgets_values"].append(img_b64)
        else:
            image_node["widgets_values"][0] = img_b64
        
        logger.info(f"Injected base64 image into ComfyUI workflow node {image_node['id']}")
    elif node_type == "LoadImage":
        # For LoadImage nodes, the image file should be available on server
        logger.info(f"Using LoadImage node {image_node['id']} - image file should be on server")
    else:
        logger.warning(f"Unknown node type: {node_type}")
    
    workflow = workflow_data
else:
    # Simple format - find image input node automatically
    logger.info("Detected simple format workflow")
    
    # Find the image input node (more flexible than hardcoded "1")
    image_node_id = None
    for node_id, node_data in workflow_data.items():
        node_class = node_data.get("class_type", "")
        if node_class in ["ETN_LoadImageBase64", "LoadImage"]:
            image_node_id = node_id
            break
    
    if not image_node_id:
        raise KeyError("No image input node found in workflow")
    
    node_class = workflow_data[image_node_id].get("class_type", "")
    if node_class == "ETN_LoadImageBase64":
        # Inject base64 data for ETN_LoadImageBase64 nodes
        workflow_data[image_node_id]["inputs"]["image"] = img_b64
        logger.info(f"Injected base64 image into ETN_LoadImageBase64 node {image_node_id}")
        
        # Generate random seed to avoid caching
        random_seed = random.randint(1, 999999999)
        logger.info(f"Generated random seed: {random_seed}")
        
        # Find and update the seed in the workflow
        for node_id, node_data in workflow_data.items():
            if node_data.get("class_type") == "KSampler" and "seed" in node_data.get("inputs", {}):
                workflow_data[node_id]["inputs"]["seed"] = random_seed
                logger.info(f"Updated seed in KSampler node {node_id} to {random_seed}")
                break
    elif node_class == "LoadImage":
        # For LoadImage nodes, the image file should be available on server
        logger.info(f"Using LoadImage node {image_node_id} - image file should be on server")
    else:
        logger.warning(f"Unknown node type: {node_class}")
    
    workflow = workflow_data

client_id = str(uuid.uuid4())
logger.info(f"Client ID: {client_id}")

# ComfyUI expects the workflow in a specific format
if "nodes" in workflow:
    # For ComfyUI format, we need to send the entire workflow structure
    payload = {"prompt": workflow, "client_id": client_id}
    logger.info("Sending ComfyUI format workflow")
else:
    # For simple format, wrap in prompt
    payload = {"prompt": workflow, "client_id": client_id}
    logger.info("Sending simple format workflow")

# === Step 1: Open WebSocket listener ===
def listen_to_ws():
    logger.info("Connecting to WebSocket for updates...")
    ws = None
    execution_completed = False
    
    try:
        ws = websocket.WebSocket()
        # Connect with the same client_id to receive updates for our prompt
        ws_url = f"{WS_SERVER}?clientId={client_id}"
        logger.info(f"Connecting to: {ws_url}")
        ws.connect(ws_url)
        logger.info("Connected to WebSocket.")

        while not execution_completed:
            try:
                msg = ws.recv()
                data = json.loads(msg)
                msg_type = data.get("type")

                if msg_type == "execution_start":
                    logger.info("🚀 Execution started")
                elif msg_type == "executing":
                    node_info = data.get('data', {})
                    node_id = node_info.get('node')
                    logger.info(f"Running node: {node_id}")
                elif msg_type == "progress":
                    progress_info = data.get('data', {})
                    progress_value = progress_info.get('value', '?')
                    progress_max = progress_info.get('max', '?')
                    logger.info(f"📈 Progress: {progress_value}/{progress_max}")
                elif msg_type == "execution_end":
                    logger.info("✅ Execution finished")
                    execution_completed = True
                    break
                elif msg_type == "execution_error":
                    logger.error(f"❌ Execution error: {data}")
                    execution_completed = True
                    break
                elif msg_type == "image":
                    logger.info("🖼️ Received output image via WebSocket")
                    try:
                        img_data = base64.b64decode(data["data"]["image"])
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"output_websocket_{timestamp}.png"
                        with open(filename, "wb") as out:
                            out.write(img_data)
                        logger.info(f"✅ Saved result as {filename}")
                        execution_completed = True
                        break
                    except Exception as e:
                        logger.error(f"Error saving WebSocket image: {e}")
                elif msg_type == "binary":
                    logger.info("🖼️ Received binary image data via WebSocket")
                    try:
                        # Handle binary image data
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"output_binary_{timestamp}.png"
                        with open(filename, "wb") as out:
                            out.write(msg)
                        logger.info(f"✅ Saved binary image as {filename}")
                        execution_completed = True
                        break
                    except Exception as e:
                        logger.error(f"Error saving binary image: {e}")
                else:
                    logger.debug(f"Other message: {msg_type}")
                    
            except websocket.WebSocketConnectionClosedException:
                logger.warning("WebSocket connection closed, attempting to reconnect...")
                try:
                    ws.close()
                    ws = websocket.WebSocket()
                    ws_url = f"{WS_SERVER}?clientId={client_id}"
                    ws.connect(ws_url)
                    logger.info("Reconnected to WebSocket.")
                except Exception as e:
                    logger.error(f"Failed to reconnect: {e}")
                    break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        if ws:
            try:
                ws.close()
            except:
                pass

# Run listener thread
listener = Thread(target=listen_to_ws, daemon=True)
listener.start()

# === Step 2: POST workflow to /prompt ===
logger.info("Submitting workflow to ComfyUI /prompt ...")
logger.debug(f"Payload size: {len(json.dumps(payload))} characters")
logger.debug(f"Payload structure: {json.dumps(payload, indent=2)[:1000]}...")

resp = requests.post(f"{HTTP_SERVER}/prompt", json=payload)
logger.info(f"Response status: {resp.status_code}")
if resp.status_code == 200:
    logger.info("Workflow successfully submitted to ComfyUI.")
    logger.info(f"Response: {resp.text}")
    
    # Extract prompt_id from response
    try:
        response_data = resp.json()
        prompt_id = response_data.get("prompt_id")
        logger.info(f"Prompt ID: {prompt_id}")
    except Exception as e:
        logger.warning(f"Could not extract prompt_id from response: {e}")
        prompt_id = None
else:
    logger.error(f"Failed to submit workflow: {resp.status_code} {resp.text}")
    exit(1)

# === Step 3: Wait for execution to complete ===
import time
timeout = 300  # 5 minutes timeout
start_time = time.time()
execution_completed = False

logger.info("Waiting for execution to complete...")
while not execution_completed and (time.time() - start_time) < timeout:
    # Check if WebSocket listener is still alive
    if not listener.is_alive():
        logger.info("WebSocket listener finished")
        break
    
    # Check queue status to see if execution is still running
    try:
        queue_response = requests.get(f"{HTTP_SERVER}/queue")
        if queue_response.status_code == 200:
            queue_data = queue_response.json()
            if not queue_data.get('queue_running') and not queue_data.get('queue_pending'):
                logger.info("✅ Queue is empty - execution completed")
                execution_completed = True
                break
            else:
                logger.info("⏳ Execution still running...")
    except Exception as e:
        logger.warning(f"Error checking queue: {e}")
    
    time.sleep(2)  # Check every 2 seconds

if not execution_completed:
    logger.warning("Timeout reached or execution not completed")
else:
    logger.info("✅ Execution completed successfully")

# === Step 4: Check queue status ===
logger.info("Checking queue status...")
try:
    queue_response = requests.get(f"{HTTP_SERVER}/queue")
    if queue_response.status_code == 200:
        queue_data = queue_response.json()
        logger.info(f"Queue status: {queue_data}")
    else:
        logger.warning(f"Failed to get queue status: {queue_response.status_code}")
except Exception as e:
    logger.error(f"Error checking queue status: {e}")

# === Step 5: Wait a moment for server to save the image ===
logger.info("Waiting for server to save the output image...")
time.sleep(5)  # Give server time to save the image

# === Step 6: Try to retrieve output image via /view endpoint ===
logger.info("Attempting to retrieve output image via /view endpoint...")
try:
    # First, try to get the history to see what files were actually generated
    history_response = requests.get(f"{HTTP_SERVER}/history")
    if history_response.status_code == 200:
        history_data = history_response.json()
        logger.info(f"Found {len(history_data)} history entries")
        
        # Look for our prompt_id in the history
        if prompt_id and prompt_id in history_data:
            entry = history_data[prompt_id]
            logger.info(f"Found our execution in history: {prompt_id}")
            
            # Check if execution completed successfully
            status = entry.get('status', {})
            if status.get('completed', False):
                logger.info("✅ Execution completed successfully")
                
                # Look for output files
                outputs = entry.get('outputs', {})
                logger.info(f"Output nodes: {list(outputs.keys())}")
                
                # Try to find and download output images
                for node_id, node_output in outputs.items():
                    if 'images' in node_output:
                        for img_info in node_output['images']:
                            filename = img_info.get('filename', '')
                            subfolder = img_info.get('subfolder', '')
                            if filename:
                                logger.info(f"Found output file: {filename} in subfolder: {subfolder}")
                                
                                # Try to download the image
                                img_response = requests.get(f"{HTTP_SERVER}/view", params={
                                    "filename": filename,
                                    "subfolder": subfolder,
                                    "type": "output"
                                })
                                
                                if img_response.status_code == 200:
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    output_filename = f"output_{timestamp}_{filename}"
                                    with open(output_filename, "wb") as out:
                                        out.write(img_response.content)
                                    logger.info(f"✅ Successfully downloaded {filename} as {output_filename}")
                                    break
                                else:
                                    logger.warning(f"Failed to download {filename}: {img_response.status_code}")
                        else:
                            continue
                        break
                else:
                    logger.warning("No output images found in history")
            else:
                logger.warning("Execution not completed yet")
        else:
            logger.warning("Our execution not found in history yet")
    else:
        logger.warning(f"Failed to get history: {history_response.status_code}")
        
    # Fallback: Try common filename patterns with multiple attempts
    logger.info("Trying common filename patterns...")
    common_patterns = [
        "ComfyUI_00001.png",
        "ComfyUI_00002.png", 
        "ComfyUI_00003.png",
        "ComfyUI_00004.png",
        "ComfyUI_00005.png",
        "comfyui_output_00001.png",
        "comfyui_output_00002.png",
        "ComfyUI_temp_00001.png",
        "ComfyUI_temp_00002.png",
        "output_00001.png",
        "output_00002.png"
    ]
    
    for pattern in common_patterns:
        view_response = requests.get(f"{HTTP_SERVER}/view", params={
            "filename": pattern,
            "subfolder": "",
            "type": "output"
        })
        
        if view_response.status_code == 200:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"output_fallback_{timestamp}.png"
            with open(output_filename, "wb") as out:
                out.write(view_response.content)
            logger.info(f"✅ Retrieved image using pattern {pattern} as {output_filename}")
            break
    else:
        logger.warning("Could not find output image with any common pattern")
            
except Exception as e:
    logger.error(f"Error retrieving image via /view endpoint: {e}")

logger.info("=== ComfyUI API Test Completed ===")
