"""
Audio Service for speech recognition and audio analysis
"""

import os
import torch
import torchaudio
import whisper
import librosa
import numpy as np
from typing import Dict, List, Any, Optional
import json
import subprocess
from pathlib import Path
import duckdb
from datetime import datetime

from config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class AudioService:
    """Service for audio processing and analysis"""
    
    def __init__(self, config):
        self.config = config
        
        # Initialize audio models
        self._init_models()
        
        # Initialize database connection
        self._init_database()
        
        logger.info("Audio Service initialized successfully")
    
    def _init_models(self):
        """Initialize audio processing models"""
        try:
            # Initialize Whisper for speech recognition
            model_size = self.config.models.whisper_model
            try:
                # Try the new Whisper API first
                self.whisper_model = whisper.load_model(model_size)
            except AttributeError:
                # Fallback to older API or skip Whisper
                logger.warning("Whisper load_model not available, skipping Whisper initialization")
                self.whisper_model = None
            
            # Move to GPU if available
            if self.whisper_model and torch.cuda.is_available():
                self.whisper_model = self.whisper_model.to("cuda:4")  # GPU 4 for audio
            
            # Initialize Wav2Vec2 for audio feature extraction
            try:
                from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
                self.wav2vec2_model = Wav2Vec2ForCTC.from_pretrained(self.config.models.wav2vec2_model)
                self.wav2vec2_processor = Wav2Vec2Processor.from_pretrained(self.config.models.wav2vec2_model)
                
                if torch.cuda.is_available():
                    self.wav2vec2_model = self.wav2vec2_model.to("cuda:4")
            except Exception as e:
                logger.warning(f"Could not load Wav2Vec2: {e}")
                self.wav2vec2_model = None
                self.wav2vec2_processor = None
            
            # Initialize AudioCLIP for audio understanding
            try:
                from audioclip import AudioCLIP
                self.audioclip_model = AudioCLIP.from_pretrained("AudioCLIP-Full-Training.pt")
                if torch.cuda.is_available():
                    self.audioclip_model = self.audioclip_model.to("cuda:4")
                logger.info("AudioCLIP model loaded successfully")
            except ImportError:
                logger.warning("AudioCLIP not available, using fallback audio classification")
                self.audioclip_model = None
            except Exception as e:
                logger.warning(f"Could not load AudioCLIP: {e}")
                self.audioclip_model = None
            
            logger.info("Audio models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing audio models: {e}")
            # Don't raise the error, just log it and continue without audio models
            logger.warning("Continuing without audio models due to initialization error")
            self.whisper_model = None
            self.wav2vec2_model = None
            self.wav2vec2_processor = None
            self.audioclip_model = None
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            self.db = duckdb.connect(self.config.storage.duckdb_path)
            logger.info("Audio Service database connection established")
            
        except Exception as e:
            logger.error(f"Error initializing database connection: {e}")
            raise
    
    def process_audio(self, video_id: str, video_path: str) -> Dict[str, Any]:
        """Process audio from video file"""
        try:
            # Extract audio from video
            audio_path = self._extract_audio(video_id, video_path)
            
            # Process audio in chunks
            audio_events = self._process_audio_chunks(video_id, audio_path)
            
            # Store audio events
            self._store_audio_events(audio_events)
            
            # Cleanup temporary audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            return {
                'video_id': video_id,
                'status': 'completed',
                'audio_events_count': len(audio_events)
            }
            
        except Exception as e:
            logger.error(f"Error processing audio for video {video_id}: {e}")
            raise
    
    def _extract_audio(self, video_id: str, video_path: str) -> str:
        """Extract audio from video file"""
        try:
            # Generate audio file path
            audio_filename = f"audio_{video_id}.wav"
            audio_path = os.path.join(self.config.storage.local_temp_dir, audio_filename)
            
            # Use FFmpeg to extract audio
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM 16-bit
                '-ar', str(self.config.processing.audio_sample_rate),  # Sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {result.stderr}")
            
            logger.info(f"Extracted audio: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise
    
    def _process_audio_chunks(self, video_id: str, audio_path: str) -> List[Dict]:
        """Process audio in chunks"""
        try:
            audio_events = []
            
            # Load audio file
            audio, sr = librosa.load(audio_path, sr=self.config.processing.audio_sample_rate)
            duration = len(audio) / sr
            
            # Process in chunks
            chunk_duration = self.config.processing.audio_chunk_duration
            chunk_samples = int(chunk_duration * sr)
            
            for i in range(0, len(audio), chunk_samples):
                start_time = i / sr
                end_time = min((i + chunk_samples) / sr, duration)
                
                # Extract chunk
                chunk = audio[i:i + chunk_samples]
                
                # Process chunk
                chunk_events = self._process_audio_chunk(
                    video_id, chunk, start_time, end_time, sr
                )
                audio_events.extend(chunk_events)
            
            return audio_events
            
        except Exception as e:
            logger.error(f"Error processing audio chunks: {e}")
            raise
    
    def _process_audio_chunk(self, video_id: str, audio_chunk: np.ndarray, 
                           start_time: float, end_time: float, sample_rate: int) -> List[Dict]:
        """Process a single audio chunk"""
        try:
            events = []
            
            # Speech recognition with Whisper
            speech_events = self._recognize_speech(audio_chunk, start_time, end_time, video_id)
            events.extend(speech_events)
            
            # Audio feature extraction with Wav2Vec2
            feature_events = self._extract_audio_features(audio_chunk, start_time, end_time, video_id)
            events.extend(feature_events)
            
            # Sound classification
            sound_events = self._classify_sounds(audio_chunk, start_time, end_time, video_id)
            events.extend(sound_events)
            
            return events
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return []
    
    def _recognize_speech(self, audio_chunk: np.ndarray, start_time: float, 
                         end_time: float, video_id: str) -> List[Dict]:
        """Recognize speech in audio chunk"""
        try:
            events = []
            
            # Check if Whisper model is available
            if self.whisper_model is None:
                logger.warning("Whisper model not available, skipping speech recognition")
                return events
            
            # Save chunk to temporary file for Whisper
            temp_path = os.path.join(self.config.storage.local_temp_dir, f"temp_{video_id}_{start_time:.2f}.wav")
            librosa.output.write_wav(temp_path, audio_chunk, self.config.processing.audio_sample_rate)
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(temp_path)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            # Create speech events
            if result['text'].strip():
                event = {
                    'video_id': video_id,
                    'ts': start_time,
                    'type': 'speech_recognition',
                    'analysis_type': 'comprehensive_analysis',
                    'actor': {
                        'track_id': 'speech',
                        'class': 'speech'
                    },
                    'location': 'audio_track',
                    'attributes': {
                        'state': 'detected',
                        'confidence': result.get('segments', [{}])[0].get('avg_logprob', 0.8),
                        'language': result.get('language', 'en')
                    },
                    'visual_evidence': {
                        'frame': int(start_time * 30),
                        'bbox': [0, 0, 0, 0],
                        'clip': f"audio_clip_{video_id}_{start_time:.2f}.wav"
                    },
                    'audio_evidence': {
                        'speech': result['text'],
                        'sounds': [],
                        'audio_features': {
                            'volume': self._analyze_volume(audio_chunk),
                            'pitch': self._analyze_pitch(audio_chunk),
                            'tempo': self._analyze_tempo(audio_chunk)
                        },
                        'audio_clip': f"audio_clip_{video_id}_{start_time:.2f}.wav"
                    },
                    'combined_analysis': {
                        'multi_modal_context': 'speech_detection',
                        'temporal_alignment': 'synchronized',
                        'confidence': 0.9
                    }
                }
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
            return []
    
    def _extract_audio_features(self, audio_chunk: np.ndarray, start_time: float,
                               end_time: float, video_id: str) -> List[Dict]:
        """Extract audio features using Wav2Vec2"""
        try:
            events = []
            
            # Check if Wav2Vec2 model is available
            if self.wav2vec2_model is None or self.wav2vec2_processor is None:
                logger.warning("Wav2Vec2 model not available, skipping audio feature extraction")
                return events
            
            # Prepare audio for Wav2Vec2
            inputs = self.wav2vec2_processor(
                audio_chunk, 
                sampling_rate=self.config.processing.audio_sample_rate, 
                return_tensors="pt"
            )
            
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda:4") for k, v in inputs.items()}
            
            # Extract features
            with torch.no_grad():
                outputs = self.wav2vec2_model(**inputs, output_hidden_states=True)
                
                # Get hidden states (features)
                hidden_states = outputs.hidden_states[-1]  # Last layer
                features = hidden_states.mean(dim=1).cpu().numpy()  # Average over time
            
            # Create feature event
            event = {
                'video_id': video_id,
                'ts': start_time,
                'type': 'audio_features',
                'analysis_type': 'comprehensive_analysis',
                'actor': {
                    'track_id': 'audio_features',
                    'class': 'audio_features'
                },
                'location': 'audio_track',
                'attributes': {
                    'state': 'extracted',
                    'confidence': 0.95,
                    'feature_dimensions': features.shape[1],
                    'feature_vector': features[0].tolist()[:100]  # First 100 dimensions
                },
                'visual_evidence': {
                    'frame': int(start_time * 30),
                    'bbox': [0, 0, 0, 0],
                    'clip': f"audio_clip_{video_id}_{start_time:.2f}.wav"
                },
                'audio_evidence': {
                    'speech': "",
                    'sounds': [],
                    'audio_features': {
                        'volume': self._analyze_volume(audio_chunk),
                        'pitch': self._analyze_pitch(audio_chunk),
                        'tempo': self._analyze_tempo(audio_chunk)
                    },
                    'audio_clip': f"audio_clip_{video_id}_{start_time:.2f}.wav"
                },
                'combined_analysis': {
                    'multi_modal_context': 'audio_feature_extraction',
                    'temporal_alignment': 'synchronized',
                    'confidence': 0.95
                }
            }
            events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error extracting audio features: {e}")
            return []
    
    def _classify_sounds(self, audio_chunk: np.ndarray, start_time: float,
                        end_time: float, video_id: str) -> List[Dict]:
        """Classify sounds in audio chunk"""
        try:
            events = []
            
            # Simple sound classification based on audio characteristics
            sounds = []
            
            # Check for silence
            if np.mean(np.abs(audio_chunk)) < 0.01:
                sounds.append('silence')
            
            # Check for music (using spectral features)
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_chunk, sr=self.config.processing.audio_sample_rate)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_chunk, sr=self.config.processing.audio_sample_rate)
            
            if np.mean(spectral_centroids) > 2000 and np.mean(spectral_rolloff) > 4000:
                sounds.append('music')
            
            # Check for noise
            zero_crossing_rate = librosa.feature.zero_crossing_rate(audio_chunk)
            if np.mean(zero_crossing_rate) > 0.1:
                sounds.append('noise')
            
            # Check for speech-like sounds
            mfccs = librosa.feature.mfcc(y=audio_chunk, sr=self.config.processing.audio_sample_rate, n_mfcc=13)
            if np.std(mfccs) > 2.0:
                sounds.append('speech_like')
            
            # Create sound classification event
            if sounds:
                event = {
                    'video_id': video_id,
                    'ts': start_time,
                    'type': 'sound_classification',
                    'analysis_type': 'comprehensive_analysis',
                    'actor': {
                        'track_id': 'sounds',
                        'class': 'audio_sounds'
                    },
                    'location': 'audio_track',
                    'attributes': {
                        'state': 'classified',
                        'confidence': 0.8,
                        'sound_types': sounds
                    },
                    'visual_evidence': {
                        'frame': int(start_time * 30),
                        'bbox': [0, 0, 0, 0],
                        'clip': f"audio_clip_{video_id}_{start_time:.2f}.wav"
                    },
                    'audio_evidence': {
                        'speech': "",
                        'sounds': sounds,
                        'audio_features': {
                            'volume': self._analyze_volume(audio_chunk),
                            'pitch': self._analyze_pitch(audio_chunk),
                            'tempo': self._analyze_tempo(audio_chunk)
                        },
                        'audio_clip': f"audio_clip_{video_id}_{start_time:.2f}.wav"
                    },
                    'combined_analysis': {
                        'multi_modal_context': 'sound_classification',
                        'temporal_alignment': 'synchronized',
                        'confidence': 0.8
                    }
                }
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error classifying sounds: {e}")
            return []
    
    def _analyze_volume(self, audio_chunk: np.ndarray) -> str:
        """Analyze audio volume level"""
        try:
            rms = np.sqrt(np.mean(audio_chunk**2))
            
            if rms < 0.01:
                return 'low'
            elif rms < 0.1:
                return 'moderate'
            else:
                return 'high'
                
        except Exception:
            return 'normal'
    
    def _analyze_pitch(self, audio_chunk: np.ndarray) -> str:
        """Analyze audio pitch"""
        try:
            pitches, magnitudes = librosa.piptrack(y=audio_chunk, sr=self.config.processing.audio_sample_rate)
            pitch_values = pitches[magnitudes > np.percentile(magnitudes, 90)]
            
            if len(pitch_values) == 0:
                return 'normal'
            
            mean_pitch = np.mean(pitch_values)
            
            if mean_pitch < 200:
                return 'low'
            elif mean_pitch > 800:
                return 'high'
            else:
                return 'normal'
                
        except Exception:
            return 'normal'
    
    def _analyze_tempo(self, audio_chunk: np.ndarray) -> str:
        """Analyze audio tempo"""
        try:
            tempo, _ = librosa.beat.beat_track(y=audio_chunk, sr=self.config.processing.audio_sample_rate)
            
            if tempo < 60:
                return 'slow'
            elif tempo > 120:
                return 'fast'
            else:
                return 'steady'
                
        except Exception:
            return 'steady'
    
    def _store_audio_events(self, audio_events: List[Dict]):
        """Store audio events in database"""
        try:
            if not audio_events:
                return
            
            # Prepare data for batch insert
            data = []
            for event in audio_events:
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
            
            logger.info(f"Stored {len(audio_events)} audio events in database")
            
        except Exception as e:
            logger.error(f"Error storing audio events: {e}")
            raise
    
    def get_audio_events(self, video_id: str, start_time: float = None, 
                        end_time: float = None) -> List[Dict]:
        """Get audio events for a video"""
        try:
            query = """
                SELECT * FROM events 
                WHERE video_id = ? AND type IN ('speech_recognition', 'audio_features', 'sound_classification')
            """
            params = [video_id]
            
            if start_time is not None:
                query += " AND ts >= ?"
                params.append(start_time)
            
            if end_time is not None:
                query += " AND ts <= ?"
                params.append(end_time)
            
            query += " ORDER BY ts"
            
            results = self.db.execute(query, params).fetchall()
            
            events = []
            for result in results:
                event = {
                    'video_id': result[0],
                    'ts': result[1],
                    'type': result[2],
                    'analysis_type': result[3],
                    'actor': json.loads(result[4]),
                    'location': result[5],
                    'attributes': json.loads(result[6]),
                    'visual_evidence': json.loads(result[7]),
                    'audio_evidence': json.loads(result[8]),
                    'combined_analysis': json.loads(result[9])
                }
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting audio events: {e}")
            return []
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'db'):
                self.db.close()
            
            logger.info("Audio Service cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up Audio Service: {e}") 