"""
Text Utilities Module
Handles timestamp extraction and text processing functionality
"""

import re

def extract_timestamps_from_text(text):
    """Extract timestamps from text using regex patterns"""
    # Pattern for timestamps like 00:15, 1:30, 00:15-00:17, etc.
    timestamp_patterns = [
        r'(\d{1,2}):(\d{2})(?::(\d{2}))?',  # MM:SS or HH:MM:SS
        r'(\d{1,2})\.(\d{2})',  # MM.SS format
        r'(\d+)s',  # seconds format
        r'(\d+)\.(\d+)s'  # decimal seconds
    ]
    
    timestamps = []
    
    for pattern in timestamp_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            if ':' in match.group():
                # Handle MM:SS or HH:MM:SS format
                parts = match.group().split(':')
                if len(parts) == 2:
                    minutes, seconds = int(parts[0]), int(parts[1])
                    timestamp = minutes * 60 + seconds
                elif len(parts) == 3:
                    hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                    timestamp = hours * 3600 + minutes * 60 + seconds
            elif '.' in match.group() and 's' not in match.group():
                # Handle MM.SS format
                parts = match.group().split('.')
                minutes, seconds = int(parts[0]), int(parts[1])
                timestamp = minutes * 60 + seconds
            elif 's' in match.group():
                # Handle seconds format
                timestamp = float(match.group().replace('s', ''))
            else:
                continue
                
            if 0 <= timestamp <= 3600:  # Reasonable range (0-1 hour)
                timestamps.append(timestamp)
    
    # Remove duplicates and sort
    timestamps = sorted(list(set(timestamps)))
    
    # Prioritize timestamps that are mentioned in key events
    # Look for specific patterns that indicate important moments
    key_events = []
    for match in re.finditer(r'(\d{1,2}):(\d{2})', text):
        minutes, seconds = int(match.group(1)), int(match.group(2))
        timestamp = minutes * 60 + seconds
        if 0 <= timestamp <= 3600:
            key_events.append(timestamp)
    
    # Combine and prioritize key events
    all_timestamps = list(set(timestamps + key_events))
    all_timestamps.sort()
    
    # Return up to 8 most relevant timestamps
    return all_timestamps[:8]

def extract_timestamp_ranges_from_text(text):
    """Extract timestamp ranges from text (e.g., '00:15-00:17')"""
    ranges = []
    # Pattern for timestamp ranges like 00:15-00:17, 1:30-1:45, etc.
    range_pattern = r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*-\s*(\d{1,2}):(\d{2})(?::(\d{2}))?'
    
    for match in re.finditer(range_pattern, text):
        # Parse start time
        start_hours = int(match.group(3)) if match.group(3) else 0
        start_minutes = int(match.group(1))
        start_seconds = int(match.group(2))
        start_time = start_hours * 3600 + start_minutes * 60 + start_seconds
        
        # Parse end time
        end_hours = int(match.group(6)) if match.group(6) else 0
        end_minutes = int(match.group(4))
        end_seconds = int(match.group(5))
        end_time = end_hours * 3600 + end_minutes * 60 + end_seconds
        
        if 0 <= start_time <= end_time <= 3600:  # Reasonable range
            ranges.append((start_time, end_time))
    
    return ranges 