#!/usr/bin/env python3
"""
Quick Speed Test for Round 2 Optimizations
Tests the optimized system for sub-1000ms performance
"""

import asyncio
import time
import os
from services.ai_service import extract_video_frames, analyze_video_with_gemini, generate_chat_response
from config import Config

def test_frame_extraction_speed():
    """Test frame extraction speed"""
    print("🚀 Testing Frame Extraction Speed...")
    
    # Try to find a test video
    test_video = None
    if os.path.exists(Config.DEFAULT_VIDEO_PATH):
        test_video = Config.DEFAULT_VIDEO_PATH
    elif os.path.exists(Config.UPLOAD_FOLDER):
        for file in os.listdir(Config.UPLOAD_FOLDER):
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.webm', '.mkv')):
                test_video = os.path.join(Config.UPLOAD_FOLDER, file)
                break
    
    if not test_video:
        print("⚠️ No test video found, skipping frame extraction test")
        return None
    
    # Test multiple runs
    times = []
    for i in range(3):
        start_time = time.time()
        frames, timestamps, duration = extract_video_frames(test_video, num_frames=1)
        extraction_time = (time.time() - start_time) * 1000
        times.append(extraction_time)
        print(f"  Run {i+1}: {extraction_time:.1f}ms")
    
    avg_time = sum(times) / len(times)
    print(f"📊 Average frame extraction: {avg_time:.1f}ms")
    
    if avg_time < 1000:
        print("✅ Frame extraction meets sub-1000ms target!")
    else:
        print("❌ Frame extraction exceeds 1000ms target")
    
    return avg_time

def test_chat_response_speed():
    """Test chat response speed"""
    print("\n🚀 Testing Chat Response Speed...")
    
    mock_analysis = "Test video shows a car on track"
    test_message = "What do you see?"
    
    times = []
    for i in range(3):
        start_time = time.time()
        response = generate_chat_response(
            mock_analysis, "test", "test", test_message, []
        )
        response_time = (time.time() - start_time) * 1000
        times.append(response_time)
        print(f"  Run {i+1}: {response_time:.1f}ms")
    
    avg_time = sum(times) / len(times)
    print(f"📊 Average chat response: {avg_time:.1f}ms")
    
    if avg_time < 1000:
        print("✅ Chat response meets sub-1000ms target!")
    else:
        print("❌ Chat response exceeds 1000ms target")
    
    return avg_time

async def test_full_analysis_speed():
    """Test full video analysis speed"""
    print("\n🚀 Testing Full Analysis Speed...")
    
    # Find test video
    test_video = None
    if os.path.exists(Config.DEFAULT_VIDEO_PATH):
        test_video = Config.DEFAULT_VIDEO_PATH
    elif os.path.exists(Config.UPLOAD_FOLDER):
        for file in os.listdir(Config.UPLOAD_FOLDER):
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.webm', '.mkv')):
                test_video = os.path.join(Config.UPLOAD_FOLDER, file)
                break
    
    if not test_video:
        print("⚠️ No test video found, skipping analysis test")
        return None
    
    start_time = time.time()
    result = await analyze_video_with_gemini(test_video, "test", "quick test")
    analysis_time = (time.time() - start_time) * 1000
    
    print(f"📊 Full analysis time: {analysis_time:.1f}ms")
    
    if analysis_time < 1000:
        print("✅ Full analysis meets sub-1000ms target!")
    else:
        print("❌ Full analysis exceeds 1000ms target")
    
    return analysis_time

async def main():
    """Run speed tests"""
    print("🏃‍♂️ Round 2 Speed Test - Optimized System")
    print("=" * 50)
    
    # Test frame extraction
    frame_time = test_frame_extraction_speed()
    
    # Test chat response
    chat_time = test_chat_response_speed()
    
    # Test full analysis
    analysis_time = await test_full_analysis_speed()
    
    # Summary
    print("\n📊 SPEED TEST SUMMARY")
    print("=" * 50)
    
    all_tests_pass = True
    
    if frame_time:
        status = "✅ PASS" if frame_time < 1000 else "❌ FAIL"
        print(f"Frame Extraction: {frame_time:.1f}ms {status}")
        if frame_time >= 1000:
            all_tests_pass = False
    
    if chat_time:
        status = "✅ PASS" if chat_time < 1000 else "❌ FAIL"
        print(f"Chat Response: {chat_time:.1f}ms {status}")
        if chat_time >= 1000:
            all_tests_pass = False
    
    if analysis_time:
        status = "✅ PASS" if analysis_time < 1000 else "❌ FAIL"
        print(f"Full Analysis: {analysis_time:.1f}ms {status}")
        if analysis_time >= 1000:
            all_tests_pass = False
    
    print(f"\nTarget: < 1000ms for all operations")
    
    if all_tests_pass:
        print("🎉 ALL TESTS PASS - Round 2 Performance Target Met!")
        print("🚀 System is optimized for sub-1000ms latency")
    else:
        print("⚠️ SOME TESTS FAIL - Further optimization needed")
        print("🔧 Consider reducing token limits or using smaller model")
    
    # Configuration summary
    print(f"\n⚙️ Current Configuration:")
    print(f"  - Max Output Tokens: {Config.MAX_OUTPUT_TOKENS}")
    print(f"  - Chat Max Tokens: {Config.CHAT_MAX_TOKENS}")
    print(f"  - Max Frames (Short): {Config.MAX_FRAMES_SHORT_VIDEO}")
    print(f"  - Max Frames (Long): {Config.MAX_FRAMES_LONG_VIDEO}")
    print(f"  - Temperature: {Config.TEMPERATURE}")
    print(f"  - Top K: {Config.TOP_K}")

if __name__ == "__main__":
    asyncio.run(main())