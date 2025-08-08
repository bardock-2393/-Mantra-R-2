// AI Video Detective - Frontend JavaScript Application

class AIVideoDetective {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.currentVideoId = null;
        this.isConnected = false;
        this.uploadInProgress = false;
        
        this.initializeElements();
        this.initializeEventListeners();
        this.initializeWebSocket();
    }
    
    initializeElements() {
        // Connection status
        this.connectionStatus = document.getElementById('connectionStatus');
        this.connectionText = document.getElementById('connectionText');
        
        // Upload elements
        this.uploadArea = document.getElementById('uploadArea');
        this.videoFile = document.getElementById('videoFile');
        this.uploadProgress = document.getElementById('uploadProgress');
        this.progressBar = document.getElementById('progressBar');
        this.progressText = document.getElementById('progressText');
        this.videoInfo = document.getElementById('videoInfo');
        this.videoFileName = document.getElementById('videoFileName');
        this.videoDuration = document.getElementById('videoDuration');
        this.videoResolution = document.getElementById('videoResolution');
        this.videoStatus = document.getElementById('videoStatus');
        
        // Analysis types
        this.analysisTypes = document.querySelectorAll('.analysis-type');
        
        // Chat elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendMessage = document.getElementById('sendMessage');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.clearChat = document.getElementById('clearChat');
        
        // Events timeline
        this.eventsSection = document.getElementById('eventsSection');
        this.eventsTimeline = document.getElementById('eventsTimeline');
    }
    
    initializeEventListeners() {
        // File upload
        this.videoFile.addEventListener('change', (e) => this.handleFileSelect(e));
        this.uploadArea.addEventListener('click', () => this.videoFile.click());
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        
        // Analysis types
        this.analysisTypes.forEach(type => {
            type.addEventListener('click', (e) => this.handleAnalysisTypeSelect(e));
        });
        
        // Chat
        this.sendMessage.addEventListener('click', () => this.sendChatMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });
        this.clearChat.addEventListener('click', () => this.clearChatHistory());
        
        // Window events
        window.addEventListener('beforeunload', () => this.cleanup());
    }
    
    initializeWebSocket() {
        // Initialize Socket.IO connection
        this.socket = io({
            transports: ['websocket', 'polling'],
            upgrade: true,
            rememberUpgrade: true
        });
        
        // Connection events
        this.socket.on('connect', () => this.handleConnect());
        this.socket.on('disconnect', () => this.handleDisconnect());
        this.socket.on('connected', (data) => this.handleConnected(data));
        
        // Chat events
        this.socket.on('chat_response', (data) => this.handleChatResponse(data));
        this.socket.on('error', (data) => this.handleError(data));
        
        // Progress events
        this.socket.on('upload_progress', (data) => this.handleUploadProgress(data));
    }
    
    handleConnect() {
        console.log('WebSocket connected');
        this.updateConnectionStatus('connected');
    }
    
    handleDisconnect() {
        console.log('WebSocket disconnected');
        this.updateConnectionStatus('disconnected');
    }
    
    handleConnected(data) {
        this.sessionId = data.session_id;
        console.log('Session established:', this.sessionId);
        this.updateConnectionStatus('connected');
    }
    
    updateConnectionStatus(status) {
        this.isConnected = status === 'connected';
        
        this.connectionStatus.className = `status-dot ${status}`;
        
        switch (status) {
            case 'connected':
                this.connectionText.textContent = 'Connected';
                break;
            case 'disconnected':
                this.connectionText.textContent = 'Disconnected';
                break;
            default:
                this.connectionText.textContent = 'Connecting...';
        }
        
        // Enable/disable chat input based on connection
        this.messageInput.disabled = !this.isConnected || !this.currentVideoId;
        this.sendMessage.disabled = !this.isConnected || !this.currentVideoId;
    }
    
    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.uploadFile(file);
        }
    }
    
    handleDragOver(event) {
        event.preventDefault();
        this.uploadArea.classList.add('dragover');
    }
    
    handleDragLeave(event) {
        event.preventDefault();
        this.uploadArea.classList.remove('dragover');
    }
    
    handleDrop(event) {
        event.preventDefault();
        this.uploadArea.classList.remove('dragover');
        
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            this.uploadFile(files[0]);
        }
    }
    
    async uploadFile(file) {
        if (this.uploadInProgress) return;
        
        // Validate file type
        if (!file.type.startsWith('video/')) {
            this.showError('Please select a valid video file.');
            return;
        }
        
        // Validate file size (1GB limit)
        const maxSize = 1024 * 1024 * 1024; // 1GB
        if (file.size > maxSize) {
            this.showError('File size must be less than 1GB.');
            return;
        }
        
        this.uploadInProgress = true;
        this.showUploadProgress();
        
        try {
            const formData = new FormData();
            formData.append('video', file);
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.handleUploadSuccess(result);
            
        } catch (error) {
            console.error('Upload error:', error);
            this.showError(`Upload failed: ${error.message}`);
            this.hideUploadProgress();
        } finally {
            this.uploadInProgress = false;
        }
    }
    
    showUploadProgress() {
        this.uploadArea.style.display = 'none';
        this.uploadProgress.style.display = 'block';
        this.progressBar.style.width = '0%';
        this.progressText.textContent = 'Preparing upload...';
    }
    
    hideUploadProgress() {
        this.uploadProgress.style.display = 'none';
        this.uploadArea.style.display = 'block';
    }
    
    handleUploadSuccess(result) {
        this.currentVideoId = result.video_id;
        this.hideUploadProgress();
        this.showVideoInfo(result);
        this.enableChat();
        
        // Show success message
        this.addMessage('ai', `Video uploaded successfully! I'm now analyzing "${result.filename}". You can ask me questions about the video content.`);
        
        // Start monitoring processing status
        this.monitorProcessingStatus(result.video_id);
    }
    
    showVideoInfo(result) {
        this.videoFileName.textContent = result.filename;
        this.videoDuration.textContent = 'Processing...';
        this.videoResolution.textContent = 'Processing...';
        this.videoStatus.textContent = 'Uploaded';
        this.videoInfo.style.display = 'block';
    }
    
    async monitorProcessingStatus(videoId) {
        const checkStatus = async () => {
            try {
                const response = await fetch(`/api/videos/${videoId}/status`);
                if (response.ok) {
                    const status = await response.json();
                    this.updateVideoStatus(status);
                    
                    if (status.status === 'completed') {
                        this.videoStatus.textContent = 'Analysis Complete';
                        this.addMessage('ai', 'Video analysis completed! I can now provide detailed insights about the content.');
                        return;
                    } else if (status.status === 'error') {
                        this.videoStatus.textContent = 'Analysis Failed';
                        this.addMessage('ai', 'Sorry, there was an error during video analysis. Please try uploading again.');
                        return;
                    }
                }
                
                // Continue monitoring if still processing
                setTimeout(checkStatus, 2000);
                
            } catch (error) {
                console.error('Status check error:', error);
                setTimeout(checkStatus, 5000);
            }
        };
        
        checkStatus();
    }
    
    updateVideoStatus(status) {
        if (status.duration) {
            this.videoDuration.textContent = this.formatDuration(status.duration);
        }
        if (status.resolution) {
            this.videoResolution.textContent = status.resolution;
        }
        this.videoStatus.textContent = status.status;
    }
    
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }
    
    handleAnalysisTypeSelect(event) {
        const selectedType = event.currentTarget;
        
        // Remove active class from all types
        this.analysisTypes.forEach(type => type.classList.remove('active'));
        
        // Add active class to selected type
        selectedType.classList.add('active');
        
        // Store selected analysis type
        this.selectedAnalysisType = selectedType.dataset.type;
        
        // Add message about analysis type
        const typeName = selectedType.querySelector('span').textContent;
        this.addMessage('ai', `Analysis type set to: ${typeName}. Ask me questions about this aspect of the video.`);
    }
    
    sendChatMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.isConnected || !this.currentVideoId) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Clear input
        this.messageInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Send message via WebSocket
        this.socket.emit('chat_message', {
            session_id: this.sessionId,
            message: message,
            video_id: this.currentVideoId,
            analysis_type: this.selectedAnalysisType || 'comprehensive_analysis'
        });
    }
    
    handleChatResponse(data) {
        this.hideTypingIndicator();
        
        if (data.error) {
            this.addMessage('ai', `Error: ${data.error}`);
        } else {
            this.addMessage('ai', data.answer);
        }
    }
    
    handleError(data) {
        this.hideTypingIndicator();
        this.addMessage('ai', `Error: ${data.message}`);
    }
    
    addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (type === 'ai') {
            // Format AI response with markdown-like formatting
            contentDiv.innerHTML = this.formatAIResponse(content);
        } else {
            contentDiv.textContent = content;
        }
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    formatAIResponse(content) {
        // Convert markdown-like formatting to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/### (.*?)$/gm, '<h4>$1</h4>')
            .replace(/## (.*?)$/gm, '<h3>$1</h3>')
            .replace(/# (.*?)$/gm, '<h2>$1</h2>')
            .replace(/\n/g, '<br>')
            .replace(/- (.*?)(?=<br>|$)/g, '<li>$1</li>')
            .replace(/(<li>.*?<\/li>)/s, '<ul>$1</ul>');
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    clearChatHistory() {
        // Keep welcome message, remove others
        const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
        this.chatMessages.innerHTML = '';
        if (welcomeMessage) {
            this.chatMessages.appendChild(welcomeMessage);
        }
    }
    
    enableChat() {
        this.messageInput.disabled = false;
        this.sendMessage.disabled = false;
        this.messageInput.placeholder = 'Ask me anything about the video...';
    }
    
    showError(message) {
        // Create error notification
        const notification = document.createElement('div');
        notification.className = 'alert alert-danger alert-dismissible fade show';
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    showSuccess(message) {
        // Create success notification
        const notification = document.createElement('div');
        notification.className = 'alert alert-success alert-dismissible fade show';
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    cleanup() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aiVideoDetective = new AIVideoDetective();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.aiVideoDetective) {
        window.aiVideoDetective.cleanup();
    }
}); 