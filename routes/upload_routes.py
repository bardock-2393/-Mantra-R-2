#!/usr/bin/env python3
"""
Production-Grade Streaming Upload Routes
Fast, reliable 2GB+ video uploads with resumable, out-of-order chunks via Content-Range
Optimized for 80GB GPU environment
"""

import os
import re
import json
import uuid
import time
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from config import Config
from services.performance_service import measure_latency, cache_manager

upload_bp = Blueprint('upload', __name__, url_prefix='/upload')

# Content-Range regex for parsing byte ranges
RANGE_RE = re.compile(r"bytes (\d+)-(\d+)/(\d+)")

def state_path(upload_id):
    """Get path for upload state file"""
    return os.path.join(Config.UPLOAD_FOLDER, f"{upload_id}.json")

def temp_path(upload_id):
    """Get path for temporary upload file"""
    return os.path.join(Config.UPLOAD_FOLDER, f"{upload_id}.part")

def load_state(upload_id):
    """Load upload state from disk"""
    path = state_path(upload_id)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading upload state {upload_id}: {e}")
            return None
    return None

def save_state(upload_id, state):
    """Save upload state to disk"""
    try:
        with open(state_path(upload_id), "w") as f:
            json.dump(state, f)
    except IOError as e:
        print(f"Error saving upload state {upload_id}: {e}")
        raise

def merge_ranges(ranges):
    """Merge overlapping byte ranges for efficient storage"""
    if not ranges:
        return []
    
    # Sort by start position
    ranges = sorted(ranges, key=lambda x: x[0])
    merged = [ranges[0]]
    
    for start, end in ranges[1:]:
        last = merged[-1]
        # Merge if ranges overlap or are adjacent
        if start <= last[1] + 1:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    
    return merged

def is_complete_upload(received_ranges, total_size):
    """Check if upload is complete by verifying full coverage"""
    if total_size == 0:
        return False
    
    merged = merge_ranges(received_ranges)
    return (len(merged) == 1 and 
            merged[0][0] == 0 and 
            merged[0][1] == total_size - 1)

@upload_bp.route('/init', methods=['POST'])
@measure_latency("upload_init")
def init_upload():
    """Initialize a new streaming upload session"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        
        # Validate input
        filename = data.get("filename", "")
        if not filename:
            return jsonify({"error": "filename required"}), 400
        
        # Secure the filename
        filename = secure_filename(filename)
        if not filename:
            return jsonify({"error": "invalid filename"}), 400
        
        # Validate file extension
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            return jsonify({
                "error": f"Unsupported file type. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}"
            }), 400
        
        total_size = int(data.get("size", 0))
        if total_size <= 0:
            return jsonify({"error": "size must be > 0"}), 400
        
        # Check file size limit (2GB for 80GB GPU)
        if total_size > Config.MAX_CONTENT_LENGTH:
            return jsonify({
                "error": f"File too large. Maximum size: {Config.MAX_CONTENT_LENGTH / (1024**3):.1f}GB"
            }), 413
        
        # Generate unique upload ID
        upload_id = uuid.uuid4().hex
        
        # Create unique final filename to avoid conflicts
        timestamp = int(time.time())
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            final_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            final_filename = f"{filename}_{timestamp}"
        
        # Setup upload state
        state = {
            "upload_id": upload_id,
            "filename": filename,
            "final_filename": final_filename,
            "total_size": total_size,
            "received_ranges": [],  # list of [start, end] ranges
            "final_path": os.path.join(Config.UPLOAD_FOLDER, final_filename),
            "temp_path": temp_path(upload_id),
            "created_at": time.time(),
            "last_activity": time.time()
        }
        
        # Create upload directory if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Create empty file with proper size for random-access writes
        try:
            with open(state["temp_path"], "wb") as f:
                if total_size > 0:
                    f.truncate(total_size)
        except IOError as e:
            return jsonify({"error": f"Failed to create upload file: {str(e)}"}), 500
        
        # Save state
        save_state(upload_id, state)
        
        print(f"🚀 Upload initialized: {upload_id} ({filename}, {total_size / (1024**2):.1f}MB)")
        
        return jsonify({
            "upload_id": upload_id,
            "filename": final_filename,
            "total_size": total_size
        })
        
    except Exception as e:
        print(f"Error initializing upload: {e}")
        return jsonify({"error": "Upload initialization failed"}), 500

@upload_bp.route('/<upload_id>', methods=['PUT'])
@measure_latency("upload_chunk")
def upload_chunk(upload_id):
    """Upload a chunk with Content-Range header (streaming, no memory buffering)"""
    try:
        # Load upload state
        state = load_state(upload_id)
        if not state:
            return jsonify({"error": "Invalid upload_id"}), 404
        
        # Parse Content-Range header
        content_range = request.headers.get("Content-Range")
        if not content_range:
            return jsonify({"error": "Content-Range header required"}), 411
        
        match = RANGE_RE.match(content_range)
        if not match:
            return jsonify({"error": "Invalid Content-Range format"}), 400
        
        start, end, total = map(int, match.groups())
        
        # Validate range
        if start > end:
            return jsonify({"error": "Invalid range: start > end"}), 400
        
        if state["total_size"] and state["total_size"] != total:
            return jsonify({"error": "Size mismatch with initialized upload"}), 409
        
        if end >= total:
            return jsonify({"error": "Range exceeds total size"}), 400
        
        # Update last activity
        state["last_activity"] = time.time()
        
        # Stream write directly to disk at the specified offset (no memory buffering)
        try:
            # Use r+b mode for existing file with random access
            mode = "r+b" if os.path.exists(state["temp_path"]) else "wb"
            
            with open(state["temp_path"], mode) as f:
                f.seek(start)
                
                # Stream data in 1MB chunks to avoid memory issues
                stream = request.stream
                bytes_written = 0
                expected_bytes = end - start + 1
                
                while bytes_written < expected_bytes:
                    remaining = expected_bytes - bytes_written
                    chunk_size = min(1024 * 1024, remaining)  # 1MB chunks
                    
                    chunk = stream.read(chunk_size)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    bytes_written += len(chunk)
                
                f.flush()  # Ensure data is written to disk
                
        except IOError as e:
            return jsonify({"error": f"Failed to write chunk: {str(e)}"}), 500
        
        # Update received ranges
        state["received_ranges"] = merge_ranges(state["received_ranges"] + [[start, end]])
        save_state(upload_id, state)
        
        # Calculate progress
        total_received = sum(r[1] - r[0] + 1 for r in state["received_ranges"])
        progress = (total_received / state["total_size"]) * 100 if state["total_size"] > 0 else 0
        
        print(f"📦 Chunk received: {upload_id} [{start}-{end}] ({progress:.1f}% complete)")
        
        return jsonify({
            "ok": True,
            "received_ranges": state["received_ranges"],
            "progress": progress,
            "bytes_received": total_received
        })
        
    except Exception as e:
        print(f"Error uploading chunk: {e}")
        return jsonify({"error": "Chunk upload failed"}), 500

@upload_bp.route('/<upload_id>/status', methods=['GET'])
@measure_latency("upload_status")
def upload_status(upload_id):
    """Get upload status and received ranges"""
    try:
        state = load_state(upload_id)
        if not state:
            return jsonify({"error": "Invalid upload_id"}), 404
        
        # Calculate progress
        total_received = sum(r[1] - r[0] + 1 for r in state["received_ranges"])
        progress = (total_received / state["total_size"]) * 100 if state["total_size"] > 0 else 0
        
        return jsonify({
            "upload_id": upload_id,
            "filename": state["filename"],
            "total_size": state["total_size"],
            "received_ranges": state["received_ranges"],
            "progress": progress,
            "bytes_received": total_received,
            "is_complete": is_complete_upload(state["received_ranges"], state["total_size"]),
            "created_at": state["created_at"],
            "last_activity": state["last_activity"]
        })
        
    except Exception as e:
        print(f"Error getting upload status: {e}")
        return jsonify({"error": "Failed to get status"}), 500

@upload_bp.route('/<upload_id>/complete', methods=['POST'])
@measure_latency("upload_complete")
def complete_upload(upload_id):
    """Complete the upload and move to final location"""
    try:
        state = load_state(upload_id)
        if not state:
            return jsonify({"error": "Invalid upload_id"}), 404
        
        # Verify upload is complete
        if not is_complete_upload(state["received_ranges"], state["total_size"]):
            total_received = sum(r[1] - r[0] + 1 for r in state["received_ranges"])
            return jsonify({
                "error": "Upload incomplete",
                "received_ranges": state["received_ranges"],
                "total_size": state["total_size"],
                "bytes_received": total_received,
                "progress": (total_received / state["total_size"]) * 100
            }), 409
        
        # Verify file exists and has correct size
        if not os.path.exists(state["temp_path"]):
            return jsonify({"error": "Upload file not found"}), 404
        
        actual_size = os.path.getsize(state["temp_path"])
        if actual_size != state["total_size"]:
            return jsonify({
                "error": "File size mismatch",
                "expected": state["total_size"],
                "actual": actual_size
            }), 409
        
        # Move to final path atomically
        try:
            os.makedirs(os.path.dirname(state["final_path"]), exist_ok=True)
            os.replace(state["temp_path"], state["final_path"])
        except OSError as e:
            return jsonify({"error": f"Failed to finalize upload: {str(e)}"}), 500
        
        # Update state
        state["completed_at"] = time.time()
        save_state(upload_id, state)
        
        # Clean up old state files (optional)
        try:
            os.remove(state_path(upload_id))
        except OSError:
            pass  # Not critical if cleanup fails
        
        upload_time = state["completed_at"] - state["created_at"]
        upload_speed = (state["total_size"] / (1024**2)) / upload_time if upload_time > 0 else 0
        
        print(f"✅ Upload completed: {state['final_filename']} ({state['total_size'] / (1024**2):.1f}MB in {upload_time:.1f}s, {upload_speed:.1f}MB/s)")
        
        return jsonify({
            "ok": True,
            "upload_id": upload_id,
            "filename": state["final_filename"],
            "file_path": state["final_path"],
            "size": state["total_size"],
            "upload_time": upload_time,
            "average_speed": upload_speed
        })
        
    except Exception as e:
        print(f"Error completing upload: {e}")
        return jsonify({"error": "Upload completion failed"}), 500

@upload_bp.route('/<upload_id>/cancel', methods=['DELETE'])
@measure_latency("upload_cancel")
def cancel_upload(upload_id):
    """Cancel an upload and clean up files"""
    try:
        state = load_state(upload_id)
        if not state:
            return jsonify({"error": "Invalid upload_id"}), 404
        
        # Clean up files
        for file_path in [state["temp_path"], state_path(upload_id)]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError as e:
                print(f"Warning: Failed to cleanup {file_path}: {e}")
        
        print(f"🚫 Upload cancelled: {upload_id}")
        
        return jsonify({
            "ok": True,
            "message": f"Upload {upload_id} cancelled and cleaned up"
        })
        
    except Exception as e:
        print(f"Error cancelling upload: {e}")
        return jsonify({"error": "Upload cancellation failed"}), 500

@upload_bp.route('/cleanup', methods=['POST'])
@measure_latency("upload_cleanup")
def cleanup_old_uploads():
    """Clean up old incomplete uploads (admin endpoint)"""
    try:
        if not Config.DEVELOPMENT:
            return jsonify({"error": "Cleanup only available in development"}), 403
        
        current_time = time.time()
        cleanup_age = 3600  # 1 hour
        cleaned_files = []
        
        # Find and clean old upload files
        for filename in os.listdir(Config.UPLOAD_FOLDER):
            if filename.endswith('.json') or filename.endswith('.part'):
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                try:
                    if current_time - os.path.getmtime(file_path) > cleanup_age:
                        os.remove(file_path)
                        cleaned_files.append(filename)
                except OSError:
                    continue
        
        return jsonify({
            "ok": True,
            "cleaned_files": cleaned_files,
            "count": len(cleaned_files)
        })
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return jsonify({"error": "Cleanup failed"}), 500