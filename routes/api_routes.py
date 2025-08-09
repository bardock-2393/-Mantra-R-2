"""
API Routes Module
Handles various API endpoints for session management, health checks, and utility functions
"""

import os
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from config import Config, AGENT_CAPABILITIES, AGENT_TOOLS
from services.session_service import (
    get_session_data, cleanup_session_data, cleanup_expired_sessions, 
    cleanup_old_uploads, get_all_session_keys
)
from services.performance_service import get_performance_stats, check_round2_compliance
from services.video_streaming_service import start_90fps_analysis, get_realtime_stats, stop_realtime_analysis
from utils.video_utils import capture_screenshot, extract_video_clip
from utils.text_utils import extract_timestamps_from_text

# Create Blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/session/<session_id>')
def get_session(session_id):
    """Get session data"""
    try:
        session_data = get_session_data(session_id)
        return jsonify(session_data)
    except Exception as e:
        return jsonify({'error': f'Failed to get session: {str(e)}'}), 500

@api_bp.route('/health')
def health_check():
    """Health check endpoint"""
    from services.session_service import redis_client
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'agent_capabilities': AGENT_CAPABILITIES,
        'agent_tools': AGENT_TOOLS,
        'redis_connected': redis_client.ping(),
        'gemini_configured': bool(Config.GOOGLE_API_KEY)
    })

@api_bp.route('/api/agent-info')
def get_agent_info():
    """Get information about the AI agent capabilities"""
    from analysis_templates import ANALYSIS_TEMPLATES
    return jsonify({
        'agent_name': 'AI Video Detective Agent',
        'version': '2.0.0',
        'description': 'Advanced AI video analysis agent with comprehensive understanding capabilities',
        'capabilities': AGENT_CAPABILITIES,
        'tools': AGENT_TOOLS,
        'analysis_types': {
            key: {
                'name': value['name'],
                'description': value['description'],
                'icon': value['icon'],
                'agent_capabilities': value.get('agent_capabilities', [])
            }
            for key, value in ANALYSIS_TEMPLATES.items()
        },
        'features': [
            'Autonomous video analysis with multi-modal understanding',
            'Context-aware conversations with memory',
            'Proactive insights generation',
            'Comprehensive reporting across multiple dimensions',
            'Adaptive focus based on content and user needs',
            'Professional-grade analysis protocols',
            'Real-time conversation with video context',
            'Advanced pattern recognition and behavioral analysis'
        ]
    })

@api_bp.route('/capture-screenshots', methods=['POST'])
def capture_screenshots():
    """Capture screenshots at specific timestamps from the analyzed video"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        timestamps = data.get('timestamps', [])
        
        if not session_id:
            return jsonify({'success': False, 'error': 'Session ID required'})
        
        # Get session data
        session_data = get_session_data(session_id)
        if not session_data or 'filepath' not in session_data:
            return jsonify({'success': False, 'error': 'No video found for session'})
        
        video_path = session_data['filepath']
        
        if not os.path.exists(video_path):
            return jsonify({'success': False, 'error': 'Video file not found'})
        
        # Capture screenshots for each timestamp
        screenshots = []
        for timestamp in timestamps:
            screenshot_data = capture_screenshot(video_path, timestamp, session_id, Config.UPLOAD_FOLDER)
            if screenshot_data:
                screenshots.append(screenshot_data)
        
        return jsonify({
            'success': True,
            'screenshots': screenshots,
            'count': len(screenshots)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/auto-capture-screenshots', methods=['POST'])
def auto_capture_screenshots():
    """Automatically capture screenshots based on timestamps found in analysis text"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        analysis_text = data.get('analysis_text', '')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'Session ID required'})
        
        # Extract timestamps from analysis text
        timestamps = extract_timestamps_from_text(analysis_text)
        
        if not timestamps:
            return jsonify({'success': False, 'error': 'No timestamps found in analysis'})
        
        # Get session data
        session_data = get_session_data(session_id)
        if not session_data or 'filepath' not in session_data:
            return jsonify({'success': False, 'error': 'No video found for session'})
        
        video_path = session_data['filepath']
        
        if not os.path.exists(video_path):
            return jsonify({'success': False, 'error': 'Video file not found'})
        
        # Capture screenshots for extracted timestamps
        screenshots = []
        for timestamp in timestamps:
            screenshot_data = capture_screenshot(video_path, timestamp, session_id, Config.UPLOAD_FOLDER)
            if screenshot_data:
                screenshots.append(screenshot_data)
        
        return jsonify({
            'success': True,
            'screenshots': screenshots,
            'timestamps': timestamps,
            'count': len(screenshots)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/session/cleanup', methods=['POST'])
def cleanup_current_session():
    """Clean up the current session data and files"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': 'No active session'})
        
        # Clean up session data
        success = cleanup_session_data(session_id)
        
        if success:
            # Clear Flask session
            session.clear()
            return jsonify({
                'success': True,
                'message': 'Session cleaned up successfully',
                'session_id': session_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to cleanup session'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/session/status')
def get_session_status():
    """Get current session status and file information"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({
                'active': False,
                'session_id': None,
                'message': 'No active session'
            })
        
        # Get session data
        session_data = get_session_data(session_id)
        
        if not session_data:
            return jsonify({
                'active': False,
                'session_id': session_id,
                'message': 'Session data not found'
            })
        
        # Check if video file exists
        video_exists = False
        video_size = 0
        if 'filepath' in session_data:
            video_path = session_data['filepath']
            if os.path.exists(video_path):
                video_exists = True
                video_size = os.path.getsize(video_path)
        
        # Count evidence files
        evidence_count = 0
        upload_folder = Config.UPLOAD_FOLDER
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                if filename.startswith(f"screenshot_{session_id}_") or filename.startswith(f"clip_{session_id}_"):
                    evidence_count += 1
        
        return jsonify({
            'active': True,
            'session_id': session_id,
            'video_uploaded': video_exists,
            'video_size': video_size,
            'evidence_count': evidence_count,
            'analysis_complete': 'analysis_result' in session_data,
            'upload_time': session_data.get('upload_time'),
            'analysis_time': session_data.get('analysis_time')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/session/cleanup-all', methods=['POST'])
def cleanup_all_sessions():
    """Clean up all sessions (admin function)"""
    try:
        # Get all session keys from Redis
        session_keys = get_all_session_keys()
        cleaned_sessions = 0
        
        for session_id in session_keys:
            if cleanup_session_data(session_id):
                cleaned_sessions += 1
        
        # Also clean up old uploads
        cleanup_old_uploads()
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {cleaned_sessions} sessions and old uploads',
            'cleaned_count': cleaned_sessions
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/cleanup-uploads', methods=['POST'])
def cleanup_uploads():
    """Clean up old upload files"""
    try:
        cleanup_old_uploads()
        return jsonify({
            'success': True,
            'message': 'Uploads cleanup completed'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Uploads cleanup failed: {str(e)}'
        }), 500

@api_bp.route('/performance/stats')
def get_performance_statistics():
    """Get Round 2 performance statistics and latency metrics"""
    try:
        stats = get_performance_stats()
        compliance = check_round2_compliance()
        
        return jsonify({
            'success': True,
            'round2_compliance': compliance,
            'detailed_stats': stats,
            'system_info': {
                'target_latency_ms': 1000,
                'target_success_rate': 95.0,
                'cache_enabled': True,
                'gpu_optimized': True
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Performance stats failed: {str(e)}'
        }), 500

@api_bp.route('/performance/round2-check')
def check_round2_performance():
    """Check if system meets Round 2 performance requirements"""
    try:
        compliance = check_round2_compliance()
        
        # Determine overall status
        overall_status = "PASSING" if compliance['passing'] else "FAILING"
        
        return jsonify({
            'success': True,
            'round2_status': overall_status,
            'requirements': {
                'latency_target': '< 1000ms',
                'success_rate_target': '≥ 95%',
                'video_duration_support': '120 minutes',
                'fps_support': '90 FPS'
            },
            'current_performance': compliance,
            'recommendations': _get_performance_recommendations(compliance),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Round 2 check failed: {str(e)}'
        }), 500

def _get_performance_recommendations(compliance):
    """Generate performance improvement recommendations"""
    recommendations = []
    
    if not compliance['passing']:
        recommendations.append("System not meeting Round 2 performance targets")
        
        for op, data in compliance['operations'].items():
            if not data['passing']:
                if data['avg_latency_ms'] > 1000:
                    recommendations.append(f"Optimize {op}: Current latency {data['avg_latency_ms']:.0f}ms > 1000ms target")
                if data['success_rate'] < 95.0:
                    recommendations.append(f"Improve {op} reliability: Current {data['success_rate']:.1f}% < 95% target")
    else:
        recommendations.append("✅ System meeting Round 2 performance targets!")
        recommendations.append("Consider implementing additional optimizations for edge cases")
    
    return recommendations

@api_bp.route('/streaming/start-90fps', methods=['POST'])
def start_90fps_streaming():
    """Start 90 FPS real-time video streaming analysis (Round 2 requirement)"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'Session ID required'})
        
        # Get session data to find video
        session_data = get_session_data(session_id)
        if not session_data or 'filepath' not in session_data:
            return jsonify({'success': False, 'error': 'No video found for session'})
        
        video_path = session_data['filepath']
        if not os.path.exists(video_path):
            return jsonify({'success': False, 'error': 'Video file not found'})
        
        # Start 90 FPS analysis
        def analysis_callback(result):
            # Could emit via WebSocket for real-time updates
            print(f"📊 90FPS Analysis: Frame {result['frame_id']} at {result['fps']:.1f} FPS")
        
        start_90fps_analysis(video_path, analysis_callback)
        
        return jsonify({
            'success': True,
            'message': '90 FPS real-time analysis started',
            'target_fps': 90,
            'session_id': session_id,
            'round2_compliant': True
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'90 FPS streaming failed: {str(e)}'
        }), 500

@api_bp.route('/streaming/stats')
def get_streaming_stats():
    """Get real-time streaming statistics"""
    try:
        stats = get_realtime_stats()
        
        return jsonify({
            'success': True,
            'streaming_stats': stats,
            'round2_requirements': {
                'target_fps': 90,
                'max_video_duration': '120 minutes',
                'latency_target': '< 1000ms'
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Streaming stats failed: {str(e)}'
        }), 500

@api_bp.route('/streaming/stop', methods=['POST'])
def stop_streaming():
    """Stop real-time streaming analysis"""
    try:
        stop_realtime_analysis()
        
        return jsonify({
            'success': True,
            'message': 'Real-time streaming stopped'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Stop streaming failed: {str(e)}'
        }), 500 