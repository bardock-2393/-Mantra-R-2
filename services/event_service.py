"""
Event Service for querying and managing events from the database
"""

import os
import json
import duckdb
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np

from config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EventService:
    """Service for querying and managing events"""
    
    def __init__(self, config):
        self.config = config
        
        # Initialize database connection
        self._init_database()
        
        logger.info("Event Service initialized successfully")
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            # Create database directory
            db_dir = os.path.dirname(self.config.storage.duckdb_path)
            os.makedirs(db_dir, exist_ok=True)
            
            # Connect to database
            self.db = duckdb.connect(self.config.storage.duckdb_path)
            
            logger.info("Event Service database connection established")
            
        except Exception as e:
            logger.error(f"Error initializing database connection: {e}")
            raise
    
    def get_events(self, video_id: str = None, start_time: float = None, 
                  end_time: float = None, event_type: str = None, 
                  analysis_type: str = None, limit: int = 1000) -> List[Dict]:
        """Get events with optional filtering"""
        try:
            # Build query
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            if video_id:
                query += " AND video_id = ?"
                params.append(video_id)
            
            if start_time is not None:
                query += " AND ts >= ?"
                params.append(start_time)
            
            if end_time is not None:
                query += " AND ts <= ?"
                params.append(end_time)
            
            if event_type:
                query += " AND type = ?"
                params.append(event_type)
            
            if analysis_type:
                query += " AND analysis_type = ?"
                params.append(analysis_type)
            
            # Add ordering and limit
            query += " ORDER BY ts ASC LIMIT ?"
            params.append(limit)
            
            # Execute query
            results = self.db.execute(query, params).fetchall()
            
            # Convert to list of dictionaries
            events = []
            for result in results:
                event = {
                    'video_id': result[0],
                    'ts': result[1],
                    'type': result[2],
                    'analysis_type': result[3],
                    'actor': json.loads(result[4]) if result[4] else {},
                    'location': result[5],
                    'attributes': json.loads(result[6]) if result[6] else {},
                    'visual_evidence': json.loads(result[7]) if result[7] else {},
                    'audio_evidence': json.loads(result[8]) if result[8] else {},
                    'combined_analysis': json.loads(result[9]) if result[9] else {},
                    'created_at': result[10]
                }
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return []
    
    def get_event_summary(self, video_id: str) -> Dict[str, Any]:
        """Get summary statistics for events in a video"""
        try:
            # Get basic statistics
            stats_query = """
                SELECT 
                    COUNT(*) as total_events,
                    COUNT(DISTINCT type) as unique_event_types,
                    MIN(ts) as start_time,
                    MAX(ts) as end_time,
                    AVG(ts) as avg_time
                FROM events 
                WHERE video_id = ?
            """
            
            stats_result = self.db.execute(stats_query, [video_id]).fetchone()
            
            if not stats_result or stats_result[0] == 0:
                return {
                    'video_id': video_id,
                    'total_events': 0,
                    'unique_event_types': 0,
                    'start_time': 0,
                    'end_time': 0,
                    'duration': 0,
                    'event_types': {},
                    'analysis_types': {}
                }
            
            # Get event type breakdown
            type_query = """
                SELECT type, COUNT(*) as count
                FROM events 
                WHERE video_id = ?
                GROUP BY type
                ORDER BY count DESC
            """
            
            type_results = self.db.execute(type_query, [video_id]).fetchall()
            event_types = {row[0]: row[1] for row in type_results}
            
            # Get analysis type breakdown
            analysis_query = """
                SELECT analysis_type, COUNT(*) as count
                FROM events 
                WHERE video_id = ?
                GROUP BY analysis_type
                ORDER BY count DESC
            """
            
            analysis_results = self.db.execute(analysis_query, [video_id]).fetchall()
            analysis_types = {row[0]: row[1] for row in analysis_results}
            
            # Calculate duration
            duration = stats_result[3] - stats_result[2] if stats_result[3] and stats_result[2] else 0
            
            return {
                'video_id': video_id,
                'total_events': stats_result[0],
                'unique_event_types': stats_result[1],
                'start_time': stats_result[2],
                'end_time': stats_result[3],
                'avg_time': stats_result[4],
                'duration': duration,
                'event_types': event_types,
                'analysis_types': analysis_types
            }
            
        except Exception as e:
            logger.error(f"Error getting event summary: {e}")
            return {}
    
    def search_events(self, video_id: str, search_text: str, 
                     search_fields: List[str] = None) -> List[Dict]:
        """Search events by text in specified fields"""
        try:
            if not search_fields:
                search_fields = ['type', 'analysis_type', 'location']
            
            # Build search query
            search_conditions = []
            params = [video_id]
            
            for field in search_fields:
                search_conditions.append(f"{field} LIKE ?")
                params.append(f"%{search_text}%")
            
            # Also search in JSON fields
            search_conditions.append("actor LIKE ?")
            params.append(f"%{search_text}%")
            
            search_conditions.append("attributes LIKE ?")
            params.append(f"%{search_text}%")
            
            search_conditions.append("audio_evidence LIKE ?")
            params.append(f"%{search_text}%")
            
            query = f"""
                SELECT * FROM events 
                WHERE video_id = ? AND ({' OR '.join(search_conditions)})
                ORDER BY ts ASC
                LIMIT 1000
            """
            
            results = self.db.execute(query, params).fetchall()
            
            # Convert to list of dictionaries
            events = []
            for result in results:
                event = {
                    'video_id': result[0],
                    'ts': result[1],
                    'type': result[2],
                    'analysis_type': result[3],
                    'actor': json.loads(result[4]) if result[4] else {},
                    'location': result[5],
                    'attributes': json.loads(result[6]) if result[6] else {},
                    'visual_evidence': json.loads(result[7]) if result[7] else {},
                    'audio_evidence': json.loads(result[8]) if result[8] else {},
                    'combined_analysis': json.loads(result[9]) if result[9] else {},
                    'created_at': result[10]
                }
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error searching events: {e}")
            return []
    
    def get_events_by_time_range(self, video_id: str, start_time: float, 
                                end_time: float, event_types: List[str] = None) -> List[Dict]:
        """Get events in a specific time range"""
        try:
            query = """
                SELECT * FROM events 
                WHERE video_id = ? AND ts >= ? AND ts <= ?
            """
            params = [video_id, start_time, end_time]
            
            if event_types:
                placeholders = ','.join(['?' for _ in event_types])
                query += f" AND type IN ({placeholders})"
                params.extend(event_types)
            
            query += " ORDER BY ts ASC"
            
            results = self.db.execute(query, params).fetchall()
            
            # Convert to list of dictionaries
            events = []
            for result in results:
                event = {
                    'video_id': result[0],
                    'ts': result[1],
                    'type': result[2],
                    'analysis_type': result[3],
                    'actor': json.loads(result[4]) if result[4] else {},
                    'location': result[5],
                    'attributes': json.loads(result[6]) if result[6] else {},
                    'visual_evidence': json.loads(result[7]) if result[7] else {},
                    'audio_evidence': json.loads(result[8]) if result[8] else {},
                    'combined_analysis': json.loads(result[9]) if result[9] else {},
                    'created_at': result[10]
                }
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events by time range: {e}")
            return []
    
    def get_events_by_actor(self, video_id: str, actor_class: str = None, 
                           track_id: str = None) -> List[Dict]:
        """Get events by actor class or track ID"""
        try:
            query = "SELECT * FROM events WHERE video_id = ?"
            params = [video_id]
            
            if actor_class:
                query += " AND actor LIKE ?"
                params.append(f'%"class": "{actor_class}"%')
            
            if track_id:
                query += " AND actor LIKE ?"
                params.append(f'%"track_id": "{track_id}"%')
            
            query += " ORDER BY ts ASC"
            
            results = self.db.execute(query, params).fetchall()
            
            # Convert to list of dictionaries
            events = []
            for result in results:
                event = {
                    'video_id': result[0],
                    'ts': result[1],
                    'type': result[2],
                    'analysis_type': result[3],
                    'actor': json.loads(result[4]) if result[4] else {},
                    'location': result[5],
                    'attributes': json.loads(result[6]) if result[6] else {},
                    'visual_evidence': json.loads(result[7]) if result[7] else {},
                    'audio_evidence': json.loads(result[8]) if result[8] else {},
                    'combined_analysis': json.loads(result[9]) if result[9] else {},
                    'created_at': result[10]
                }
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events by actor: {e}")
            return []
    
    def get_events_with_audio(self, video_id: str) -> List[Dict]:
        """Get events that have audio evidence"""
        try:
            query = """
                SELECT * FROM events 
                WHERE video_id = ? AND audio_evidence IS NOT NULL 
                AND audio_evidence != '{}' AND audio_evidence != 'null'
                ORDER BY ts ASC
            """
            
            results = self.db.execute(query, [video_id]).fetchall()
            
            # Convert to list of dictionaries
            events = []
            for result in results:
                event = {
                    'video_id': result[0],
                    'ts': result[1],
                    'type': result[2],
                    'analysis_type': result[3],
                    'actor': json.loads(result[4]) if result[4] else {},
                    'location': result[5],
                    'attributes': json.loads(result[6]) if result[6] else {},
                    'visual_evidence': json.loads(result[7]) if result[7] else {},
                    'audio_evidence': json.loads(result[8]) if result[8] else {},
                    'combined_analysis': json.loads(result[9]) if result[9] else {},
                    'created_at': result[10]
                }
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events with audio: {e}")
            return []
    
    def get_events_with_visual_evidence(self, video_id: str) -> List[Dict]:
        """Get events that have visual evidence"""
        try:
            query = """
                SELECT * FROM events 
                WHERE video_id = ? AND visual_evidence IS NOT NULL 
                AND visual_evidence != '{}' AND visual_evidence != 'null'
                ORDER BY ts ASC
            """
            
            results = self.db.execute(query, [video_id]).fetchall()
            
            # Convert to list of dictionaries
            events = []
            for result in results:
                event = {
                    'video_id': result[0],
                    'ts': result[1],
                    'type': result[2],
                    'analysis_type': result[3],
                    'actor': json.loads(result[4]) if result[4] else {},
                    'location': result[5],
                    'attributes': json.loads(result[6]) if result[6] else {},
                    'visual_evidence': json.loads(result[7]) if result[7] else {},
                    'audio_evidence': json.loads(result[8]) if result[8] else {},
                    'combined_analysis': json.loads(result[9]) if result[9] else {},
                    'created_at': result[10]
                }
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events with visual evidence: {e}")
            return []
    
    def get_high_confidence_events(self, video_id: str, confidence_threshold: float = 0.8) -> List[Dict]:
        """Get events with high confidence scores"""
        try:
            query = """
                SELECT * FROM events 
                WHERE video_id = ? AND attributes LIKE ?
                ORDER BY ts ASC
            """
            
            # Search for confidence values above threshold
            confidence_pattern = f'%"confidence": {confidence_threshold}%'
            params = [video_id, confidence_pattern]
            
            results = self.db.execute(query, params).fetchall()
            
            # Convert to list of dictionaries
            events = []
            for result in results:
                event = {
                    'video_id': result[0],
                    'ts': result[1],
                    'type': result[2],
                    'analysis_type': result[3],
                    'actor': json.loads(result[4]) if result[4] else {},
                    'location': result[5],
                    'attributes': json.loads(result[6]) if result[6] else {},
                    'visual_evidence': json.loads(result[7]) if result[7] else {},
                    'audio_evidence': json.loads(result[8]) if result[8] else {},
                    'combined_analysis': json.loads(result[9]) if result[9] else {},
                    'created_at': result[10]
                }
                
                # Check if confidence is actually above threshold
                confidence = event['attributes'].get('confidence', 0)
                if confidence >= confidence_threshold:
                    events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting high confidence events: {e}")
            return []
    
    def get_event_timeline(self, video_id: str, resolution: float = 1.0) -> List[Dict]:
        """Get event timeline with specified time resolution"""
        try:
            # Get all events for the video
            events = self.get_events(video_id=video_id)
            
            if not events:
                return []
            
            # Create timeline buckets
            timeline = {}
            for event in events:
                timestamp = event['ts']
                bucket = int(timestamp / resolution) * resolution
                
                if bucket not in timeline:
                    timeline[bucket] = {
                        'timestamp': bucket,
                        'events': [],
                        'event_count': 0,
                        'event_types': set()
                    }
                
                timeline[bucket]['events'].append(event)
                timeline[bucket]['event_count'] += 1
                timeline[bucket]['event_types'].add(event['type'])
            
            # Convert to list and sort by timestamp
            timeline_list = []
            for bucket, data in timeline.items():
                timeline_list.append({
                    'timestamp': data['timestamp'],
                    'event_count': data['event_count'],
                    'event_types': list(data['event_types']),
                    'events': data['events']
                })
            
            timeline_list.sort(key=lambda x: x['timestamp'])
            return timeline_list
            
        except Exception as e:
            logger.error(f"Error getting event timeline: {e}")
            return []
    
    def delete_events(self, video_id: str) -> bool:
        """Delete all events for a video"""
        try:
            self.db.execute("DELETE FROM events WHERE video_id = ?", [video_id])
            logger.info(f"Deleted events for video: {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting events: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'db'):
                self.db.close()
            
            logger.info("Event Service cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up Event Service: {e}") 