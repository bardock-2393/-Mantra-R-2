# Gemma 3 Migration Guide

This document outlines the migration from Gemini Live to Gemma 3 open-source model for video analysis.

## What Changed

### 1. Dependencies
- **Removed**: `google-genai` package
- **Added**: 
  - `transformers>=4.50.0`
  - `torch>=2.0.0` 
  - `accelerate>=0.20.0`

### 2. AI Service (`services/ai_service.py`)
- **Model**: Now uses `google/gemma-3-12b-it` instead of Gemini Live
- **Video Processing**: Extracts frames locally using OpenCV instead of uploading to Google
- **Analysis**: Processes video frames directly with Gemma 3 multimodal capabilities
- **Chat**: Uses Gemma 3 for contextual responses instead of Gemini API

### 3. Configuration (`config.py`)
- **Removed**: `GOOGLE_API_KEY` requirement (commented out)
- **Kept**: All other configuration parameters for consistency

## Installation

### 1. Install Dependencies
```bash
python install_gemma3.py
```

### 2. Test Installation
```bash
python test_gemma3.py
```

## Key Features Preserved

- ✅ **Same API**: All function signatures remain unchanged
- ✅ **Enhanced Analysis**: Same comprehensive video analysis capabilities
- ✅ **Chat Functionality**: Contextual AI responses with conversation history
- ✅ **Agentic Behavior**: Proactive insights and comprehensive reporting
- ✅ **Quality Standards**: Precision, timestamps, and structured output

## Benefits of Migration

### 1. **Open Source**
- No API keys required
- No rate limits or usage costs
- Full control over the model

### 2. **Privacy**
- Video data stays local
- No external uploads required
- Complete data sovereignty

### 3. **Performance**
- Direct local processing
- No network latency for API calls
- Consistent availability

### 4. **Customization**
- Can fine-tune model for specific use cases
- Modify inference parameters
- Add custom processing pipelines

## Technical Details

### Model Specifications
- **Model**: Gemma 3 12B Instruction-Tuned
- **Context**: 128K tokens (4B, 12B, 27B) / 32K tokens (1B)
- **Output**: 8192 tokens
- **Multimodal**: Text + Image input, Text output
- **Languages**: 140+ languages supported

### Hardware Requirements
- **Minimum**: 16GB RAM, modern CPU
- **Recommended**: 24GB+ VRAM GPU for optimal performance
- **Storage**: ~25GB for model files (first download)

### Frame Processing
- **Extraction**: 10 frames per video by default
- **Distribution**: Evenly spaced throughout video
- **Format**: 896x896 resolution (Gemma 3 standard)
- **Encoding**: 256 tokens per image

## Usage

The application works exactly the same as before:

1. **Start the server**: `python app.py`
2. **Upload video**: Same web interface
3. **Analyze**: Choose analysis type and focus
4. **Chat**: Ask questions about the video

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Run `python install_gemma3.py`
   - Check Python version (3.8+ required)

2. **Model Download Issues**
   - Ensure stable internet connection
   - Model downloads ~25GB on first run
   - Check available disk space

3. **Memory Issues**
   - Close other applications
   - Use smaller video files for testing
   - Consider CPU-only mode if GPU memory is limited

4. **Performance Issues**
   - Check GPU availability with `torch.cuda.is_available()`
   - Monitor system resources during analysis
   - Reduce number of frames if needed

### Getting Help

1. Run the test script: `python test_gemma3.py`
2. Check console output for detailed error messages
3. Verify all dependencies are installed correctly
4. Ensure video files are in supported formats (mp4, avi, mov, webm, mkv)

## Migration Verification

To verify the migration was successful:

1. ✅ All tests pass in `test_gemma3.py`
2. ✅ Video analysis produces structured output with timestamps
3. ✅ Chat responses are contextual and comprehensive
4. ✅ No API key errors in console
5. ✅ Processing happens locally (no network uploads)

The migration maintains 100% functional compatibility while providing the benefits of open-source, local processing with Gemma 3.