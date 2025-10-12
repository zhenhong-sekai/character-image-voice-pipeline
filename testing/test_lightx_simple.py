#!/usr/bin/env python3
"""
Simple LightX Outpainting Test
Quick test of the LightX AI Expand API
"""

import requests
import json
import time
import os

def test_lightx_outpainting():
    """Simple test of LightX outpainting API"""
    
    # Replace with your actual API key
    API_KEY = "c87fbbdea28849dabbba313479687776_0f5f7a6790b64b6997dd4770d2e7b685_andoraitools"
    
    # Test image (use any image from downloaded_images folder)
    test_image = "downloaded_images/donald4.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        print("Please add an image to the downloaded_images folder")
        return
    
    print("🎭 LightX Outpainting API Test")
    print("=" * 40)
    
    # Different headers for different endpoints
    upload_headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    
    expand_headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    
    print(f"   API Key: {API_KEY[:20]}...")  # Show first 20 chars for debugging
    
    # Step 1: Upload image
    print("📤 Step 1: Uploading image...")
    
    file_size = os.path.getsize(test_image)
    print(f"   File size: {file_size} bytes")
    print(f"   File exists: {os.path.exists(test_image)}")
    
    upload_data = {
        "uploadType": "imageUrl",
        "size": file_size,
        "contentType": "image/jpeg"
    }
    
    print(f"   Upload data: {upload_data}")
    
    try:
        # Get upload URL
        upload_response = requests.post(
            "https://api.lightxeditor.com/external/api/v2/uploadImageUrl",
            headers=upload_headers,
            json=upload_data
        )
        
        if upload_response.status_code == 200:
            result = upload_response.json()
            if result["statusCode"] == 2000:
                upload_url = result["body"]["uploadImage"]
                image_url = result["body"]["imageUrl"]
                
                print(f"✅ Upload URL generated: {image_url}")
                
                # Upload actual image with correct headers
                with open(test_image, 'rb') as f:
                    # Set the correct content type for the upload
                    upload_headers = {
                        'Content-Type': 'image/jpeg',
                        'Content-Length': str(file_size)
                    }
                    put_response = requests.put(upload_url, data=f, headers=upload_headers)
                    print(f"   Upload response: {put_response.status_code}")
                    if put_response.status_code == 200:
                        print("✅ Image uploaded successfully")
                    else:
                        print(f"❌ Image upload failed: {put_response.status_code}")
                        print(f"   Response: {put_response.text}")
                        return
            else:
                print(f"❌ Upload failed: {result}")
                return
        else:
            print(f"❌ Upload request failed: {upload_response.status_code}")
            return
    
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return
    
    # Step 2: Request outpainting using the uploaded image URL
    print("\n🎨 Step 2: Requesting outpainting...")
    
    # Use the imageUrl from the upload response (not external URL)
    expand_data = {
        "imageUrl": image_url,  # This should be the LightX uploaded image URL
        "leftPadding": 0,   # Add 50px to left
        "rightPadding": 0,  # Add 50px to right
        "topPadding": 0,   # Add 100px to top
        "bottomPadding": 100, # Add 100px to bottom
        "textPrompt": "Add realistic human body and clothing below the head, extending to mid-thigh level for a cowboy shot, maintaining consistent lighting and style"
    }
    
    print(f"   Expand data: {expand_data}")
    print(f"   Headers: {expand_headers}")
    
    try:
        # Use the correct AI Expand endpoint (v1/expand-photo, not v2/ai-expand)
        expand_response = requests.post(
            "https://api.lightxeditor.com/external/api/v1/expand-photo",
            headers=expand_headers,
            json=expand_data
        )
        
        print(f"   Expand response: {expand_response.status_code}")
        if expand_response.status_code == 200:
            result = expand_response.json()
            print(f"   Expand result: {result}")
            if result["statusCode"] == 2000:
                order_id = result["body"]["orderId"]
                print(f"✅ Outpainting request submitted")
                print(f"   Order ID: {order_id}")
            else:
                print(f"❌ Outpainting request failed: {result}")
                return
        else:
            print(f"❌ Outpainting request failed: {expand_response.status_code}")
            print(f"   Response: {expand_response.text}")
            return
    
    except Exception as e:
        print(f"❌ Outpainting error: {e}")
        return
    
    # Step 3: Check status
    print("\n⏳ Step 3: Checking status...")
    
    for attempt in range(5):  # Max 5 attempts
        try:
            print(f"   Attempt {attempt + 1}/5...")
            
            status_response = requests.post(
                "https://api.lightxeditor.com/external/api/v1/order-status",
                headers=expand_headers,
                json={"orderId": order_id}
            )
            
            if status_response.status_code == 200:
                result = status_response.json()
                if result["statusCode"] == 2000:
                    status = result["body"]["status"]
                    print(f"   Status: {status}")
                    
                    if status == "active":
                        output_url = result["body"]["output"]
                        print(f"✅ Processing complete!")
                        print(f"   Output URL: {output_url}")
                        
                        # Download result
                        print("\n💾 Downloading result...")
                        try:
                            download_response = requests.get(output_url)
                            if download_response.status_code == 200:
                                with open("outpainted_test.jpg", 'wb') as f:
                                    f.write(download_response.content)
                                print("✅ Result saved as 'outpainted_test.jpg'")
                                return True
                            else:
                                print(f"❌ Download failed: {download_response.status_code}")
                                return False
                        except Exception as e:
                            print(f"❌ Download error: {e}")
                            return False
                    elif status == "failed":
                        print("❌ Processing failed")
                        return False
                    else:
                        if attempt < 4:
                            print("   Still processing... waiting 3 seconds")
                            time.sleep(3)
                        else:
                            print("❌ Timeout")
                            return False
                else:
                    print(f"❌ Status check failed: {result}")
                    return False
            else:
                print(f"❌ Status check failed: {status_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return False
    
    return False

if __name__ == "__main__":
    print("🚀 LightX Outpainting API Test")
    print("Make sure to set your API key in the script!")
    print()
    
    success = test_lightx_outpainting()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("Check 'outpainted_test.jpg' for the result")
    else:
        print("\n❌ Test failed")
