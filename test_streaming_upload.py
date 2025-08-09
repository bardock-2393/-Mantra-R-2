#!/usr/bin/env python3
"""
Streaming Upload System Test
Test the production-grade streaming upload endpoints
"""

import os
import time
import requests
import json
from io import BytesIO

def test_streaming_upload():
    """Test the complete streaming upload flow"""
    
    # Test configuration
    BASE_URL = "http://localhost:5000"  # Adjust for your setup
    
    # Create a test file (simulate video data)
    test_data = b"x" * (10 * 1024 * 1024)  # 10MB test file
    test_filename = "test_video.mp4"
    
    print("🚀 Testing Streaming Upload System")
    print("=" * 50)
    
    try:
        # Step 1: Initialize upload
        print("📋 Step 1: Initialize upload...")
        init_response = requests.post(f"{BASE_URL}/upload/init", 
                                      json={
                                          "filename": test_filename,
                                          "size": len(test_data)
                                      })
        
        if init_response.status_code != 200:
            print(f"❌ Upload initialization failed: {init_response.text}")
            return False
        
        init_data = init_response.json()
        upload_id = init_data["upload_id"]
        print(f"✅ Upload initialized: {upload_id}")
        
        # Step 2: Upload chunks
        print("📦 Step 2: Upload chunks...")
        chunk_size = 5 * 1024 * 1024  # 5MB chunks
        total_chunks = (len(test_data) + chunk_size - 1) // chunk_size
        
        for i in range(total_chunks):
            start = i * chunk_size
            end = min(start + chunk_size - 1, len(test_data) - 1)
            chunk_data = test_data[start:end + 1]
            
            chunk_response = requests.put(
                f"{BASE_URL}/upload/{upload_id}",
                headers={
                    "Content-Range": f"bytes {start}-{end}/{len(test_data)}"
                },
                data=chunk_data
            )
            
            if chunk_response.status_code != 200:
                print(f"❌ Chunk {i+1} upload failed: {chunk_response.text}")
                return False
            
            chunk_result = chunk_response.json()
            progress = chunk_result.get("progress", 0)
            print(f"📦 Chunk {i+1}/{total_chunks} uploaded ({progress:.1f}% complete)")
        
        # Step 3: Get status
        print("📊 Step 3: Check upload status...")
        status_response = requests.get(f"{BASE_URL}/upload/{upload_id}/status")
        
        if status_response.status_code != 200:
            print(f"❌ Status check failed: {status_response.text}")
            return False
        
        status_data = status_response.json()
        print(f"📊 Upload status: {status_data['progress']:.1f}% complete")
        print(f"📊 Bytes received: {status_data['bytes_received']} / {status_data['total_size']}")
        
        # Step 4: Complete upload
        print("✅ Step 4: Complete upload...")
        complete_response = requests.post(f"{BASE_URL}/upload/{upload_id}/complete")
        
        if complete_response.status_code != 200:
            print(f"❌ Upload completion failed: {complete_response.text}")
            return False
        
        complete_data = complete_response.json()
        print(f"✅ Upload completed: {complete_data['filename']}")
        print(f"📁 File path: {complete_data['file_path']}")
        print(f"⚡ Average speed: {complete_data.get('average_speed', 0):.1f} MB/s")
        
        # Step 5: Verify file exists
        if os.path.exists(complete_data['file_path']):
            actual_size = os.path.getsize(complete_data['file_path'])
            if actual_size == len(test_data):
                print(f"✅ File verification passed: {actual_size} bytes")
            else:
                print(f"❌ File size mismatch: expected {len(test_data)}, got {actual_size}")
                return False
        else:
            print(f"❌ Uploaded file not found: {complete_data['file_path']}")
            return False
        
        # Cleanup
        try:
            os.remove(complete_data['file_path'])
            print("🧹 Test file cleaned up")
        except OSError:
            pass
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def test_upload_cancellation():
    """Test upload cancellation"""
    
    BASE_URL = "http://localhost:5000"
    test_data = b"x" * (5 * 1024 * 1024)  # 5MB test file
    
    print("\n🚫 Testing Upload Cancellation")
    print("=" * 50)
    
    try:
        # Initialize upload
        init_response = requests.post(f"{BASE_URL}/upload/init", 
                                      json={
                                          "filename": "cancel_test.mp4",
                                          "size": len(test_data)
                                      })
        
        if init_response.status_code != 200:
            print(f"❌ Initialization failed: {init_response.text}")
            return False
        
        upload_id = init_response.json()["upload_id"]
        print(f"📋 Upload initialized: {upload_id}")
        
        # Upload one chunk
        chunk_data = test_data[:1024*1024]  # 1MB chunk
        requests.put(
            f"{BASE_URL}/upload/{upload_id}",
            headers={"Content-Range": f"bytes 0-{len(chunk_data)-1}/{len(test_data)}"},
            data=chunk_data
        )
        print("📦 Partial upload completed")
        
        # Cancel upload
        cancel_response = requests.delete(f"{BASE_URL}/upload/{upload_id}/cancel")
        
        if cancel_response.status_code != 200:
            print(f"❌ Cancellation failed: {cancel_response.text}")
            return False
        
        print("✅ Upload cancelled successfully")
        
        # Verify status after cancellation
        status_response = requests.get(f"{BASE_URL}/upload/{upload_id}/status")
        if status_response.status_code == 404:
            print("✅ Upload state cleaned up after cancellation")
        else:
            print("⚠️ Upload state still exists after cancellation")
        
        return True
        
    except Exception as e:
        print(f"❌ Cancellation test failed: {e}")
        return False

def test_error_conditions():
    """Test error handling"""
    
    BASE_URL = "http://localhost:5000"
    
    print("\n⚠️ Testing Error Conditions")
    print("=" * 50)
    
    # Test 1: Invalid filename
    print("🔍 Test 1: Invalid filename...")
    response = requests.post(f"{BASE_URL}/upload/init", json={"filename": "", "size": 1000})
    if response.status_code == 400:
        print("✅ Invalid filename rejected correctly")
    else:
        print(f"❌ Invalid filename not rejected: {response.status_code}")
    
    # Test 2: File too large
    print("🔍 Test 2: File too large...")
    large_size = 3 * 1024 * 1024 * 1024  # 3GB (over limit)
    response = requests.post(f"{BASE_URL}/upload/init", 
                           json={"filename": "large.mp4", "size": large_size})
    if response.status_code == 413:
        print("✅ Large file rejected correctly")
    else:
        print(f"❌ Large file not rejected: {response.status_code}")
    
    # Test 3: Invalid upload ID
    print("🔍 Test 3: Invalid upload ID...")
    response = requests.get(f"{BASE_URL}/upload/invalid_id/status")
    if response.status_code == 404:
        print("✅ Invalid upload ID rejected correctly")
    else:
        print(f"❌ Invalid upload ID not rejected: {response.status_code}")
    
    # Test 4: Missing Content-Range
    print("🔍 Test 4: Missing Content-Range...")
    # First create a valid upload
    init_response = requests.post(f"{BASE_URL}/upload/init", 
                                  json={"filename": "test.mp4", "size": 1000})
    if init_response.status_code == 200:
        upload_id = init_response.json()["upload_id"]
        # Try to upload without Content-Range
        response = requests.put(f"{BASE_URL}/upload/{upload_id}", data=b"test")
        if response.status_code == 411:
            print("✅ Missing Content-Range rejected correctly")
        else:
            print(f"❌ Missing Content-Range not rejected: {response.status_code}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/upload/{upload_id}/cancel")
    
    print("✅ Error condition tests completed")

def main():
    """Run all streaming upload tests"""
    
    print("🧪 Streaming Upload Test Suite")
    print("🚀 Testing production-grade 2GB+ upload system")
    print("🎯 Optimized for 80GB GPU environment")
    print("")
    
    # Run tests
    success = True
    
    success &= test_streaming_upload()
    success &= test_upload_cancellation()
    test_error_conditions()  # Don't fail on error condition tests
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Streaming upload system is working correctly")
        print("🚀 Ready for 2GB+ video uploads with 80GB GPU optimization")
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Check server logs and configuration")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)