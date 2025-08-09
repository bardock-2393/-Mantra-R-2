"""
Fast HTTP Chunked Upload Routes
High-performance file upload system for 2GB video files
"""

import os
import time
from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
from config import Config
from services.performance_service import measure_latency

upload_bp = Blueprint('upload', __name__)

# Global upload sessions tracking
upload_sessions = {}

@upload_bp.route('/upload/start', methods=['POST'])
@measure_latency("upload_start")
def start_chunked_upload():
    """Initialize a chunked upload session"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        file_size = data.get('file_size')
        total_chunks = data.get('total_chunks')
        
        if not all([filename, file_size, total_chunks]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: filename, file_size, total_chunks'
            }), 400
        
        # Validate file size (2GB limit)
        if file_size > Config.MAX_CONTENT_LENGTH:
            return jsonify({
                'success': False,
                'error': f'File size ({file_size / (1024**3):.1f}GB) exceeds 2GB limit'
            }), 400
        
        # Validate file type
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            return jsonify({
                'success': False,
                'error': f'File type .{file_ext} not supported'
            }), 400
        
        # Create session ID and upload directory
        session_id = session.get('session_id', f"session_{int(time.time())}")
        session['session_id'] = session_id
        
        upload_id = f"{session_id}_{int(time.time())}"
        upload_dir = os.path.join(Config.UPLOAD_FOLDER, session_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Secure filename
        safe_filename = secure_filename(filename)
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Initialize upload session
        upload_sessions[upload_id] = {
            'filename': safe_filename,
            'file_path': file_path,
            'file_size': file_size,
            'total_chunks': total_chunks,
            'received_chunks': set(),
            'bytes_received': 0,
            'started_at': time.time(),
            'session_id': session_id
        }
        
        print(f"🚀 Started chunked upload: {safe_filename} ({file_size / (1024**2):.1f}MB, {total_chunks} chunks)")
        
        return jsonify({
            'success': True,
            'upload_id': upload_id,
            'message': f'Upload session created for {safe_filename}'
        })
        
    except Exception as e:
        print(f"❌ Error starting upload: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start upload: {str(e)}'
        }), 500

@upload_bp.route('/upload/chunk/<upload_id>/<int:chunk_index>', methods=['POST'])
@measure_latency("upload_chunk")
def upload_chunk(upload_id, chunk_index):
    """Upload a single chunk via HTTP"""
    try:
        if upload_id not in upload_sessions:
            return jsonify({
                'success': False,
                'error': 'Upload session not found'
            }), 404
        
        upload_session = upload_sessions[upload_id]
        
        # Check if chunk already received
        if chunk_index in upload_session['received_chunks']:
            return jsonify({
                'success': True,
                'message': 'Chunk already received',
                'duplicate': True
            })
        
        # Get chunk data from request
        if 'chunk' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No chunk data provided'
            }), 400
        
        chunk_file = request.files['chunk']
        chunk_data = chunk_file.read()
        chunk_size = len(chunk_data)
        
        # Append chunk to file
        with open(upload_session['file_path'], 'ab') as f:
            f.write(chunk_data)
        
        # Update session
        upload_session['received_chunks'].add(chunk_index)
        upload_session['bytes_received'] += chunk_size
        
        # Calculate progress
        progress = (upload_session['bytes_received'] / upload_session['file_size']) * 100
        upload_speed = upload_session['bytes_received'] / (time.time() - upload_session['started_at']) / (1024**2)
        
        # Check if upload complete
        is_complete = len(upload_session['received_chunks']) == upload_session['total_chunks']
        
        response_data = {
            'success': True,
            'chunk_index': chunk_index,
            'progress': progress,
            'bytes_received': upload_session['bytes_received'],
            'total_size': upload_session['file_size'],
            'upload_speed': upload_speed,
            'chunks_received': len(upload_session['received_chunks']),
            'total_chunks': upload_session['total_chunks'],
            'complete': is_complete
        }
        
        if is_complete:
            upload_time = time.time() - upload_session['started_at']
            avg_speed = upload_session['file_size'] / upload_time / (1024**2)
            
            # Verify file size
            actual_size = os.path.getsize(upload_session['file_path'])
            if actual_size != upload_session['file_size']:
                return jsonify({
                    'success': False,
                    'error': f'File size mismatch: expected {upload_session["file_size"]}, got {actual_size}'
                }), 400
            
            response_data.update({
                'file_path': upload_session['file_path'],
                'upload_time': upload_time,
                'average_speed': avg_speed,
                'message': f'✅ Upload complete: {upload_session["filename"]} ({avg_speed:.1f}MB/s avg)'
            })
            
            # Store file info in session for analysis
            session['filepath'] = upload_session['file_path']
            session['filename'] = upload_session['filename']
            session['file_size'] = upload_session['file_size']
            
            print(f"✅ Upload completed: {upload_session['filename']} ({avg_speed:.1f}MB/s)")
            
            # Cleanup upload session
            del upload_sessions[upload_id]
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error uploading chunk {chunk_index}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to upload chunk: {str(e)}'
        }), 500

@upload_bp.route('/upload/status/<upload_id>', methods=['GET'])
def get_upload_status(upload_id):
    """Get current upload status"""
    try:
        if upload_id not in upload_sessions:
            return jsonify({
                'success': False,
                'error': 'Upload session not found'
            }), 404
        
        upload_session = upload_sessions[upload_id]
        progress = (upload_session['bytes_received'] / upload_session['file_size']) * 100
        upload_speed = upload_session['bytes_received'] / (time.time() - upload_session['started_at']) / (1024**2)
        
        return jsonify({
            'success': True,
            'upload_id': upload_id,
            'progress': progress,
            'bytes_received': upload_session['bytes_received'],
            'total_size': upload_session['file_size'],
            'upload_speed': upload_speed,
            'chunks_received': len(upload_session['received_chunks']),
            'total_chunks': upload_session['total_chunks']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get status: {str(e)}'
        }), 500

@upload_bp.route('/upload/cancel/<upload_id>', methods=['POST'])
def cancel_upload(upload_id):
    """Cancel an active upload"""
    try:
        if upload_id not in upload_sessions:
            return jsonify({
                'success': False,
                'error': 'Upload session not found'
            }), 404
        
        upload_session = upload_sessions[upload_id]
        
        # Remove partial file
        if os.path.exists(upload_session['file_path']):
            os.remove(upload_session['file_path'])
        
        # Remove session
        del upload_sessions[upload_id]
        
        return jsonify({
            'success': True,
            'message': 'Upload cancelled successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to cancel upload: {str(e)}'
        }), 500