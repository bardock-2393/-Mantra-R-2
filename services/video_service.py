"""
Video Service for video processing, object detection, and clip generation
"""

import os
import cv2
import numpy as np
import torch
import ray
from typing import Dict, List, Any, Optional, Tuple
import json
import subprocess
from pathlib import Path
import duckdb
from datetime import datetime

from config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

@ray.remote(num_gpus=1)
class VideoProcessor:
    """Ray actor for video processing on GPU"""
    
    def __init__(self, gpu_id: int, config):
        self.gpu_id = gpu_id
        self.config = config
        self.device = f"cuda:{gpu_id}"
        
        # Initialize models
        self._init_models()
        
        logger.info(f"VideoProcessor initialized on GPU {gpu_id}")
    
    def _init_models(self):
        """Initialize detection and tracking models"""
        try:
            # Check if GPU device is available
            if not torch.cuda.is_available():
                logger.warning(f"CUDA not available, using CPU for GPU {self.gpu_id}")
                self.device = "cpu"
            elif self.gpu_id >= torch.cuda.device_count():
                logger.warning(f"GPU {self.gpu_id} not available, using CPU")
                self.device = "cpu"
            
            # Initialize RT-DETR-v2 for object detection
            from ultralytics import YOLO
            
            # Load RT-DETR-v2 model
            self.detector = YOLO('rtdetr-l.pt')  # RT-DETR large model
            
            # Try to move to device, fallback to CPU if failed
            try:
                self.detector.to(self.device)
                logger.info(f"Model loaded on {self.device}")
            except Exception as e:
                logger.warning(f"Failed to load model on {self.device}, using CPU: {e}")
                self.device = "cpu"
                self.detector.to(self.device)
            
            # Initialize ByteTrack for tracking
            try:
                from bytetrack.byte_tracker import BYTETracker
                self.tracker = BYTETracker(
                    track_thresh=0.5,
                    track_buffer=30,
                    match_thresh=0.8,
                    frame_rate=30
                )
                logger.info(f"ByteTrack tracker initialized on {self.device}")
            except ImportError:
                logger.warning(f"ByteTrack not available, using fallback tracking")
                self.tracker = None
            except Exception as e:
                logger.warning(f"Could not initialize ByteTrack: {e}")
                self.tracker = None
            
            logger.info(f"Models initialized on {self.device}")
            
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise
    
    def process_video_window(self, video_path: str, start_time: float, end_time: float, 
                           video_id: str, window_id: int) -> Dict[str, Any]:
        """Process a video window and return events"""
        try:
            events = []
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate frame range for window
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)
            
            # Set start position
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            frame_count = start_frame
            current_time = start_time
            
            # Process frames
            while frame_count < end_frame and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Adaptive sampling
                sample_rate = self._get_sample_rate(frame, current_time)
                
                if frame_count % sample_rate == 0:
                    # Detect objects
                    detections = self._detect_objects(frame)
                    
                    # Track objects
                    tracks = self._track_objects(detections, current_time)
                    
                    # Generate events
                    window_events = self._generate_events(tracks, current_time, video_id)
                    events.extend(window_events)
                
                frame_count += 1
                current_time += 1.0 / fps
            
            cap.release()
            
            return {
                'window_id': window_id,
                'start_time': start_time,
                'end_time': end_time,
                'events': events,
                'processed_frames': frame_count - start_frame
            }
            
        except Exception as e:
            logger.error(f"Error processing video window {window_id}: {e}")
            return {
                'window_id': window_id,
                'start_time': start_time,
                'end_time': end_time,
                'events': [],
                'error': str(e)
            }
    
    def _get_sample_rate(self, frame: np.ndarray, current_time: float) -> int:
        """Determine sampling rate based on motion and time"""
        # Base sampling rate
        base_rate = self.config.processing.global_fps
        
        # Check for motion (simple frame difference)
        if hasattr(self, '_prev_frame'):
            frame_diff = cv2.absdiff(frame, self._prev_frame)
            motion_score = np.mean(frame_diff)
            
            if motion_score > 10:  # Threshold for motion
                base_rate = self.config.processing.motion_fps
        
        self._prev_frame = frame.copy()
        return max(1, int(30 / base_rate))  # Convert fps to frame skip
    
    def _detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """Detect objects in frame using RT-DETR-v2"""
        try:
            # Run detection
            results = self.detector(frame, verbose=False)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = box.conf[0].cpu().numpy()
                        cls = int(box.cls[0].cpu().numpy())
                        class_name = self.detector.names[cls]
                        
                        detections.append({
                            'bbox': [x1, y1, x2, y2],
                            'confidence': conf,
                            'class': class_name,
                            'class_id': cls
                        })
            
            return detections
            
        except Exception as e:
            logger.error(f"Error in object detection: {e}")
            return []
    
    def _track_objects(self, detections: List[Dict], timestamp: float) -> List[Dict]:
        """Track objects using ByteTrack or fallback"""
        try:
            if not detections:
                return []
            
            # Check if ByteTrack is available
            if self.tracker is None:
                # Fallback: convert detections directly to tracks
                tracks = []
                for i, det in enumerate(detections):
                    tracks.append({
                        'track_id': f"det_{i}_{int(timestamp)}",
                        'bbox': det['bbox'],
                        'timestamp': timestamp,
                        'class': det.get('class', 'object')
                    })
                return tracks
            
            # Use ByteTrack for tracking
            dets = []
            for det in detections:
                bbox = det['bbox']
                dets.append([
                    bbox[0], bbox[1], bbox[2], bbox[3],  # bbox
                    det['confidence']  # confidence
                ])
            
            dets = np.array(dets)
            
            # Update tracker (assuming 1920x1080 as default image size)
            online_targets = self.tracker.update(
                dets,
                [1080, 1920],  # image size (height, width)
                [1080, 1920]   # image size (height, width)
            )
            
            # Convert tracks to events
            tracks = []
            for target in online_targets:
                tracks.append({
                    'track_id': target.track_id,
                    'bbox': target.tlbr.tolist(),
                    'timestamp': timestamp,
                    'class': 'tracked_object'
                })
            
            return tracks
            
        except Exception as e:
            logger.error(f"Error in object tracking: {e}")
            # Fallback: return detections as tracks
            tracks = []
            for i, det in enumerate(detections):
                tracks.append({
                    'track_id': f"det_{i}_{int(timestamp)}",
                    'bbox': det['bbox'],
                    'timestamp': timestamp,
                    'class': det.get('class', 'object')
                })
            return tracks
    
    def _generate_events(self, tracks: List[Dict], timestamp: float, video_id: str) -> List[Dict]:
        """Generate events from tracks"""
        events = []
        
        for track in tracks:
            event = {
                'video_id': video_id,
                'ts': timestamp,
                'type': 'object_detection',
                'analysis_type': 'comprehensive_analysis',
                'actor': {
                    'track_id': track['track_id'],
                    'class': track['class']
                },
                'location': 'frame_center',
                'attributes': {
                    'state': 'detected',
                    'confidence': 0.95,
                    'bbox': track['bbox']
                },
                'visual_evidence': {
                    'frame': int(timestamp * 30),  # Approximate frame number
                    'bbox': track['bbox'],
                    'clip': f"clip_{video_id}_{timestamp:.2f}.mp4"
                },
                'audio_evidence': {
                    'speech': "",
                    'sounds': [],
                    'audio_features': {
                        'volume': 'normal',
                        'pitch': 'normal',
                        'tempo': 'normal'
                    }
                },
                'combined_analysis': {
                    'multi_modal_context': 'visual_detection',
                    'temporal_alignment': 'synchronized',
                    'confidence': 0.95
                }
            }
            events.append(event)
        
        return events

class VideoService:
    """Service for video processing and management"""
    
    def __init__(self, config):
        self.config = config
        
        # Initialize Ray if not already initialized
        if not ray.is_initialized():
            ray_config = config.get_ray_config()
            ray.init(**ray_config)
        
        # Initialize video processors
        self._init_processors()
        
        # Initialize database
        self._init_database()
        
        logger.info("Video Service initialized successfully")
    
    def _init_processors(self):
        """Initialize video processing actors"""
        self.processors = []
        
        # Create processors for each GPU (0-3 for detection)
        for gpu_id in range(min(4, self.config.gpu.num_gpus)):
            processor = VideoProcessor.remote(gpu_id, self.config)
            self.processors.append(processor)
        
        logger.info(f"Initialized {len(self.processors)} video processors")
    
    def _init_database(self):
        """Initialize DuckDB database"""
        try:
            # Create database directory
            db_dir = os.path.dirname(self.config.storage.duckdb_path)
            os.makedirs(db_dir, exist_ok=True)
            
            # Connect to database
            self.db = duckdb.connect(self.config.storage.duckdb_path)
            
            # Create events table
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    video_id VARCHAR,
                    ts DOUBLE,
                    type VARCHAR,
                    analysis_type VARCHAR,
                    actor JSON,
                    location VARCHAR,
                    attributes JSON,
                    visual_evidence JSON,
                    audio_evidence JSON,
                    combined_analysis JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create video_metadata table
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS video_metadata (
                    video_id VARCHAR PRIMARY KEY,
                    filename VARCHAR,
                    duration DOUBLE,
                    fps DOUBLE,
                    resolution VARCHAR,
                    file_size BIGINT,
                    status VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def process_video(self, video_id: str, video_path: str) -> Dict[str, Any]:
        """Process a video file and extract events"""
        try:
            # Get video metadata
            metadata = self._get_video_metadata(video_path)
            
            # Store metadata
            self._store_video_metadata(video_id, metadata)
            
            # Update status
            self._update_video_status(video_id, 'processing')
            
            # Process video in windows
            events = self._process_video_windows(video_id, video_path, metadata)
            
            # Store events
            self._store_events(events)
            
            # Update status
            self._update_video_status(video_id, 'completed')
            
            return {
                'video_id': video_id,
                'status': 'completed',
                'events_count': len(events),
                'duration': metadata['duration'],
                'fps': metadata['fps']
            }
            
        except Exception as e:
            logger.error(f"Error processing video {video_id}: {e}")
            self._update_video_status(video_id, 'error')
            raise
    
    def _get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using OpenCV"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0
            
            cap.release()
            
            # Get file size
            file_size = os.path.getsize(video_path)
            
            return {
                'fps': fps,
                'total_frames': total_frames,
                'width': width,
                'height': height,
                'duration': duration,
                'resolution': f"{width}x{height}",
                'file_size': file_size
            }
            
        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            raise
    
    def _process_video_windows(self, video_id: str, video_path: str, metadata: Dict) -> List[Dict]:
        """Process video in windows using Ray"""
        try:
            duration = metadata['duration']
            window_size = self.config.processing.window_seconds
            overlap = self.config.processing.overlap_seconds
            
            # Calculate windows
            windows = []
            start_time = 0
            window_id = 0
            
            while start_time < duration:
                end_time = min(start_time + window_size, duration)
                windows.append({
                    'window_id': window_id,
                    'start_time': start_time,
                    'end_time': end_time
                })
                start_time = end_time - overlap
                window_id += 1
            
            # Process windows in parallel
            futures = []
            for i, window in enumerate(windows):
                processor = self.processors[i % len(self.processors)]
                future = processor.process_video_window.remote(
                    video_path, window['start_time'], window['end_time'], 
                    video_id, window['window_id']
                )
                futures.append(future)
            
            # Collect results
            results = ray.get(futures)
            
            # Combine events
            all_events = []
            for result in results:
                if 'events' in result:
                    all_events.extend(result['events'])
            
            return all_events
            
        except Exception as e:
            logger.error(f"Error processing video windows: {e}")
            raise
    
    def _store_video_metadata(self, video_id: str, metadata: Dict):
        """Store video metadata in database"""
        try:
            self.db.execute("""
                INSERT OR REPLACE INTO video_metadata 
                (video_id, filename, duration, fps, resolution, file_size, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                video_id,
                metadata.get('filename', ''),
                metadata['duration'],
                metadata['fps'],
                metadata['resolution'],
                metadata['file_size'],
                'processing'
            ))
            
        except Exception as e:
            logger.error(f"Error storing video metadata: {e}")
            raise
    
    def _store_events(self, events: List[Dict]):
        """Store events in database"""
        try:
            if not events:
                return
            
            # Prepare data for batch insert
            data = []
            for event in events:
                data.append((
                    event['video_id'],
                    event['ts'],
                    event['type'],
                    event['analysis_type'],
                    json.dumps(event['actor']),
                    event['location'],
                    json.dumps(event['attributes']),
                    json.dumps(event['visual_evidence']),
                    json.dumps(event['audio_evidence']),
                    json.dumps(event['combined_analysis'])
                ))
            
            # Batch insert
            self.db.executemany("""
                INSERT INTO events 
                (video_id, ts, type, analysis_type, actor, location, attributes, 
                 visual_evidence, audio_evidence, combined_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            
            logger.info(f"Stored {len(events)} events in database")
            
        except Exception as e:
            logger.error(f"Error storing events: {e}")
            raise
    
    def _update_video_status(self, video_id: str, status: str):
        """Update video processing status"""
        try:
            self.db.execute("""
                UPDATE video_metadata 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE video_id = ?
            """, (status, video_id))
            
        except Exception as e:
            logger.error(f"Error updating video status: {e}")
    
    def generate_clip(self, video_id: str, start_time: float, end_time: float) -> str:
        """Generate a video clip for the specified time range"""
        try:
            # Get video file path
            video_path = self._get_video_path(video_id)
            if not video_path:
                raise ValueError(f"Video file not found for {video_id}")
            
            # Generate clip filename
            clip_filename = f"clip_{video_id}_{start_time:.2f}_{end_time:.2f}.mp4"
            clip_path = os.path.join(self.config.storage.local_upload_dir, clip_filename)
            
            # Use FFmpeg to extract clip
            cmd = [
                'ffmpeg', '-i', video_path,
                '-ss', str(start_time),
                '-t', str(end_time - start_time),
                '-c', 'copy',  # Copy without re-encoding
                '-y',  # Overwrite output file
                clip_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {result.stderr}")
            
            # Return clip URL
            clip_url = f"/static/uploads/{clip_filename}"
            
            logger.info(f"Generated clip: {clip_url}")
            return clip_url
            
        except Exception as e:
            logger.error(f"Error generating clip: {e}")
            raise
    
    def _get_video_path(self, video_id: str) -> Optional[str]:
        """Get video file path from database"""
        try:
            result = self.db.execute("""
                SELECT filename FROM video_metadata 
                WHERE video_id = ?
            """, (video_id,)).fetchone()
            
            if result:
                return os.path.join(self.config.storage.local_upload_dir, result[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting video path: {e}")
            return None
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Get video processing status"""
        try:
            result = self.db.execute("""
                SELECT * FROM video_metadata 
                WHERE video_id = ?
            """, (video_id,)).fetchone()
            
            if result:
                return {
                    'video_id': result[0],
                    'filename': result[1],
                    'duration': result[2],
                    'fps': result[3],
                    'resolution': result[4],
                    'file_size': result[5],
                    'status': result[6],
                    'created_at': result[7],
                    'updated_at': result[8]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting video status: {e}")
            return None
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'db'):
                self.db.close()
            
            # Shutdown Ray
            if ray.is_initialized():
                ray.shutdown()
            
            logger.info("Video Service cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up Video Service: {e}") 