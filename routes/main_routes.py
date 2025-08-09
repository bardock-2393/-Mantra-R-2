"""
Main Routes Module
Handles core application routes like index, upload, and analysis
"""

import os
import json
import uuid
import shutil
import re
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, send_file
from werkzeug.utils import secure_filename
from config import Config
from services.session_service import generate_session_id, store_session_data, get_session_data, cleanup_old_uploads
from services.ai_service import analyze_video_with_gemini
from services.performance_service import measure_latency
from utils.video_utils import extract_video_metadata, create_evidence_for_timestamps
from utils.text_utils import extract_timestamps_from_text, extract_timestamp_ranges_from_text
from analysis_templates import ANALYSIS_TEMPLATES

# Create Blueprint
main_bp = Blueprint('main', __name__)

# Streaming upload configuration
RANGE_RE = re.compile(r"bytes (\d+)-(\d+)/(\d+)")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def state_path(upload_id):
    """Get upload state file path"""
    return os.path.join(Config.UPLOAD_FOLDER, f"{upload_id}.json")

def temp_path(upload_id):
    """Get temporary upload file path"""
    return os.path.join(Config.UPLOAD_FOLDER, f"{upload_id}.part")

def load_state(upload_id):
    """Load upload state from disk"""
    p = state_path(upload_id)
    if os.path.exists(p):
        with open(p, "r") as f:
            return json.load(f)
    return None

def save_state(upload_id, state):
    """Save upload state to disk"""
    with open(state_path(upload_id), "w") as f:
        json.dump(state, f)

def merge_ranges(ranges):
    """Merge overlapping byte ranges"""
    if not ranges:
        return []
    ranges = sorted(ranges, key=lambda x: x[0])
    merged = [ranges[0]]
    for s, e in ranges[1:]:
        last = merged[-1]
        if s <= last[1] + 1:
            last[1] = max(last[1], e)
        else:
            merged.append([s, e])
    return merged

@main_bp.route('/')
def index():
    """Main page"""
    # Clean up old files when user visits the page
    cleanup_old_uploads()
    
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()
    return render_template('index.html')

@main_bp.route('/api/analysis-types')
def get_analysis_types():
    """Get available analysis types"""
    return jsonify({
        'analysis_types': ANALYSIS_TEMPLATES,
        'success': True
    })

# === STREAMING UPLOAD ENDPOINTS ===

@main_bp.route('/upload/init', methods=['POST'])
@measure_latency("streaming_upload_init")
def init_streaming_upload():
    """Initialize streaming upload for large files"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        filename = secure_filename(data.get("filename", "file.bin"))
        
        if not allowed_file(filename):
            return jsonify({"error": "Invalid file type"}), 400
            
        total = int(data.get("size", 0))
        if total > Config.MAX_CONTENT_LENGTH:
            return jsonify({"error": f"File too large. Max size: {Config.MAX_CONTENT_LENGTH} bytes"}), 413
            
        upload_id = uuid.uuid4().hex
        session_id = session.get('session_id', generate_session_id())
        session['session_id'] = session_id
        
        # Create unique filename with session
        name, ext = os.path.splitext(filename)
        unique_filename = f"{session_id}_{name}_{uuid.uuid4().hex[:8]}{ext}"
        final_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        
        state = {
            "upload_id": upload_id,
            "session_id": session_id,
            "filename": filename,
            "unique_filename": unique_filename,
            "total": total,
            "received": [],  # list of [start, end]
            "final_path": final_path,
            "temp_path": temp_path(upload_id),
            "created_at": datetime.now().isoformat()
        }
        
        save_state(upload_id, state)
        
        # Create empty file to enable random-access writes
        with open(state["temp_path"], "wb") as f:
            if total > 0:
                f.truncate(total)
                
        print(f"🚀 Streaming upload initialized: {upload_id} ({filename}, {total} bytes)")
        
        return jsonify({
            "upload_id": upload_id,
            "session_id": session_id,
            "chunk_size": 16 * 1024 * 1024,  # 16MB chunks
            "max_parallel": 4
        })
        
    except Exception as e:
        print(f"❌ Streaming upload init error: {e}")
        return jsonify({"error": str(e)}), 500

@main_bp.route('/upload/<upload_id>', methods=['PUT'])
@measure_latency("streaming_upload_chunk")
def upload_chunk(upload_id):
    """Handle streaming upload chunk with Content-Range"""
    try:
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
        
        # Validate total size consistency
        if state["total"] and state["total"] != total:
            return jsonify({"error": "Size mismatch"}), 409

        # Stream chunk directly to disk at correct offset
        mode = "r+b" if os.path.exists(state["temp_path"]) else "wb"
        with open(state["temp_path"], mode) as f:
            f.seek(start)
            
            # Stream in 1MB blocks to avoid memory usage
            bytes_written = 0
            target_bytes = end - start + 1
            
            while bytes_written < target_bytes:
                chunk = request.stream.read(min(1024 * 1024, target_bytes - bytes_written))
                if not chunk:
                    break
                f.write(chunk)
                bytes_written += len(chunk)

        # Update received ranges
        state["received"] = merge_ranges(state["received"] + [[start, end]])
        save_state(upload_id, state)
        
        progress = sum(r[1] - r[0] + 1 for r in state["received"]) / state["total"] * 100
        
        print(f"📊 Chunk received: {upload_id} [{start}-{end}] ({progress:.1f}%)")
        
        return jsonify({
            "ok": True,
            "received": state["received"],
            "progress": progress
        })
        
    except Exception as e:
        print(f"❌ Chunk upload error: {e}")
        return jsonify({"error": str(e)}), 500

@main_bp.route('/upload/<upload_id>/status', methods=['GET'])
def get_upload_status(upload_id):
    """Get streaming upload status"""
    try:
        state = load_state(upload_id)
        if not state:
            return jsonify({"error": "Invalid upload_id"}), 404
            
        progress = 0
        if state["total"] > 0:
            received_bytes = sum(r[1] - r[0] + 1 for r in state["received"])
            progress = received_bytes / state["total"] * 100
            
        return jsonify({
            "upload_id": upload_id,
            "total": state["total"],
            "received": state["received"],
            "progress": progress,
            "filename": state["filename"]
        })
        
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return jsonify({"error": str(e)}), 500

@main_bp.route('/upload/<upload_id>/complete', methods=['POST'])
@measure_latency("streaming_upload_complete")
def complete_streaming_upload(upload_id):
    """Complete streaming upload and finalize file"""
    try:
        state = load_state(upload_id)
        if not state:
            return jsonify({"error": "Invalid upload_id"}), 404

        # Verify upload completion
        if state["total"] == 0:
            size = os.path.getsize(state["temp_path"])
            state["total"] = size
            
        received = merge_ranges(state["received"])
        is_complete = (len(received) == 1 and 
                      received[0][0] == 0 and 
                      received[0][1] == state["total"] - 1)
        
        if not is_complete:
            return jsonify({
                "error": "Upload incomplete",
                "received": received,
                "total": state["total"],
                "missing_ranges": []  # Could calculate missing ranges here
            }), 409

        # Atomic move to final location
        os.makedirs(os.path.dirname(state["final_path"]), exist_ok=True)
        os.replace(state["temp_path"], state["final_path"])
        
        # Store session data for analysis
        session_data = {
            'filepath': state["final_path"],
            'filename': state["filename"],
            'upload_time': datetime.now().isoformat(),
            'session_id': state["session_id"],
            'file_size': state["total"],
            'upload_method': 'streaming'
        }
        
        store_session_data(state["session_id"], session_data)
        
        # Cleanup state file
        try:
            os.remove(state_path(upload_id))
        except:
            pass
            
        print(f"✅ Streaming upload complete: {state['filename']} ({state['total']} bytes)")
        
        return jsonify({
            "ok": True,
            "path": state["final_path"],
            "filename": state["filename"],
            "size": state["total"],
            "session_id": state["session_id"],
            "message": "Upload completed successfully"
        })
        
    except Exception as e:
        print(f"❌ Upload completion error: {e}")
        return jsonify({"error": str(e)}), 500

@main_bp.route('/upload', methods=['POST'])
@measure_latency("video_upload")
def upload_video():
    """Handle video upload"""
    try:
        session_id = session.get('session_id', generate_session_id())
        print(f"Debug: Upload - Session ID: {session_id}")
        
        # Check if video file was uploaded
        if 'video' in request.files and request.files['video'].filename != '':
            # User uploaded a file
            file = request.files['video']
            
            if not allowed_file(file.filename):
                return jsonify({'error': 'Invalid file type. Please upload MP4, AVI, MOV, WebM, or MKV'}), 400
            
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
            
            # Save file
            file.save(filepath)
            
            # Extract video metadata
            video_metadata = extract_video_metadata(filepath)
            
            file_info = {
                'filename': unique_filename,
                'original_name': filename,
                'filepath': filepath,
                'upload_time': datetime.now().isoformat(),
                'status': 'uploaded',
                'metadata': json.dumps(video_metadata),
                'is_default_video': False
            }
            
        else:
            # No file uploaded, use default video
            default_video_path = Config.DEFAULT_VIDEO_PATH
            
            if not os.path.exists(default_video_path):
                return jsonify({'error': 'Default video file not found'}), 500
            
            # Copy default video to uploads folder with unique name
            filename = os.path.basename(default_video_path)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
            
            # Copy the default video file
            shutil.copy2(default_video_path, filepath)
            
            # Extract video metadata
            video_metadata = extract_video_metadata(filepath)
            
            file_info = {
                'filename': unique_filename,
                'original_name': filename,
                'filepath': filepath,
                'upload_time': datetime.now().isoformat(),
                'status': 'uploaded',
                'metadata': json.dumps(video_metadata),
                'is_default_video': True
            }
        
        print(f"Debug: Upload - File info: {file_info}")
        store_session_data(session_id, file_info)
        
        # Verify storage
        stored_data = get_session_data(session_id)
        print(f"Debug: Upload - Stored data keys: {list(stored_data.keys()) if stored_data else 'None'}")
        
        message = 'Default video loaded successfully' if file_info.get('is_default_video', False) else 'Video uploaded successfully'
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'message': message,
            'is_default_video': file_info.get('is_default_video', False)
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@main_bp.route('/analyze', methods=['POST'])
@measure_latency("video_analysis_endpoint")
def analyze_video():
    """Analyze uploaded video"""
    try:
        data = request.get_json()
        analysis_type = data.get('analysis_type', 'comprehensive_analysis')
        user_focus = data.get('user_focus', 'Analyze this video comprehensively')
        
        session_id = session.get('session_id')
        print(f"Debug: Session ID: {session_id}")
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session found'})
        
        # Get session data
        session_data = get_session_data(session_id)
        print(f"Debug: Session data keys: {list(session_data.keys()) if session_data else 'None'}")
        print(f"Debug: Session data: {session_data}")
        
        if not session_data or 'filepath' not in session_data:
            return jsonify({'success': False, 'error': 'No video uploaded'})
        
        video_path = session_data['filepath']
        print(f"Debug: Video path: {video_path}")
        
        if not os.path.exists(video_path):
            return jsonify({'success': False, 'error': 'Video file not found'})
        
        # Perform analysis with real-time WebSocket updates
        import asyncio
        analysis_result = asyncio.run(analyze_video_with_gemini(video_path, analysis_type, user_focus, session_id))
        
        # Extract timestamps and capture screenshots automatically
        timestamps = extract_timestamps_from_text(analysis_result)
        evidence = []
        
        if timestamps:
            # Create evidence (screenshots or video clips) based on timeframe length
            evidence = create_evidence_for_timestamps(timestamps, video_path, session_id, Config.UPLOAD_FOLDER)
        
        # Store analysis results and evidence in session
        analysis_data = {
            'analysis_result': analysis_result,
            'analysis_type': analysis_type,
            'user_focus': user_focus,
            'timestamps_found': timestamps,
            'evidence': evidence,
            'analysis_time': datetime.now().isoformat()
        }
        
        # Update session data
        session_data.update(analysis_data)
        store_session_data(session_id, session_data)
        
        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'timestamps': timestamps,
            'evidence': evidence,
            'evidence_count': len(evidence)
        })
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@main_bp.route('/screenshot/<filename>')
def get_screenshot(filename):
    """Serve screenshot files"""
    try:
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Screenshot not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/demo-video')
def get_demo_video():
    """Serve the demo video file"""
    try:
        demo_video_path = Config.DEFAULT_VIDEO_PATH
        if os.path.exists(demo_video_path):
            return send_file(demo_video_path, mimetype='video/mp4')
        else:
            return jsonify({'error': 'Demo video not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500 