"""
AI Service Module
Handles Gemma 3 model interactions and analysis functionality
"""

import asyncio
import torch
from transformers import AutoProcessor, Gemma3ForConditionalGeneration, pipeline
from PIL import Image
import cv2
import os
import tempfile
import shutil
from config import Config
from analysis_templates import generate_analysis_prompt

# Import WebSocket service for real-time updates (avoiding circular import)
def get_websocket_service():
    """Get WebSocket service with delayed import to avoid circular dependency"""
    try:
        from services.websocket_service import get_websocket_service
        return get_websocket_service()
    except ImportError:
        return None

# Disable compilation to save disk space
os.environ['TORCHDYNAMO_DISABLE'] = '1'
os.environ['TORCH_COMPILE_DISABLE'] = '1'

# Initialize Gemma 3 model - Optimized for A100 80GB with space constraints
model_id = "google/gemma-3-12b-it"  # Use 12B to avoid disk space issues
device = "cuda" if torch.cuda.is_available() else "cpu"

# Global variables for model and processor (lazy loading)
model = None
processor = None

def cleanup_cache():
    """Clean up cache and temporary files to free disk space"""
    try:
        # Clean up /tmp directory
        for item in os.listdir('/tmp'):
            if item.startswith('torch') or item.startswith('torchinductor'):
                try:
                    path = os.path.join('/tmp', item)
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                except:
                    pass
        print("✅ Cleaned up temporary files")
    except Exception as e:
        print(f"Cache cleanup warning: {e}")

def initialize_model():
    """Initialize Gemma 3 model and processor - A100 Optimized with space management"""
    global model, processor
    if model is None:
        print("Loading Gemma 3 12B model for A100...")
        
        # Clean up cache first
        cleanup_cache()
        
        try:
            # A100 optimized settings without compilation
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.set_float32_matmul_precision('high')
            # Maximum A100 speed optimizations
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False
            
            # Use low_cpu_mem_usage to reduce memory pressure
            model = Gemma3ForConditionalGeneration.from_pretrained(
                model_id, 
                device_map="auto",
                torch_dtype=torch.bfloat16,  # A100 supports bfloat16 natively
                trust_remote_code=True,
                low_cpu_mem_usage=True
            ).eval()
            
            processor = AutoProcessor.from_pretrained(model_id)
            
            # Skip compilation to save disk space
            print("✅ Gemma 3 12B model loaded successfully on A100 (compilation disabled)")
            if torch.cuda.is_available():
                print(f"📊 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
                print(f"📊 GPU Memory Allocated: {torch.cuda.memory_allocated() / 1e9:.1f}GB")
            
        except Exception as e:
            print(f"Error loading Gemma 3 12B model: {e}")
            raise e

def extract_video_frames(video_path, num_frames=None):
    """Extract frames from video for analysis - A100 Optimized with Smart Sampling for Long Videos"""
    import random
    
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = frame_count / fps if fps > 0 else 0
    
    # Auto-determine frame count based on video length
    if num_frames is None:
        if duration >= Config.LONG_VIDEO_THRESHOLD:  # 1+ hour videos
            num_frames = Config.MAX_FRAMES_LONG_VIDEO
            print(f"🎬 Long video detected ({duration/60:.1f} minutes) - using smart sampling with {num_frames} frames")
        else:
            num_frames = Config.MAX_FRAMES_SHORT_VIDEO
            print(f"🎬 Short video ({duration/60:.1f} minutes) - using regular sampling with {num_frames} frames")
    
    # Smart sampling strategy for different video lengths
    if duration >= Config.LONG_VIDEO_THRESHOLD:  # Long videos (1+ hours)
        # Strategic frame selection for long videos
        key_points = [
            0,  # Start
            frame_count // 6,  # ~17%
            frame_count // 3,  # ~33%
            frame_count // 2,  # 50% (middle)
            2 * frame_count // 3,  # ~67%
            5 * frame_count // 6,  # ~83%
            frame_count - 1  # End
        ]
        
        # Add random samples from different segments for variety
        if num_frames > len(key_points):
            segment_size = frame_count // num_frames
            for i in range(len(key_points), num_frames):
                random_frame = i * segment_size + random.randint(0, min(segment_size//2, frame_count//20))
                key_points.append(min(random_frame, frame_count-1))
        
        frame_indices = sorted(list(set(key_points)))[:num_frames]
        print(f"📊 Smart sampling: {len(frame_indices)} strategic frames from {frame_count} total frames")
    else:
        # Regular distributed sampling for shorter videos
        frame_indices = [int(i * frame_count / num_frames) for i in range(num_frames)]
        print(f"📊 Regular sampling: {len(frame_indices)} evenly distributed frames")
    
    timestamps = []
    for i, frame_idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            # Optimized resize for A100 - use faster interpolation for long videos
            interpolation = cv2.INTER_NEAREST if duration >= Config.LONG_VIDEO_THRESHOLD else cv2.INTER_LANCZOS4
            frame_resized = cv2.resize(frame, (896, 896), interpolation=interpolation)
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            # Convert to PIL Image
            pil_image = Image.fromarray(frame_rgb)
            frames.append(pil_image)
            # Calculate timestamp
            timestamp = frame_idx / fps if fps > 0 else 0
            timestamps.append(timestamp)
    
    cap.release()
    
    # Memory optimization for long videos
    if duration >= Config.LONG_VIDEO_THRESHOLD:
        torch.cuda.empty_cache()  # Clear GPU memory after processing
    
    return frames, timestamps, duration

async def analyze_video_with_gemini(video_path, analysis_type, user_focus, session_id=None):
    """Analyze video using Gemma 3 model with real-time WebSocket updates"""
    import time
    start_time = time.time()
    print(f"🎬 Starting video analysis at {time.strftime('%H:%M:%S')}")
    
    # Get WebSocket service for real-time updates
    ws_service = get_websocket_service()
    
    try:
        # Generate analysis prompt based on type and user focus
        analysis_prompt = generate_analysis_prompt(analysis_type, user_focus)
        
        # Emit progress: Starting analysis
        if ws_service and session_id:
            ws_service.emit_progress(session_id, 'initialization', 10, '🚀 Starting video analysis...')
        
        # Clean up before analysis
        cleanup_cache()
        
        # Extract frames from video with smart sampling
        frame_start = time.time()
        print('🎬 Extracting frames from video...')
        
        if ws_service and session_id:
            ws_service.emit_progress(session_id, 'frame_extraction', 25, '🎬 Extracting frames from video...')
        
        frames, timestamps, duration = extract_video_frames(video_path)  # Auto-detects long videos
        frame_time = time.time() - frame_start
        
        if not frames:
            raise ValueError("No frames could be extracted from the video")
        
        print(f'✅ Extracted {len(frames)} frames in {frame_time:.2f}s (video duration: {duration:.2f}s)')
        
        # Emit progress: Frames extracted
        if ws_service and session_id:
            ws_service.emit_progress(session_id, 'frame_extraction', 50, f'✅ Extracted {len(frames)} frames ({duration/60:.1f} min video)')
        
        # Adaptive system prompt based on video length
        is_long_video = duration >= Config.LONG_VIDEO_THRESHOLD
        
        # Notify about long video detection
        if ws_service and session_id and is_long_video:
            ws_service.emit_long_video_detected(session_id, duration/60)
        video_type = "long-form" if is_long_video else "short-form"
        
        if is_long_video:
            # Condensed prompt for long videos (faster processing)
            agent_system_prompt = f"""
You are an **AI video analysis agent** optimized for {video_type} content analysis. Provide **concise, precise analysis** focusing on key elements.

## ANALYSIS PROTOCOL FOR LONG VIDEOS ({duration/60:.1f} minutes)

### Key Requirements:
- **Concise Summaries**: Focus on major themes and key moments
- **Strategic Timestamps**: Highlight critical transitions and events
- **Pattern Recognition**: Identify recurring elements across the video
- **Efficient Structure**: Use clear headings and bullet points

### Analysis Focus:
- **Major Events**: Key moments and transitions
- **Visual Themes**: Consistent elements throughout
- **Technical Quality**: Overall production assessment
- **Narrative Flow**: Story progression and pacing

**Video Duration**: {duration:.1f}s ({duration/60:.1f} minutes)
**Frames Analyzed**: {len(frames)} strategic samples at: {[f'{t:.1f}s' for t in timestamps]}

Provide **concise, actionable insights** suitable for real-time analysis.
"""
        else:
            # Detailed prompt for shorter videos
            agent_system_prompt = f"""
You are an **exceptional AI video analysis agent** providing **comprehensive analysis** for {video_type} content.

## DETAILED ANALYSIS PROTOCOL

### Analysis Standards:
- **Maximum Precision**: Exact timestamps and measurements
- **Comprehensive Coverage**: Analyze all significant aspects
- **Detailed Descriptions**: Vivid, descriptive language
- **Evidence-Based**: Support observations with visual evidence

### Focus Areas:
- **Temporal Precision**: Exact timestamps for events
- **Visual Details**: Colors, lighting, composition
- **Behavioral Analysis**: Actions and interactions
- **Technical Assessment**: Quality and production values

**Video Duration**: {duration:.1f}s
**Frames Analyzed**: {len(frames)} at timestamps: {[f'{t:.1f}s' for t in timestamps]}

Provide **detailed, comprehensive analysis** for optimal user experience.
"""
        
        # Analyze the first frame to get initial insights, then analyze sequence
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": agent_system_prompt}]
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": frames[0]},
                    {"type": "text", "text": f"Analyze this video sequence. {analysis_prompt}"}
                ]
            }
        ]
        
        # Adaptive frame processing based on video length
        if is_long_video:
            # For long videos: Use more frames but process efficiently 
            max_additional_frames = min(len(frames) - 1, 3)  # Up to 3 additional frames
            frame_step = max(1, (len(frames) - 1) // max_additional_frames) if max_additional_frames > 0 else 1
            selected_frames = frames[1::frame_step][:max_additional_frames]
            selected_timestamps = timestamps[1::frame_step][:max_additional_frames]
            
            for i, (frame, timestamp) in enumerate(zip(selected_frames, selected_timestamps), 1):
                messages[-1]["content"].append({"type": "image", "image": frame})
                messages[-1]["content"].append({"type": "text", "text": f"Key frame at {timestamp:.1f}s:"})
            
            print(f"📊 Processing {len(selected_frames)} key frames for long video analysis")
        else:
            # For short videos: Use minimal frames for speed
            for i, frame in enumerate(frames[1:1], 1):  # Use 0 additional frames for max speed
                messages[-1]["content"].append({"type": "image", "image": frame})
                messages[-1]["content"].append({"type": "text", "text": f"Frame at {timestamps[i]:.2f}s:"})
            
            print(f"📊 Processing {len(frames[1:1])} additional frames for short video analysis")
        
        inputs = processor.apply_chat_template(
            messages, 
            add_generation_prompt=True, 
            tokenize=True,
            return_dict=True, 
            return_tensors="pt"
        ).to(model.device, dtype=torch.bfloat16)
        
        input_len = inputs["input_ids"].shape[-1]
        
        # Emit progress: AI thinking
        if ws_service and session_id:
            ws_service.emit_ai_thinking(session_id, 'ai_inference')
            ws_service.emit_progress(session_id, 'ai_inference', 75, '🧠 Gemma 3 AI analyzing video content...')
        
        # A100 optimized generation settings (reduced tokens to save space)
        inference_start = time.time()
        print('🧠 Starting AI inference...')
        with torch.inference_mode():
            generation = model.generate(
                **inputs, 
                max_new_tokens=Config.MAX_OUTPUT_TOKENS,  # Use direct config value for speed
                temperature=Config.TEMPERATURE,
                top_p=Config.TOP_P,
                do_sample=True if Config.TEMPERATURE > 0 else False,
                use_cache=True,  # Enable KV cache for speed
                pad_token_id=processor.tokenizer.eos_token_id
            )
            generation = generation[0][input_len:]
        
        inference_time = time.time() - inference_start
        print(f'✅ AI inference completed in {inference_time:.2f}s')
        
        response_text = processor.decode(generation, skip_special_tokens=True)
        
        # Calculate total time and add timing info to response
        total_time = time.time() - start_time
        print(f'🏁 Total analysis completed in {total_time:.2f}s')
        
        # Add enhanced timing information for long videos
        video_info = f"({duration/60:.1f} min, {len(frames)} frames)" if is_long_video else f"({duration:.1f}s, {len(frames)} frames)"
        timing_info = f"""

---
⏱️ **Performance Report:**
- **Video**: {video_info}
- **Frame Extraction**: {frame_time:.2f}s
- **AI Inference**: {inference_time:.2f}s  
- **Total Time**: {total_time:.2f}s
- **Speed**: {len(frames)/total_time:.1f} frames/sec
- **Mode**: {'Long Video (Smart Sampling)' if is_long_video else 'Short Video (Full Analysis)'} 
- **GPU**: A100 Optimized ⚡
"""
        
        # Emit completion with results
        if ws_service and session_id:
            timing_info_dict = {
                'frame_time': frame_time,
                'inference_time': inference_time,
                'total_time': total_time,
                'speed': len(frames)/total_time,
                'mode': 'Long Video (Smart Sampling)' if is_long_video else 'Short Video (Full Analysis)'
            }
            ws_service.emit_analysis_complete(session_id, response_text + timing_info, timing_info_dict)
            ws_service.emit_progress(session_id, 'complete', 100, f'✅ Analysis complete in {total_time:.2f}s!')
        
        # Enhanced cleanup for long videos
        cleanup_cache()
        if is_long_video:
            torch.cuda.empty_cache()  # Additional GPU memory cleanup for long videos
            torch.cuda.synchronize()  # Ensure all GPU operations complete
        
        return response_text + timing_info
        
    except Exception as e:
        print(f"Gemma 3 analysis error: {e}")
        if ws_service and session_id:
            ws_service.emit_error(session_id, str(e), 'analysis')
        cleanup_cache()  # Clean up on error too
        return f"Error analyzing video: {str(e)}"

def generate_chat_response(analysis_result, analysis_type, user_focus, message, chat_history, session_id=None):
    """Generate contextual AI response with real-time WebSocket updates"""
    import time
    start_time = time.time()
    print(f"💬 Starting chat response at {time.strftime('%H:%M:%S')}")
    
    # Get WebSocket service for real-time updates
    ws_service = get_websocket_service()
    
    try:
        # Clean up before chat
        cleanup_cache()
        
        # Enhanced agentic conversation prompt with advanced capabilities
        context_prompt = f"""
You are an advanced AI video analysis agent with comprehensive understanding capabilities. You are engaging in a multi-turn conversation about a video that has been analyzed.

## AGENT CONVERSATION PROTOCOL

### Current Context:
- Analysis Type: {analysis_type.replace('_', ' ').title()}
- Original Analysis Focus: {user_focus}
- User Question: "{message}"
- Conversation History: Available for context awareness

### Video Analysis Context:
            {analysis_result}
            
### Agent Capabilities:
- Autonomous Analysis: Provide comprehensive insights beyond the immediate question
- Multi-Modal Understanding: Reference visual, audio, temporal, and spatial elements
- Context Awareness: Adapt responses based on conversation history and user intent
- Proactive Insights: Offer additional relevant information and observations
- Comprehensive Reporting: Provide detailed, structured responses
- Adaptive Focus: Adjust response depth based on question complexity

### Response Quality Standards:
1. **Precision & Accuracy**: Provide exact, verifiable information with specific timestamps
2. **Comprehensive Coverage**: Address all aspects of the question thoroughly
3. **Evidence-Based**: Support every claim with specific evidence from the analysis
4. **Clear Structure**: Use logical organization with clear headings and bullet points
5. **Professional Tone**: Maintain engaging yet professional communication
6. **Proactive Insights**: Offer additional relevant observations beyond the direct question
7. **Visual Clarity**: Use formatting to enhance readability (bold, italics, lists)
8. **Contextual Awareness**: Reference previous conversation context when relevant

### Response Format Guidelines:
- **Start with a direct answer** to the user's question
- **Use clear headings** for different sections (e.g., "**Key Findings:**", "**Timeline:**", "**Additional Insights:**")
- **Include specific timestamps** when discussing events (e.g., "At **00:15-00:17**")
- **Use bullet points** for lists and multiple items
- **Bold important information** for emphasis
- **Provide quantitative data** when available (durations, counts, measurements)
- **Include relevant context** that enhances understanding
- **End with actionable insights** or additional observations when relevant

### Specialized Response Areas:
- **Safety Analysis**: Focus on specific safety concerns, violations, and recommendations
- **Timeline Events**: Provide chronological details with precise timestamps
- **Pattern Recognition**: Highlight recurring behaviors, trends, and anomalies
- **Performance Assessment**: Discuss quality, efficiency, and optimization opportunities
- **Creative Elements**: Analyze artistic, aesthetic, and creative aspects
- **Technical Details**: Provide technical specifications and quality assessments
- **Behavioral Insights**: Analyze human behavior, interactions, and social dynamics
- **Environmental Factors**: Consider context, setting, and environmental conditions

### Quality Enhancement Techniques:
- **Quantify responses**: Use specific numbers, durations, and measurements
- **Cross-reference information**: Connect related details across different sections
- **Provide context**: Explain why certain details are significant
- **Use descriptive language**: Make responses vivid and engaging
- **Structure complex information**: Break down complex topics into digestible sections
- **Highlight patterns**: Identify and explain recurring themes or behaviors
- **Offer insights**: Provide analysis beyond simple description

Your mission is to provide **exceptional quality responses** that demonstrate deep understanding of the video content, offer precise information with timestamps, and deliver insights that exceed user expectations. Every response should be comprehensive, well-structured, and highly informative.
"""
        
        # Include conversation history for context awareness
        conversation_context = ""
        if len(chat_history) > 2:  # More than just current message
            recent_messages = chat_history[-6:]  # Last 6 messages for context
            conversation_context = "\n\n### Recent Conversation Context:\n"
            for msg in recent_messages:
                if 'user' in msg:
                    conversation_context += f"User: {msg['user']}\n"
                elif 'ai' in msg:
                    conversation_context += f"Agent: {msg['ai'][:200]}...\n"  # Truncate for context
        
        enhanced_context_prompt = context_prompt + conversation_context
        
        # Create messages for Gemma 3
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": enhanced_context_prompt}]
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": message}]
            }
        ]
        
        inputs = processor.apply_chat_template(
            messages, 
            add_generation_prompt=True, 
            tokenize=True,
            return_dict=True, 
            return_tensors="pt"
        ).to(model.device)
        
        input_len = inputs["input_ids"].shape[-1]
        
        with torch.inference_mode():
            generation = model.generate(
                **inputs, 
                max_new_tokens=Config.CHAT_MAX_TOKENS,
                temperature=Config.CHAT_TEMPERATURE,
                top_p=Config.TOP_P,
                do_sample=True if Config.CHAT_TEMPERATURE > 0 else False
            )
            generation = generation[0][input_len:]
        
        response_text = processor.decode(generation, skip_special_tokens=True)
        
        # Calculate chat response time and add to response
        chat_time = time.time() - start_time
        print(f'💬 Chat response completed in {chat_time:.2f}s')
        
        # Add timing info for chat responses
        timing_info = f"\n\n⚡ *Response generated in {chat_time:.2f}s*"
        
        # Clean up after chat
        cleanup_cache()
        
        return response_text + timing_info
        
    except Exception as e:
        print(f"Gemma 3 chat error: {e}")
        cleanup_cache()  # Clean up on error too
        return f"I apologize, but I'm experiencing technical difficulties accessing the video analysis. As an advanced AI video analysis agent, I'm designed to provide comprehensive insights about your video content. Please try asking your question again, or if the issue persists, you may need to re-analyze the video to restore full agentic capabilities." 