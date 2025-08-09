# 🕵️ Visual Understanding Chat Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![Gemini AI](https://img.shields.io/badge/Gemini%20AI-API-orange.svg)](https://aistudio.google.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-red.svg)](https://redis.io/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-purple.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Advanced Visual Understanding Chat Assistant** - An agentic AI system that processes video input, recognizes events, summarizes content, and engages in multi-turn conversations with context-aware understanding.

## 🚀 Live Demo & Video

### **🌐 Live Application**
Experience the Visual Understanding Chat Assistant in action:
**[🔗 Try it now: mantra-r-1.deepsantoshwar.xyz/](https://mantra-r-1.deepsantoshwar.xyz/)**

### **📺 Demo Video**
Watch our comprehensive demo showcasing the system capabilities:

[![Demo Video](https://img.shields.io/badge/YouTube-Watch%20Demo-red?style=for-the-badge&logo=youtube)](https://youtu.be/LNLOXMHwRxE)

**Click the button above to watch the full demo video on YouTube**

## 📋 Table of Contents

- [🎯 Project Overview](#-project-overview)
- [🏗️ Architecture](#️-architecture)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [💻 Usage](#-usage)
- [🎬 Demo](#-demo)
- [🔧 Configuration](#-configuration)
- [🧪 Testing](#-testing)
- [🤝 Contributing](#-contributing)

## 🎯 Project Overview

### **Problem Statement**
Develop an agentic chat assistant for visual understanding that can process video input, recognize events, summarize content, and engage in multi-turn conversations. The system focuses on building a functional prototype that demonstrates core features without strict performance constraints.

### **Core Features Implemented**

#### **1. Video Event Recognition & Summarization**
- **Video Stream Processing**: Accepts video input with maximum 2-minute duration
- **Event Identification**: Recognizes specific events within video content
- **Guideline Adherence Analysis**: Detects violations and compliance issues
- **Intelligent Summarization**: Highlights key events with timestamps

**Example Scenario**: Traffic scene analysis
- Identifies vehicle movements, pedestrian crossings, traffic light changes
- Summarizes violations: "Vehicle X ran a red light at timestamp Y"
- Reports compliance issues: "Pedestrian crossed against signal at timestamp Z"

#### **2. Multi-Turn Conversations**
- **Context Retention**: Maintains conversation history across interactions
- **Agentic Workflow**: Self-directed analysis and response generation
- **Clarifying Questions**: Supports follow-up inquiries about events/summaries
- **Coherent Responses**: Provides contextually relevant information

#### **3. Video Input Processing**
- **Format Support**: MP4, AVI, MOV, WMV, FLV
- **Duration Limit**: Maximum 2-minute video processing
- **Real-time Processing**: Stream-based video analysis
- **Evidence Generation**: Automatic screenshots and video clips

### **Innovation Highlights**
- **Agentic Architecture**: Autonomous decision-making and analysis
- **Multi-Modal Understanding**: Visual, temporal, and contextual comprehension
- **Proactive Insights**: Beyond-request information and observations
- **Adaptive Focus**: Dynamic response depth based on content complexity

## 🏗️ Architecture

### **System Architecture Diagram**

<img width="1765" height="710" alt="image" src="https://github.com/user-attachments/assets/889cc49f-86e4-41f8-9c12-a7a30995aba6" />


### **Component Interactions**

#### **1. Frontend Layer**
- **Responsive UI**: Modern web interface with real-time chat
- **Video Upload**: Drag-and-drop or file selection
- **Chat Interface**: Multi-turn conversation support
- **Evidence Display**: Screenshots and video clips presentation

#### **2. Backend Layer**
- **Flask Application**: RESTful API and web server
- **Session Management**: Redis-backed conversation persistence
- **File Processing**: Video upload and storage management
- **Route Handling**: API endpoints and request processing

#### **3. AI Layer**
- **Gemini AI Integration**: Advanced video understanding
- **Event Recognition**: Automated event detection and classification
- **Context Management**: Conversation history and context retention
- **Response Generation**: Intelligent, contextual responses

#### **4. Video Processing Pipeline**
- **OpenCV Processing**: Video frame extraction and analysis
- **Metadata Extraction**: Technical video information
- **Evidence Generation**: Automatic screenshot and clip creation
- **Quality Assessment**: Video quality and format validation

## 🛠️ Tech Stack

### **Backend Technology Justification**

#### **Flask Framework**
- **Rationale**: Lightweight, flexible Python web framework
- **AI/ML Suitability**: Excellent integration with Python ML libraries
- **Scalability**: Modular architecture supports horizontal scaling
- **Development Speed**: Rapid prototyping and development
- **Community Support**: Extensive documentation and community

#### **Redis Cache**
- **Rationale**: High-performance in-memory data store
- **Session Management**: Fast conversation history storage
- **Scalability**: Horizontal scaling with clustering
- **Persistence**: Optional disk persistence for data durability
- **Real-time**: Sub-millisecond response times

#### **OpenCV**
- **Rationale**: Industry-standard computer vision library
- **Video Processing**: Efficient frame extraction and manipulation
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Performance**: Optimized C++ backend with Python bindings
- **Rich Ecosystem**: Extensive documentation and examples

### **AI Model Selection**

#### **Google Gemini AI**
- **Rationale**: State-of-the-art multimodal AI model
- **Video Understanding**: Advanced video content comprehension
- **Conversational AI**: Natural language processing capabilities
- **Context Awareness**: Long-context window for multi-turn conversations
- **API Integration**: Easy-to-use REST API with Python SDK

### **Additional Technologies**

#### **Python 3.8+**
- **Rationale**: Primary language for AI/ML development
- **Library Ecosystem**: Rich ecosystem of AI/ML libraries
- **Community**: Large, active developer community
- **Performance**: Optimized for numerical computing

#### **Werkzeug**
- **Rationale**: WSGI utility library for Flask
- **File Handling**: Secure file upload processing
- **Security**: Built-in security features for web applications

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8 or higher
- Redis server
- Google Gemini API key
- 2GB+ RAM
- Stable internet connection

### **1. Clone Repository**
```bash
git clone https://github.com/MantraHackathon/visual-understanding-chat-assistant.git
cd visual-understanding-chat-assistant
```

### **2. Setup Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **3. Configure API Keys**
   ```bash
# Create environment file
   cp .env.example .env

# Edit with your API key
nano .env
```

Add your Gemini API key:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here
```

### **4. Start Services**
```bash
# Start Redis (if not running)
redis-server

# Run the application
python main.py
```

### **5. Access Application**
Open your browser and visit: `http://localhost:5000`

## 📦 Installation

### **Detailed Setup Instructions**

#### **System Requirements**
- **Operating System**: Windows 10+, macOS 10.14+, or Ubuntu 18.04+
- **Python**: 3.8 or higher
- **Memory**: 2GB+ RAM (4GB+ recommended)
- **Storage**: 1GB+ free space
- **Network**: Stable internet connection for API calls

#### **Dependencies Installation**

```bash
# Core Python packages
pip install -r requirements.txt

# Verify installation
python -c "
import flask, redis, google.generativeai, cv2
print('✅ All dependencies installed successfully!')
"
```

#### **Redis Setup**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Windows:**
```bash
# Download from https://redis.io/download
# Or use WSL2 with Ubuntu
```

#### **Environment Configuration**

```bash
# Create environment file
cat > .env << EOF
GOOGLE_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here
REDIS_URL=redis://localhost:6379
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=104857600
EOF
```

#### **Get Gemini API Key**

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Add it to your `.env` file

## 💻 Usage

### **Basic Usage**

#### **1. Upload Video**
- Click "Choose Video File" or drag-and-drop a video
- Supported formats: MP4, AVI, MOV, WMV, FLV
- Maximum duration: 2 minutes
- Maximum size: 100MB

#### **2. Start Analysis**
- Select analysis type (Comprehensive, Safety, Performance, etc.)
- Add focus area or specific questions
- Click "Upload & Analyze"

#### **3. Chat with AI**
- Ask questions about the video content
- Request clarification on events
- Inquire about specific timestamps
- Get detailed explanations

### **Conversation Examples**

#### **Traffic Scene Analysis**
```
User: "What traffic violations do you see in this video?"

AI: "I've identified several traffic violations in the video:

1. **Red Light Violation** (00:15): A blue sedan ran through a red traffic light at the intersection
2. **Speeding Vehicle** (00:32): A motorcycle exceeded the speed limit in a school zone
3. **Illegal Parking** (00:45): A delivery truck parked in a no-parking zone

The video shows a busy intersection with multiple safety concerns..."

User: "Can you tell me more about the red light violation?"

AI: "Certainly! The red light violation occurred at timestamp 00:15:

- **Vehicle**: Blue sedan (Toyota Camry, 2019-2021 model)
- **Location**: Main Street and Oak Avenue intersection
- **Violation**: Entered intersection 2.3 seconds after light turned red
- **Severity**: High - could have caused a collision
- **Context**: Heavy traffic conditions, school zone nearby

This violation is particularly concerning because..."
```

#### **Workplace Safety Analysis**
```
User: "Analyze this workplace video for safety concerns."

AI: "I've conducted a comprehensive safety analysis of the workplace video:

**Critical Safety Violations:**
1. **Missing PPE** (00:08): Worker operating machinery without safety goggles
2. **Improper Lifting** (00:23): Employee lifting heavy object with incorrect posture
3. **Blocked Emergency Exit** (00:41): Emergency exit partially blocked by equipment

**Safety Recommendations:**
- Immediate: Provide safety goggles to all workers
- Short-term: Conduct proper lifting technique training
- Long-term: Implement regular safety audits..."

User: "What specific training should be provided?"

AI: "Based on the safety violations observed, I recommend the following training programs:

1. **PPE Training** (Immediate Priority):
   - Proper selection and use of safety equipment
   - Maintenance and inspection procedures
   - Enforcement protocols

2. **Ergonomics Training** (High Priority):
   - Proper lifting techniques
   - Body mechanics and posture
   - Injury prevention strategies..."
```

### **Advanced Features**

#### **Multi-Turn Context Retention**
The system maintains conversation context across multiple interactions:

```
User: "What happened at 1:30 in the video?"
AI: "At 1:30, I observed a pedestrian crossing the street..."

User: "Was that person following the rules?"
AI: "No, the pedestrian was not following the rules. At 1:30, they crossed against the 'Don't Walk' signal..."

User: "What should they have done instead?"
AI: "The pedestrian should have waited for the 'Walk' signal before crossing. The proper procedure would be..."
```

#### **Proactive Insights**
The AI provides additional relevant information:

```
User: "Analyze this video for performance issues."

AI: "I've identified several performance concerns:

**Immediate Issues:**
- Inefficient workflow at 00:15
- Equipment downtime at 00:32

**Proactive Observations:**
- The current process could be optimized by 40% with better equipment placement
- There's potential for automation in the repetitive tasks at 00:45
- Team communication could be improved with visual signals..."
```

## 🎬 Demo

### **Demo Video Features**
Our demo video showcases:

1. **Video Upload Process**
   - Drag-and-drop functionality
   - File validation and processing
   - Progress indicators

2. **Event Recognition**
   - Real-time event detection
   - Timestamp marking
   - Violation identification

3. **Multi-Turn Conversations**
   - Context retention
   - Follow-up questions
   - Detailed explanations

4. **Evidence Generation**
   - Automatic screenshots
   - Video clip extraction
   - Evidence organization

### **Demo Scenarios**
- **Traffic Analysis**: Identifying violations and safety concerns
- **Workplace Safety**: Detecting safety violations and recommendations
- **Performance Review**: Analyzing efficiency and improvement opportunities
- **Creative Content**: Evaluating artistic and technical quality

## 🔧 Configuration

### **Environment Variables**

```env
# Required
GOOGLE_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here

# Optional (with defaults)
REDIS_URL=redis://localhost:6379
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=104857600
SESSION_EXPIRY=3600
CLEANUP_INTERVAL=1800
```

### **Application Settings**

```python
# config.py
class Config:
    # File upload settings
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv'}
    
    # Session settings
    SESSION_EXPIRY = 3600  # 1 hour
    CLEANUP_INTERVAL = 1800  # 30 minutes
    
    # AI settings
    AI_TEMPERATURE = 0.7
    AI_MAX_TOKENS = 4000
```

## 🧪 Testing

### **Setup Testing**
```bash
# Run comprehensive setup test
python test_setup.py
```

### **Manual Testing**
```bash
# Test video upload
curl -X POST http://localhost:5000/upload \
  -F "video=@test_video.mp4"

# Test analysis
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"analysis_type": "comprehensive", "user_focus": "safety concerns"}'

# Test chat
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What events did you detect in the video?"}'
```

### **API Testing**
```bash
# Health check
curl http://localhost:5000/health

# Get analysis types
curl http://localhost:5000/api/analysis-types

# Get session status
curl http://localhost:5000/session/status
```

## 🔍 Troubleshooting

### **Common Issues**

#### **1. Redis Connection Error**
```bash
# Error: Redis connection failed
# Solution: Start Redis server
redis-server

# Check Redis status
redis-cli ping
# Should return: PONG
```

#### **2. Gemini API Errors**
```bash
# Error: Invalid API key
# Solution: Verify your API key
echo $GOOGLE_API_KEY

# Check API quota
# Visit: https://aistudio.google.com/app/apikey
```

#### **3. Video Upload Issues**
```bash
# Error: File too large
# Check file size limit in config.py
# Default: 100MB

# Error: Unsupported format
# Supported: MP4, AVI, MOV, WMV, FLV
```

#### **4. Session Issues**
```bash
# Clear browser cache and cookies
# Restart the application
python main.py

# Check Redis connection
redis-cli keys "*"
```

### **Debug Mode**
```python
# Enable debug mode for detailed errors
app.run(debug=True, host='0.0.0.0', port=5000)
```

## 🤝 Contributing

### **Development Setup**
```bash
# Fork and clone the repository
git clone https://github.com/MantraHackathon/visual-understanding-chat-assistant.git
cd visual-understanding-chat-assistant

# Create feature branch
git checkout -b feature/amazing-feature

# Make your changes
# Add tests if applicable

# Commit and push
git commit -m "Add amazing feature"
git push origin feature/amazing-feature

# Create pull request
```

### **Code Style**
- Follow PEP 8 Python style guide
- Add docstrings to functions
- Include type hints where appropriate
- Write tests for new features

### **Testing**
```bash
# Run tests
python -m pytest tests/

# Check code coverage
pip install coverage
coverage run -m pytest
coverage report
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### **Getting Help**
- 📖 **Documentation**: Check this README and STARTUP_GUIDE.md
- 🐛 **Issues**: Report bugs on GitHub Issues
- 💬 **Discussions**: Join our community discussions
- 📧 **Email**: Contact us directly

### **Useful Resources**
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Google Gemini API Docs](https://ai.google.dev/docs)
- [Redis Documentation](https://redis.io/documentation)
- [OpenCV Documentation](https://opencv.org/)

---

<div align="center">

**Visual Understanding Chat Assistant** - Advanced AI-powered video analysis with multi-turn conversations

[![GitHub stars](https://img.shields.io/github/stars/MantraHackathon/visual-understanding-chat-assistant?style=social)](https://github.com/MantraHackathon/visual-understanding-chat-assistant)
[![GitHub forks](https://img.shields.io/github/forks/MantraHackathon/visual-understanding-chat-assistant?style=social)](https://github.com/MantraHackathon/visual-understanding-chat-assistant)
[![GitHub issues](https://img.shields.io/github/issues/MantraHackathon/visual-understanding-chat-assistant)](https://github.com/MantraHackathon/visual-understanding-chat-assistant/issues)

**Built with ❤️ for the Mantra Hackathon**

</div> 
