#!/usr/bin/env python3
"""
Test script for Gemma 3 integration
Run this to verify that Gemma 3 is working correctly
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required imports are available"""
    print("Testing imports...")
    try:
        import torch
        print(f"✓ PyTorch {torch.__version__} imported successfully")
    except ImportError as e:
        print(f"✗ PyTorch import failed: {e}")
        return False
    
    try:
        from transformers import AutoProcessor, Gemma3ForConditionalGeneration
        print("✓ Transformers with Gemma3 imported successfully")
    except ImportError as e:
        print(f"✗ Transformers import failed: {e}")
        return False
    
    try:
        import cv2
        print(f"✓ OpenCV imported successfully")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✓ PIL imported successfully")
    except ImportError as e:
        print(f"✗ PIL import failed: {e}")
        return False
    
    return True

def test_model_loading():
    """Test if Gemma 3 model can be loaded"""
    print("\nTesting model loading...")
    try:
        from services.ai_service import initialize_model
        print("Attempting to load Gemma 3 model...")
        print("Note: This may take several minutes for first-time download...")
        initialize_model()
        print("✓ Gemma 3 model loaded successfully!")
        return True
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        return False

def test_video_analysis():
    """Test video analysis functionality"""
    print("\nTesting video analysis...")
    try:
        from services.ai_service import extract_video_frames
        
        # Look for a test video file
        test_video = None
        for filename in os.listdir('.'):
            if filename.endswith(('.mp4', '.avi', '.mov')):
                test_video = filename
                break
        
        if not test_video:
            print("✗ No test video found. Please add a video file to test.")
            return False
        
        print(f"Testing with video: {test_video}")
        frames, timestamps, duration = extract_video_frames(test_video, num_frames=3)
        
        if frames:
            print(f"✓ Successfully extracted {len(frames)} frames")
            print(f"✓ Video duration: {duration:.2f} seconds")
            print(f"✓ Frame timestamps: {[f'{t:.2f}s' for t in timestamps]}")
            return True
        else:
            print("✗ No frames could be extracted")
            return False
            
    except Exception as e:
        print(f"✗ Video analysis test failed: {e}")
        return False

def main():
    print("Gemma 3 Integration Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n✗ Import test failed. Please install required packages.")
        print("Run: python install_gemma3.py")
        return
    
    # Test model loading
    if not test_model_loading():
        print("\n✗ Model loading test failed.")
        return
    
    # Test video analysis
    if not test_video_analysis():
        print("\n✗ Video analysis test failed.")
        return
    
    print("\n" + "=" * 40)
    print("✓ All tests passed! Gemma 3 integration is working correctly.")
    print("You can now run your video analysis application.")

if __name__ == "__main__":
    main()