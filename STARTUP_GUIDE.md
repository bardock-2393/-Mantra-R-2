# AI Video Detective Agent - Quick Start Guide

## 🚀 Get Started in 5 Minutes

Transform your video understanding with the most advanced AI agent for comprehensive video analysis.

## 📋 Prerequisites

- **Python 3.8+** installed
- **Google Gemini API Key** (free tier available)
- **Redis Server** (local or cloud)

## ⚡ Quick Setup

### 1. Clone & Install
```bash
git clone <repository-url>
cd ai_video_detective
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your Google Gemini API key
```

### 3. Start Services
```bash
# Start Redis (choose one):
# macOS: brew services start redis
# Ubuntu: sudo systemctl start redis
# Windows: redis-server

# Start the application
python app.py
```

### 4. Access the Agent
Open `http://localhost:5000` in your browser

## 🎯 First Video Analysis

### Step 1: Upload Video
- Drag & drop any video file (MP4, AVI, MOV, WebM, MKV)
- Maximum size: 100MB
- Supported content: Any video type

### Step 2: Configure Analysis
- **Select Analysis Type**: Choose from 5 specialized types
- **Add Custom Focus**: Specify what you want the agent to focus on
- **View Agent Capabilities**: See real-time agent capabilities

### Step 3: Start Analysis
- Click "Start Analysis"
- Watch the agent work autonomously
- Real-time progress updates

### Step 4: Chat with Agent
- Ask any question about the video
- Get comprehensive, evidence-based responses
- Engage in multi-turn conversations

## 🤖 Agent Capabilities

### Autonomous Analysis
- **Self-directed processing**: Agent analyzes video comprehensively
- **Multi-modal understanding**: Visual, audio, temporal, spatial analysis
- **Proactive insights**: Discovers insights beyond explicit requests

### Context-Aware Conversations
- **Memory**: Remembers conversation history
- **Adaptive responses**: Adjusts based on context and user needs
- **Evidence-based**: All claims supported with video evidence

### Professional Analysis Types
1. **Comprehensive Analysis**: Complete multi-dimensional analysis
2. **Safety Investigation**: Advanced safety and risk assessment
3. **Performance Analysis**: Efficiency and quality evaluation
4. **Pattern Detection**: Behavioral and trend analysis
5. **Creative Review**: Artistic and aesthetic assessment

## 💬 Example Conversations

### Safety Analysis
```
You: "What safety violations did you find?"
Agent: "I identified 3 critical safety violations in the video:
1. [Timestamp 0:45] - Worker not wearing required PPE
2. [Timestamp 1:23] - Unsafe equipment operation
3. [Timestamp 2:15] - Blocked emergency exit

Risk Level: HIGH
Immediate Actions Required: [detailed recommendations]"
```

### Performance Analysis
```
You: "How efficient was the workflow?"
Agent: "Based on my analysis, the workflow efficiency is 7.2/10:

Strengths:
- Good time management (85% efficiency)
- Effective tool usage
- Clear process flow

Areas for Improvement:
- [specific recommendations with timestamps]
- [optimization opportunities]"
```

### Pattern Detection
```
You: "What patterns did you notice?"
Agent: "I identified several behavioral patterns:

1. Movement Patterns:
   - [specific patterns with evidence]
2. Interaction Patterns:
   - [communication patterns]
3. Temporal Patterns:
   - [timing and sequence patterns]

These patterns suggest [insights and implications]"
```

## 🔧 Configuration Options

### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key

# Optional
REDIS_URL=redis://localhost:6379
UPLOAD_FOLDER=static/uploads
MAX_FILE_SIZE=104857600  # 100MB
```

### Analysis Settings
- **Temperature**: 0.1-0.4 (creativity vs consistency)
- **Token Limits**: 8K-16K (analysis depth)
- **Response Format**: Structured or conversational

## 🎨 UI Features

### Minimalist Design
- **Black & White**: Professional, distraction-free interface
- **Responsive**: Works on all devices
- **Intuitive**: Simple upload → analyze → chat workflow

### Real-time Feedback
- **Progress Tracking**: Live analysis progress
- **Status Updates**: Agent status and capabilities
- **Error Handling**: Graceful error recovery

## 📊 Analysis Output

### Comprehensive Reports
Each analysis includes:
- **Executive Summary**: High-level findings
- **Detailed Analysis**: 10+ analysis dimensions
- **Actionable Insights**: Practical recommendations
- **Evidence Board**: Key findings summary
- **Risk Assessment**: Safety and performance risks
- **Timeline**: Chronological event sequence

### Evidence-Based Responses
- **Specific Timestamps**: Precise event timing
- **Visual Evidence**: Detailed observations
- **Contextual Information**: Background and setting
- **Comparative Analysis**: Benchmarks and standards

## 🚨 Troubleshooting

### Common Issues

**API Key Issues**
   ```bash
# Verify your API key
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://generativelanguage.googleapis.com/v1beta/models
```

**Redis Connection**
```bash
# Test Redis connection
redis-cli ping
# Should return: PONG
```

**File Upload Issues**
- Check file format (MP4, AVI, MOV, WebM, MKV)
- Verify file size (max 100MB)
- Ensure upload folder permissions

### Debug Mode
```bash
export FLASK_DEBUG=1
python app.py
```

## 🎯 Pro Tips

### Optimal Analysis
1. **Choose Right Type**: Match analysis type to your needs
2. **Add Custom Focus**: Be specific about what you want analyzed
3. **Ask Follow-up Questions**: Use chat to dive deeper
4. **Use Quick Questions**: Try predefined question buttons

### Advanced Usage
- **Batch Analysis**: Upload multiple videos for comparison
- **Export Results**: Save analysis reports for later
- **Share Insights**: Collaborate with team members
- **Custom Prompts**: Modify analysis focus areas

## 📈 Performance Tips

### For Large Videos
- **Compress**: Reduce file size before upload
- **Segment**: Break long videos into parts
- **Focus**: Use custom focus to target specific areas

### For Better Results
- **Clear Content**: Ensure good video quality
- **Specific Questions**: Ask targeted questions
- **Context**: Provide background information in chat

## 🔮 What's Next?

### Try These Workflows
1. **Safety Audit**: Upload workplace videos for safety analysis
2. **Performance Review**: Analyze training or demonstration videos
3. **Pattern Analysis**: Study behavioral patterns in any video
4. **Creative Assessment**: Evaluate marketing or artistic content
5. **Comprehensive Review**: Get complete video understanding

### Advanced Features
- **Batch Processing**: Multiple video analysis
- **Custom Models**: Domain-specific analysis
- **API Integration**: Connect to your systems
- **Export Options**: PDF, CSV, custom formats

## 🆘 Need Help?

### Quick Support
- **Documentation**: Check this guide and README
- **Issues**: Report bugs on GitHub
- **Community**: Join discussions for help

### API Limits
- **Free Tier**: 15 requests/minute
- **Paid Tier**: Higher limits available
- **Optimization**: Efficient analysis reduces API usage

---

**Ready to transform your video understanding?** 🚀

Start with any video and let the AI Video Detective Agent tell you everything about it! 