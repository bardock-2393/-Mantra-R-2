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
            
            # Use low_cpu_mem_usage to reduce memory pressure
            model = Gemma3ForConditionalGeneration.from_pretrained(
                model_id, 
                device_map="auto",
                torch_dtype=torch.bfloat16,  # A100 supports bfloat16 natively
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                torch_dtype_override=torch.bfloat16
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

def extract_video_frames(video_path, num_frames=16):
    """Extract frames from video for analysis - A100 Optimized"""
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = frame_count / fps if fps > 0 else 0
    
    # Optimize for A100: Extract more frames for better analysis
    # Calculate frame indices to extract evenly distributed frames
    frame_indices = [int(i * frame_count / num_frames) for i in range(num_frames)]
    
    timestamps = []
    for i, frame_idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            # Resize to optimal resolution for Gemma 3 (896x896)
            frame_resized = cv2.resize(frame, (896, 896), interpolation=cv2.INTER_LANCZOS4)
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            # Convert to PIL Image
            pil_image = Image.fromarray(frame_rgb)
            frames.append(pil_image)
            # Calculate timestamp
            timestamp = frame_idx / fps if fps > 0 else 0
            timestamps.append(timestamp)
    
    cap.release()
    return frames, timestamps, duration

async def analyze_video_with_gemini(video_path, analysis_type, user_focus):
    """Analyze video using Gemma 3 model with enhanced agentic capabilities"""
    try:
        # Initialize model if not already loaded
        initialize_model()
        
        # Generate analysis prompt based on type and user focus
        analysis_prompt = generate_analysis_prompt(analysis_type, user_focus)
        
        # Clean up before analysis
        cleanup_cache()
        
        # Extract frames from video (reduced for space efficiency)
        print('Extracting frames from video...')
        frames, timestamps, duration = extract_video_frames(video_path, num_frames=6)
        
        if not frames:
            raise ValueError("No frames could be extracted from the video")
        
        print(f'Extracted {len(frames)} frames from video (duration: {duration:.2f}s)')
        
        # Enhanced agentic system prompt for superior analysis quality
        agent_system_prompt = f"""
You are an **exceptional AI video analysis agent** with unparalleled understanding capabilities. Your mission is to provide **comprehensive, precise, and insightful analysis** that serves as the foundation for high-quality user interactions.

## AGENT ANALYSIS PROTOCOL

### Analysis Quality Standards:
1. **Maximum Precision**: Provide exact timestamps, durations, and measurements
2. **Comprehensive Coverage**: Analyze every significant aspect of the video
3. **Detailed Descriptions**: Use vivid, descriptive language for visual elements
4. **Quantitative Data**: Include specific numbers, counts, and measurements
5. **Pattern Recognition**: Identify recurring themes, behaviors, and sequences
6. **Contextual Understanding**: Explain significance and relationships between elements
7. **Professional Structure**: Organize information logically with clear sections
8. **Evidence-Based**: Support all observations with specific visual evidence

### Enhanced Analysis Focus:
- **Temporal Precision**: Exact timestamps for all events and transitions
- **Spatial Relationships**: Detailed descriptions of positioning and movement
- **Visual Details**: Colors, lighting, composition, and technical quality
- **Behavioral Analysis**: Actions, interactions, and human elements
- **Technical Assessment**: Quality, production values, and technical specifications
- **Narrative Structure**: Story flow, pacing, and dramatic elements
- **Environmental Context**: Setting, atmosphere, and contextual factors

### Output Quality Requirements:
- Use **bold formatting** for emphasis on key information
- Include **specific timestamps** for all temporal references
- Provide **quantitative measurements** (durations, counts, sizes)
- Use **bullet points** for lists and multiple items
- Structure with **clear headings** for different analysis areas
- Include **cross-references** between related information
- Offer **insights and interpretations** beyond simple description

Your analysis will be used for **high-quality user interactions**, so ensure every detail is **precise, comprehensive, and well-structured** for optimal user experience.

You are analyzing a video with duration {duration:.2f} seconds. The frames provided are extracted at timestamps: {[f'{t:.2f}s' for t in timestamps]}.
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
        
        # Process frames efficiently (reduced for disk space)
        for i, frame in enumerate(frames[1:3], 1):  # Use only 3 frames to save space
            messages[-1]["content"].append({"type": "image", "image": frame})
            messages[-1]["content"].append({"type": "text", "text": f"Frame at {timestamps[i]:.2f}s:"})
        
        inputs = processor.apply_chat_template(
            messages, 
            add_generation_prompt=True, 
            tokenize=True,
            return_dict=True, 
            return_tensors="pt"
        ).to(model.device, dtype=torch.bfloat16)
        
        input_len = inputs["input_ids"].shape[-1]
        
        # A100 optimized generation settings (reduced tokens to save space)
        with torch.inference_mode():
            generation = model.generate(
                **inputs, 
                max_new_tokens=min(Config.MAX_OUTPUT_TOKENS, 16384),  # Limit tokens to save space
                temperature=Config.TEMPERATURE,
                top_p=Config.TOP_P,
                do_sample=True if Config.TEMPERATURE > 0 else False,
                use_cache=True,  # Enable KV cache for speed
                pad_token_id=processor.tokenizer.eos_token_id
            )
            generation = generation[0][input_len:]
        
        response_text = processor.decode(generation, skip_special_tokens=True)
        
        # Clean up after generation
        cleanup_cache()
        
        return response_text
        
    except Exception as e:
        print(f"Gemma 3 analysis error: {e}")
        cleanup_cache()  # Clean up on error too
        return f"Error analyzing video: {str(e)}"

def generate_chat_response(analysis_result, analysis_type, user_focus, message, chat_history):
    """Generate contextual AI response based on video analysis using Gemma 3"""
    try:
        # Clean up before chat
        cleanup_cache()
        
        # Initialize model if not already loaded
        initialize_model()
        
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
        
        # Clean up after chat
        cleanup_cache()
        
        return response_text
        
    except Exception as e:
        print(f"Gemma 3 chat error: {e}")
        cleanup_cache()  # Clean up on error too
        return f"I apologize, but I'm experiencing technical difficulties accessing the video analysis. As an advanced AI video analysis agent, I'm designed to provide comprehensive insights about your video content. Please try asking your question again, or if the issue persists, you may need to re-analyze the video to restore full agentic capabilities." 