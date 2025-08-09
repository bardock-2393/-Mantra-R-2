"""
High-Performance Video Streaming Service - Round 2 Feature
Supports real-time 90 FPS video stream processing for live analysis
"""

import cv2
import threading
import queue
import time
import numpy as np
from typing import Optional, Callable, Dict, Any
from PIL import Image
from config import Config
from services.performance_service import measure_latency, cache_manager

class HighFPSVideoStream:
    """High-performance video stream processor for 90 FPS support"""
    
    def __init__(self, source: str, target_fps: int = 90):
        self.source = source
        self.target_fps = target_fps
        self.frame_queue = queue.Queue(maxsize=10)  # Buffer frames
        self.processing_queue = queue.Queue(maxsize=5)  # Processed frames
        self.is_streaming = False
        self.capture_thread = None
        self.process_thread = None
        self.frame_processor: Optional[Callable] = None
        
        # Performance tracking
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.actual_fps = 0
        
        print(f"🎬 High-FPS Video Stream initialized for {target_fps} FPS")
    
    @measure_latency("stream_start")
    def start_stream(self, frame_processor: Optional[Callable] = None):
        """Start high-performance video streaming"""
        if self.is_streaming:
            return
        
        self.frame_processor = frame_processor
        self.is_streaming = True
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        self.capture_thread.start()
        
        # Start processing thread if processor provided
        if self.frame_processor:
            self.process_thread = threading.Thread(target=self._process_frames, daemon=True)
            self.process_thread.start()
        
        print(f"🚀 High-FPS streaming started (target: {self.target_fps} FPS)")
    
    def _capture_frames(self):
        """Capture frames at high FPS in dedicated thread"""
        cap = cv2.VideoCapture(self.source)
        
        # Optimize capture settings for high FPS
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer lag
        cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        
        frame_interval = 1.0 / self.target_fps  # Target frame interval
        last_frame_time = time.time()
        
        while self.is_streaming:
            current_time = time.time()
            
            # Skip if not enough time passed for target FPS
            if current_time - last_frame_time < frame_interval:
                time.sleep(0.001)  # Small sleep to prevent CPU spinning
                continue
            
            ret, frame = cap.read()
            if not ret:
                break
            
            # Add frame to queue (non-blocking)
            try:
                self.frame_queue.put_nowait({
                    'frame': frame,
                    'timestamp': current_time,
                    'frame_id': self.fps_counter
                })
                
                self.fps_counter += 1
                last_frame_time = current_time
                
                # Update FPS counter
                if current_time - self.last_fps_time >= 1.0:
                    self.actual_fps = self.fps_counter / (current_time - self.last_fps_time)
                    self.fps_counter = 0
                    self.last_fps_time = current_time
                    
            except queue.Full:
                # Drop frame if queue is full (maintain real-time performance)
                continue
        
        cap.release()
        print("📹 Frame capture thread stopped")
    
    def _process_frames(self):
        """Process frames using provided processor function"""
        while self.is_streaming:
            try:
                # Get frame from queue with timeout
                frame_data = self.frame_queue.get(timeout=1.0)
                
                # Process frame
                if self.frame_processor:
                    processed_data = self.frame_processor(frame_data)
                    
                    # Add to processing queue
                    try:
                        self.processing_queue.put_nowait(processed_data)
                    except queue.Full:
                        # Drop processed result if queue full
                        continue
                
                self.frame_queue.task_done()
                
            except queue.Empty:
                continue
        
        print("🔄 Frame processing thread stopped")
    
    def get_processed_frame(self) -> Optional[Dict[str, Any]]:
        """Get next processed frame (non-blocking)"""
        try:
            return self.processing_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_current_fps(self) -> float:
        """Get current actual FPS"""
        return self.actual_fps
    
    @measure_latency("stream_stop")
    def stop_stream(self):
        """Stop video streaming"""
        self.is_streaming = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        
        if self.process_thread:
            self.process_thread.join(timeout=2.0)
        
        # Clear queues
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
                self.frame_queue.task_done()
            except queue.Empty:
                break
        
        while not self.processing_queue.empty():
            try:
                self.processing_queue.get_nowait()
            except queue.Empty:
                break
        
        print("⏹️ High-FPS streaming stopped")

class RealTimeVideoAnalyzer:
    """Real-time video analysis for live streams"""
    
    def __init__(self):
        self.stream: Optional[HighFPSVideoStream] = None
        self.analysis_cache = {}
        self.frame_skip = 1  # Process every N frames for performance
    
    @measure_latency("realtime_analysis_start")
    def start_realtime_analysis(self, source: str, target_fps: int = 90, analysis_callback: Optional[Callable] = None):
        """Start real-time video analysis"""
        self.stream = HighFPSVideoStream(source, target_fps)
        
        # Frame processor for real-time analysis
        def process_frame(frame_data):
            frame = frame_data['frame']
            timestamp = frame_data['timestamp']
            frame_id = frame_data['frame_id']
            
            # Skip frames for performance (analyze every N frames)
            if frame_id % self.frame_skip != 0:
                return None
            
            # Convert to RGB for analysis
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Quick analysis (cached if possible)
            analysis_result = self._quick_frame_analysis(pil_image, timestamp)
            
            result = {
                'frame_id': frame_id,
                'timestamp': timestamp,
                'analysis': analysis_result,
                'fps': self.stream.get_current_fps()
            }
            
            # Call analysis callback if provided
            if analysis_callback:
                analysis_callback(result)
            
            return result
        
        self.stream.start_stream(process_frame)
        print(f"🎯 Real-time analysis started (target: {target_fps} FPS)")
    
    def _quick_frame_analysis(self, frame: Image.Image, timestamp: float) -> Dict[str, Any]:
        """Quick frame analysis optimized for real-time performance"""
        # Create cache key based on frame characteristics
        frame_array = np.array(frame)
        frame_hash = hash(frame_array.tobytes())
        
        cache_key = f"frame_analysis_{frame_hash}"
        cached_result = cache_manager.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Simple real-time analysis (can be enhanced)
        analysis = {
            'timestamp': timestamp,
            'frame_size': frame.size,
            'brightness': np.mean(frame_array),
            'motion_detected': self._detect_motion(frame_array),
            'objects_detected': self._quick_object_detection(frame_array)
        }
        
        # Cache result for similar frames
        cache_manager.set(cache_key, analysis, ttl=300)  # 5 minutes
        
        return analysis
    
    def _detect_motion(self, frame: np.ndarray) -> bool:
        """Simple motion detection for real-time analysis"""
        # Simplified motion detection (can be enhanced)
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        
        # Check if we have a previous frame
        if hasattr(self, '_prev_frame'):
            diff = cv2.absdiff(self._prev_frame, gray)
            motion_threshold = np.mean(diff) > 30  # Tunable threshold
            self._prev_frame = gray
            return motion_threshold
        else:
            self._prev_frame = gray
            return False
    
    def _quick_object_detection(self, frame: np.ndarray) -> int:
        """Quick object detection using edge detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter significant contours
        significant_objects = len([c for c in contours if cv2.contourArea(c) > 500])
        return significant_objects
    
    def get_stream_stats(self) -> Dict[str, Any]:
        """Get real-time streaming statistics"""
        if not self.stream:
            return {'status': 'not_active'}
        
        return {
            'status': 'active',
            'current_fps': self.stream.get_current_fps(),
            'target_fps': self.stream.target_fps,
            'frame_skip': self.frame_skip,
            'queue_size': self.stream.frame_queue.qsize(),
            'processing_queue_size': self.stream.processing_queue.qsize()
        }
    
    def adjust_performance(self, target_latency_ms: int = 1000):
        """Dynamically adjust performance based on latency requirements"""
        current_fps = self.stream.get_current_fps() if self.stream else 0
        
        if current_fps > 0:
            # Adjust frame skip based on performance
            frame_time_ms = 1000 / current_fps
            
            if frame_time_ms > target_latency_ms:
                # Increase frame skip to reduce processing load
                self.frame_skip = min(10, self.frame_skip + 1)
                print(f"🔧 Increased frame skip to {self.frame_skip} for performance")
            elif frame_time_ms < target_latency_ms * 0.5:
                # Decrease frame skip to increase quality
                self.frame_skip = max(1, self.frame_skip - 1)
                print(f"🔧 Decreased frame skip to {self.frame_skip} for quality")
    
    def stop_analysis(self):
        """Stop real-time analysis"""
        if self.stream:
            self.stream.stop_stream()
            self.stream = None
        print("⏹️ Real-time analysis stopped")

# Global instance for real-time analysis
realtime_analyzer = RealTimeVideoAnalyzer()

# Convenience functions
def start_90fps_analysis(source: str, callback: Optional[Callable] = None):
    """Start 90 FPS real-time analysis (Round 2 requirement)"""
    return realtime_analyzer.start_realtime_analysis(source, 90, callback)

def get_realtime_stats() -> Dict[str, Any]:
    """Get real-time streaming statistics"""
    return realtime_analyzer.get_stream_stats()

def stop_realtime_analysis():
    """Stop real-time analysis"""
    realtime_analyzer.stop_analysis()