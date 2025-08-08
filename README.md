# AI Video Detective - Advanced Multi-Modal Video Analysis

A distributed AI-powered video analysis system with real-time processing, multi-modal understanding, and sub-second query response times.

## 🚀 Features

- **Real-time Video Analysis**: Process videos up to 120 minutes at 90 FPS
- **Multi-Modal Understanding**: Combined visual and audio analysis
- **Sub-Second Queries**: < 1 second response times after video ingestion
- **Distributed Architecture**: Local development + Remote GPU server
- **Advanced AI Models**: LLaVA-NeXT-Video-7B, RT-DETR-v2, Whisper, Wav2Vec2
- **Comprehensive Analysis Types**: Safety, Performance, Pattern Detection, Creative Review
- **Modern Web Interface**: Real-time chat with AI assistant
- **Event Timeline**: Detailed event tracking and visualization

## 🏗️ Architecture

### Distributed System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Local Development Environment            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Web UI    │  │  Flask API  │  │   File Upload &     │ │
│  │  (Port 8888)│  │ (Port 8080) │  │   Session Mgmt      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Remote GPU Server                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Redis     │  │   Ray       │  │   DuckDB            │ │
│  │  Pub/Sub    │  │  Cluster    │  │   Events Store      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ GPU 0-3     │  │ GPU 4       │  │ GPU 5               │ │
│  │ Video Proc  │  │ Audio Proc  │  │ VLM (LLaVA)         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### GPU Allocation (7× A100 80GB)

- **GPU 0-3**: Video processing (RT-DETR-v2, ByteTrack)
- **GPU 4**: Audio processing (Whisper, Wav2Vec2)
- **GPU 5**: VLM serving (LLaVA-NeXT-Video-7B)
- **GPU 6**: Video encoding (NVENC)

## 📋 Requirements

### System Requirements

- **Local Environment**: Any OS with Python 3.10+
- **Remote GPU Server**: Ubuntu 22.04 with NVIDIA drivers
- **GPU**: 7× NVIDIA A100 80GB (or equivalent)
- **RAM**: 64GB+ recommended
- **Storage**: 1TB+ SSD for video processing

### Software Dependencies

- Python 3.10+
- CUDA 12.7+
- FFmpeg with NVIDIA codecs
- Redis 6.0+
- Docker (optional)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai_video_detective2
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file:

```bash
# Environment
ENV=development
DEBUG=true

# Distributed Architecture
IS_REMOTE_SERVER=false
REMOTE_GPU_SERVER_URL=http://localhost:8001

# GPU Configuration
NUM_GPUS=7

# Models
LLAVA_MODEL=llava-hf/LLaVA-NeXT-Video-7B-hf
WHISPER_MODEL=base

# Processing
WINDOW_SECONDS=20
AUDIO_ENABLED=true

# Storage
LOCAL_UPLOAD_DIR=./static/uploads
DUCKDB_PATH=./data/events.duckdb

# Network
LOCAL_PORTS=8888,8080,8000

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Analysis Types
ANALYSIS_TYPES=comprehensive_analysis,safety_investigation,performance_analysis,pattern_detection,creative_review
```

### 5. Setup Directories

```bash
mkdir -p static/uploads temp data logs
```

## 🚀 Quick Start

### Local Development Server

```bash
# Start local server (for development)
python main.py --mode local --debug

# Or with custom host/port
python main.py --mode local --host 0.0.0.0 --port 8888 --debug
```

### Remote GPU Server

```bash
# Start remote GPU server
python main.py --mode remote --host 0.0.0.0 --port 8001

# Start background worker
python main.py --mode worker
```

### Using Gunicorn (Production)

```bash
# Local server
gunicorn -w 4 -k gevent --bind 0.0.0.0:8888 app:create_app

# Remote server
gunicorn -w 4 -k gevent --bind 0.0.0.0:8001 app:create_app
```

## 📖 Usage

### 1. Access the Web Interface

Open your browser and navigate to:
- **Local**: http://localhost:8888
- **Remote**: http://your-server-ip:8888

### 2. Upload a Video

1. Drag and drop a video file or click to browse
2. Supported formats: MP4, AVI, MOV, MKV, WebM, FLV
3. Maximum file size: 1GB

### 3. Select Analysis Type

Choose from:
- **Comprehensive Analysis**: Complete multi-dimensional analysis
- **Safety Investigation**: Risk assessment and violation detection
- **Performance Analysis**: Efficiency and optimization evaluation
- **Pattern Detection**: Behavioral pattern recognition
- **Creative Review**: Artistic and aesthetic analysis

### 4. Chat with AI

Ask questions about the video:
- "What safety violations do you see?"
- "Analyze the performance of the workers"
- "What patterns emerge in the behavior?"
- "Evaluate the creative elements"

## 🔧 Configuration

### Model Configuration

```python
# config.py
models = ModelConfig(
    llava_model="llava-hf/LLaVA-NeXT-Video-7B-hf",
    detection_model="RT-DETR-v2",
    whisper_model="base",
    tensorrt_enabled=True
)
```

### Processing Configuration

```python
processing = ProcessingConfig(
    target_fps=90,
    window_seconds=20,
    audio_enabled=True,
    adaptive_sampling=True
)
```

### GPU Configuration

```python
gpu = GPUConfig(
    num_gpus=7,
    gpu_memory_gb=80,
    gpu_ids=[0, 1, 2, 3, 4, 5, 6]
)
```

## 📊 Performance

### Benchmarks

- **Query Latency**: < 600ms (p50), < 950ms (p95)
- **Video Processing**: 90 FPS sustained
- **Long Videos**: 120 minutes supported
- **Concurrent Users**: 10+ simultaneous sessions

### Optimization Features

- **Adaptive Sampling**: 6-24 FPS based on motion
- **TensorRT Optimization**: FP16/INT8 inference
- **Ray Distribution**: Multi-GPU parallel processing
- **Redis Caching**: Real-time event streaming
- **DuckDB**: Vectorized event queries

## 🔍 Analysis Types

### 1. Comprehensive Analysis

Complete multi-dimensional analysis covering:
- Visual elements and objects
- Audio content and speech
- Temporal structure and events
- Spatial relationships
- Behavioral patterns
- Technical quality assessment

### 2. Safety Investigation

Expert safety analysis including:
- Safety violations and risks
- Regulatory compliance
- Environmental hazards
- Behavioral safety assessment
- Emergency preparedness
- Corrective action plans

### 3. Performance Analysis

Efficiency and optimization evaluation:
- Process efficiency metrics
- Quality assessment
- Competency evaluation
- Productivity analysis
- Technical performance
- Improvement opportunities

### 4. Pattern Detection

Advanced behavioral pattern recognition:
- Movement patterns
- Interaction patterns
- Temporal patterns
- Social dynamics
- Anomaly detection
- Predictive insights

### 5. Creative Review

Artistic and aesthetic analysis:
- Visual aesthetics
- Storytelling and narrative
- Brand alignment
- Creative execution
- Emotional impact
- Cultural relevance

## 🛡️ Security

### Access Control

- IP whitelisting support
- API key authentication (optional)
- CORS configuration
- File upload validation

### Data Privacy

- Local processing option
- Encrypted storage
- Session management
- Audit logging

## 🔧 Development

### Project Structure

```
ai_video_detective2/
├── app.py                 # Main Flask application
├── main.py               # Entry point
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── services/            # Core services
│   ├── ai_service.py    # AI/VLM processing
│   ├── video_service.py # Video processing
│   ├── audio_service.py # Audio processing
│   ├── event_service.py # Event management
│   └── session_service.py # Session management
├── utils/               # Utilities
│   └── logger.py        # Logging utilities
├── templates/           # HTML templates
│   └── index.html       # Main interface
├── static/              # Static files
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript
│   └── uploads/        # Uploaded videos
└── data/               # Database and logs
```

### API Endpoints

#### Video Management
- `POST /api/upload` - Upload video file
- `GET /api/videos/{id}/status` - Get processing status
- `GET /api/videos/{id}/events` - Get video events
- `GET /api/videos/{id}/clips` - Generate video clips

#### Chat Interface
- `POST /api/chat` - Send chat message
- `WS /ws/chat` - WebSocket chat connection
- `WS /ws/progress` - Processing progress updates

#### Health & Status
- `GET /health` - Health check
- `GET /` - Main web interface

### Adding New Analysis Types

1. Define analysis template in `ai_service.py`
2. Add analysis type to configuration
3. Update frontend interface
4. Test with sample videos

## 🐛 Troubleshooting

### Common Issues

#### GPU Memory Errors
```bash
# Reduce batch size or model precision
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

#### Redis Connection Issues
```bash
# Start Redis server
redis-server --port 6379

# Test connection
redis-cli ping
```

#### FFmpeg Errors
```bash
# Install NVIDIA codecs
sudo apt-get install nvidia-cuda-toolkit
ffmpeg -encoders | grep nvenc
```

### Logs and Debugging

```bash
# View application logs
tail -f logs/ai_video_detective_*.log

# Enable debug mode
export DEBUG=true
python main.py --debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **LLaVA Team**: For the excellent video understanding model
- **Ultralytics**: For RT-DETR-v2 object detection
- **OpenAI**: For Whisper speech recognition
- **Ray Team**: For distributed computing framework
- **DuckDB Team**: For high-performance analytics database

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review troubleshooting guide

---

**AI Video Detective** - Advanced Multi-Modal Video Analysis with Real-time AI 