#!/usr/bin/env python3
"""
LightX AI Expand (Outpainting) API Test Script
Based on: https://docs.lightxeditor.com/api/ai-expand#quick-steps-to-generate-with-your-api
"""

import requests
import json
import time
import os
from pathlib import Path

class LightXOutpaintingAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.lightxeditor.com/external/api"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }
    
    def upload_image(self, image_path):
        """Step 1: Upload image to get imageUrl"""
        print(f"📤 Step 1: Uploading image {os.path.basename(image_path)}")
        
        # Get file info
        file_size = os.path.getsize(image_path)
        file_ext = Path(image_path).suffix.lower()
        
        # Determine content type
        content_type = "image/jpeg" if file_ext in ['.jpg', '.jpeg'] else "image/png"
        
        # Request upload URL
        upload_url = f"{self.base_url}/v2/uploadImageUrl"
        upload_data = {
            "uploadType": "imageUrl",
            "size": file_size,
            "contentType": content_type
        }
        
        try:
            response = requests.post(upload_url, headers=self.headers, json=upload_data)
            response.raise_for_status()
            
            result = response.json()
            if result["statusCode"] == 2000:
                upload_image_url = result["body"]["uploadImage"]
                image_url = result["body"]["imageUrl"]
                
                print(f"✅ Upload URL generated")
                print(f"   Image URL: {image_url}")
                
                # Upload the actual image file
                with open(image_path, 'rb') as f:
                    upload_response = requests.put(upload_image_url, data=f)
                    upload_response.raise_for_status()
                
                print(f"✅ Image uploaded successfully")
                return image_url
            else:
                print(f"❌ Upload failed: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None
    
    def expand_image(self, image_url, left_padding=0, right_padding=0, top_padding=0, bottom_padding=0):
        """Step 2: Request AI Expand (outpainting)"""
        print(f"🎨 Step 2: Requesting AI Expand")
        print(f"   Padding: L:{left_padding} R:{right_padding} T:{top_padding} B:{bottom_padding}")
        
        expand_url = f"{self.base_url}/v2/ai-expand"
        expand_data = {
            "imageUrl": image_url,
            "leftPadding": left_padding,
            "rightPadding": right_padding,
            "topPadding": top_padding,
            "bottomPadding": bottom_padding
        }
        
        try:
            response = requests.post(expand_url, headers=self.headers, json=expand_data)
            response.raise_for_status()
            
            result = response.json()
            if result["statusCode"] == 2000:
                order_id = result["body"]["orderId"]
                max_retries = result["body"]["maxRetriesAllowed"]
                avg_time = result["body"]["avgResponseTimeInSec"]
                
                print(f"✅ Expand request submitted")
                print(f"   Order ID: {order_id}")
                print(f"   Max retries: {max_retries}")
                print(f"   Avg response time: {avg_time}s")
                
                return order_id
            else:
                print(f"❌ Expand request failed: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Expand error: {e}")
            return None
    
    def check_status(self, order_id, max_retries=5):
        """Step 3: Check status until completion"""
        print(f"⏳ Step 3: Checking status for order {order_id}")
        
        status_url = f"{self.base_url}/v1/order-status"
        status_data = {"orderId": order_id}
        
        for attempt in range(max_retries):
            try:
                print(f"   Attempt {attempt + 1}/{max_retries}...")
                
                response = requests.post(status_url, headers=self.headers, json=status_data)
                response.raise_for_status()
                
                result = response.json()
                
                if result["statusCode"] == 2000:
                    status = result["body"]["status"]
                    print(f"   Status: {status}")
                    
                    if status == "active":
                        output_url = result["body"]["output"]
                        print(f"✅ Processing complete!")
                        print(f"   Output URL: {output_url}")
                        return output_url
                    elif status == "failed":
                        print(f"❌ Processing failed")
                        return None
                    else:  # status == "init" (processing)
                        if attempt < max_retries - 1:
                            print(f"   Still processing... waiting 3 seconds")
                            time.sleep(3)
                        else:
                            print(f"❌ Timeout after {max_retries} attempts")
                            return None
                else:
                    print(f"❌ Status check failed: {result}")
                    return None
                    
            except Exception as e:
                print(f"❌ Status check error: {e}")
                return None
        
        return None
    
    def download_result(self, output_url, output_path):
        """Step 4: Download the result image"""
        print(f"💾 Step 4: Downloading result to {output_path}")
        
        try:
            response = requests.get(output_url)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Result downloaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Download error: {e}")
            return False
    
    def process_outpainting(self, image_path, output_path, left=0, right=0, top=0, bottom=0):
        """Complete outpainting workflow"""
        print("🎭 LightX AI Expand (Outpainting) Test")
        print("=" * 50)
        
        # Step 1: Upload image
        image_url = self.upload_image(image_path)
        if not image_url:
            return False
        
        # Step 2: Request expansion
        order_id = self.expand_image(image_url, left, right, top, bottom)
        if not order_id:
            return False
        
        # Step 3: Check status
        output_url = self.check_status(order_id)
        if not output_url:
            return False
        
        # Step 4: Download result
        success = self.download_result(output_url, output_path)
        return success

def main():
    # Configuration
    API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual API key
    
    # Test parameters
    input_image = "downloaded_images/sample_person.jpg"  # Test image
    output_image = "outpainted_result.jpg"
    
    # Padding settings (pixels to add to each side)
    padding_settings = {
        "left": 100,    # Add 100px to left
        "right": 100,   # Add 100px to right  
        "top": 200,     # Add 200px to top
        "bottom": 200   # Add 200px to bottom
    }
    
    print("🚀 Starting LightX Outpainting Test")
    print(f"Input: {input_image}")
    print(f"Output: {output_image}")
    print(f"Padding: {padding_settings}")
    print()
    
    # Check if input image exists
    if not os.path.exists(input_image):
        print(f"❌ Input image not found: {input_image}")
        print("Please add an image to the downloaded_images folder")
        return
    
    # Initialize API
    api = LightXOutpaintingAPI(API_KEY)
    
    # Run outpainting
    success = api.process_outpainting(
        input_image, 
        output_image,
        **padding_settings
    )
    
    if success:
        print("\n🎉 Outpainting test completed successfully!")
        print(f"Check the result: {output_image}")
    else:
        print("\n❌ Outpainting test failed")

if __name__ == "__main__":
    main()
