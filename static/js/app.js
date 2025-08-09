// AI Video Detective - Professional JavaScript Application with Real-time WebSocket Support

class VideoDetective {
    constructor() {
        this.currentFile = null;
        this.analysisComplete = false;
        this.isTyping = false;
        this.socket = null;
        this.currentSessionId = null;
        this.currentUploadId = null;
        this.currentUploader = null;
        this.heartbeatInterval = null;
        this.init();
    }

    init() {
        console.log('🚀 Initializing AI Video Detective Pro with Real-time WebSocket Support...');
        this.initializeWebSocket();
        this.setupEventListeners();
        this.setupAutoResize();
        this.checkSessionStatus();
        this.setupPageCleanup();
        this.showDemoVideoPreview();
        console.log('✅ AI Video Detective Pro initialized with real-time capabilities!');
    }

    // WebSocket initialization for real-time communication
    initializeWebSocket() {
        if (this.socket) {
            this.socket.disconnect();
        }
        
        console.log('🔗 Connecting to WebSocket for real-time updates...');
        this.socket = io({
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 20000,
            transports: ['websocket', 'polling']
        });
        
        this.socket.on('connect', () => {
            console.log('🔗 Connected to WebSocket for real-time updates');
            this.showNotification('Real-time connection established', 'success');
            
            // Join session if we have one
            if (this.currentSessionId) {
                this.socket.emit('join_session', { session_id: this.currentSessionId });
            }
        });
        
        this.socket.on('disconnect', () => {
            console.log('🔌 Disconnected from WebSocket');
            this.showNotification('Real-time connection lost', 'warning');
            
            // If upload is in progress, show reconnection message
            if (this.currentUploadId) {
                this.showNotification('Upload in progress - attempting to reconnect...', 'info');
            }
        });
        
        this.socket.on('reconnect', () => {
            console.log('🔄 WebSocket reconnected');
            this.showNotification('Real-time connection restored', 'success');
            
            // Rejoin session if we have one
            if (this.currentSessionId) {
                this.socket.emit('join_session', { session_id: this.currentSessionId });
            }
            
            // If upload was in progress, show reconnection message
            if (this.currentUploadId) {
                this.showNotification('Upload connection restored - resuming...', 'info');
            }
        });
        
        this.socket.on('reconnect_error', () => {
            console.log('❌ WebSocket reconnection failed');
            this.showNotification('Connection failed - please refresh page', 'error');
        });
        
        // Analysis progress updates
        this.socket.on('analysis_progress', (data) => {
            this.updateAnalysisProgress(data.stage, data.progress, data.message);
        });
        
        // Long video detection
        this.socket.on('long_video_detected', (data) => {
            this.showNotification(`Long video detected (${data.duration_minutes.toFixed(1)} minutes) - Using smart sampling!`, 'info');
        });
        
        // AI thinking indicator
        this.socket.on('ai_thinking', (data) => {
            this.showAIThinking(data.message);
        });
        
        // Analysis completion
        this.socket.on('analysis_complete', (data) => {
            this.hideAnalysisProgress();
            this.hideAIThinking();
            this.handleAnalysisComplete(data.result, data.timing);
        });
        
        // Chat response (real-time streaming)
        this.socket.on('chat_response', (data) => {
            this.handleChatResponse(data.response, data.timing);
        });
        
        // Error handling
        this.socket.on('error', (data) => {
            this.hideAnalysisProgress();
            this.hideAIThinking();
            this.showNotification(`Error: ${data.error}`, 'error');
        });
        
        // Session joined confirmation
        this.socket.on('session_joined', (data) => {
            console.log(`📡 Joined session: ${data.session_id} for real-time updates`);
        });
    }

    setupEventListeners() {
        // File upload
        const videoFile = document.getElementById('videoFile');
        const uploadArea = document.getElementById('uploadArea');

        videoFile.addEventListener('change', (e) => this.handleFileSelect(e));

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        });

        uploadArea.addEventListener('click', () => {
            videoFile.click();
        });

        // Chat functionality
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');

        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        sendBtn.addEventListener('click', () => this.sendMessage());
    }

    setupAutoResize() {
        const chatInput = document.getElementById('chatInput');
        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
        });
    }

    setupPageCleanup() {
        // Clean up old uploads when page loads
        this.cleanupOldUploads();
        
        // Clean up when user navigates away or refreshes
        window.addEventListener('beforeunload', () => {
            this.cleanupOldUploads();
        });
        
        // Clean up when user goes back to upload screen
        window.addEventListener('popstate', () => {
            this.cleanupOldUploads();
        });
    }

    async cleanupOldUploads() {
        try {
            const response = await fetch('/cleanup-uploads', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            if (result.success) {
                console.log('🧹 Old uploads cleaned up');
            }
        } catch (error) {
            console.log('Cleanup request failed (normal on page unload)');
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.handleFile(file);
        }
    }

    handleFile(file) {
        if (!this.isValidVideoFile(file)) {
            this.showError('Please select a valid video file (MP4, AVI, MOV, WebM, MKV)');
            return;
        }

        if (file.size > 2 * 1024 * 1024 * 1024) { // 2GB limit - 80GB GPU optimized
            this.showError('File size must be less than 2GB');
            return;
        }

        this.currentFile = file;
        this.showFileInfo(file);
        this.showVideoPreview(file);
        
        // Initialize WebSocket upload capabilities
        this.initializeWebSocketUpload();
    }
    
    // === SESSION MANAGEMENT ===
    
    generateSessionId() {
        // Generate a unique session ID
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // === WEBSOCKET UPLOAD METHODS ===
    
    initializeWebSocketUpload() {
        // Initialize WebSocket upload event listeners
        if (!this.socket) {
            console.error('WebSocket not connected');
            return;
        }
        
        // WebSocket upload event listeners
        this.socket.on('upload_ready', (data) => {
            console.log('📤 Upload ready:', data);
            this.currentUploadId = data.upload_id;
            this.showNotification(data.message, 'success');
        });
        
        this.socket.on('upload_progress', (data) => {
            this.updateUploadProgress(data);
        });
        
        this.socket.on('upload_completed', (data) => {
            console.log('✅ Upload completed:', data);
            this.stopUploadHeartbeat();
            this.hideUploadProgress();
            this.showSuccess(data.message);
            this.currentFilePath = data.file_path;
            this.currentUploadId = null;
            this.enableAnalysisButtons();
        });
        
        this.socket.on('upload_error', (data) => {
            console.error('❌ Upload error:', data);
            this.stopUploadHeartbeat();
            this.hideUploadProgress();
            this.showError(`Upload failed: ${data.error}`);
            
            // Reset upload state
            this.currentUploadId = null;
        });
        
        this.socket.on('upload_cancelled', (data) => {
            console.log('🚫 Upload cancelled:', data);
            this.stopUploadHeartbeat();
            this.hideUploadProgress();
            this.showNotification(data.message, 'warning');
            this.currentUploadId = null;
        });
        
        this.socket.on('chunk_received', (data) => {
            // Real-time chunk confirmation (optional)
            console.log(`📦 Chunk received: ${data.progress.toFixed(1)}%`);
        });
    }
    
    async startWebSocketUpload() {
        // Start WebSocket-based file upload
        if (!this.currentFile) {
            this.showError('No file selected');
            return;
        }
        
        if (!this.socket || !this.socket.connected) {
            this.showError('WebSocket not connected. Please refresh the page.');
            return;
        }
        
        try {
            // Ensure we have a session ID
            if (!this.currentSessionId) {
                this.currentSessionId = this.generateSessionId();
                console.log('🔄 Generated new session ID:', this.currentSessionId);
            }
            
            // Join the session for real-time updates
            this.socket.emit('join_session', { session_id: this.currentSessionId });
            
            // Show upload progress UI
            this.showUploadProgress();
            
            console.log('📤 Starting WebSocket upload:', {
                session_id: this.currentSessionId,
                filename: this.currentFile.name,
                file_size: this.currentFile.size,
                file_type: this.currentFile.type
            });
            
            // Initialize upload session
            this.socket.emit('start_upload', {
                session_id: this.currentSessionId,
                filename: this.currentFile.name,
                file_size: this.currentFile.size,
                file_type: this.currentFile.type
            });
            
            // Wait for upload_ready event before starting chunk upload (with timeout)
            const uploadTimeout = setTimeout(() => {
                this.hideUploadProgress();
                this.showError('Upload initialization timeout. Please try again.');
            }, 10000); // 10 second timeout
            
            this.socket.once('upload_ready', (data) => {
                clearTimeout(uploadTimeout);
                this.currentUploadId = data.upload_id;
                this.startUploadHeartbeat();
                this.uploadFileInChunks();
            });
            
            this.socket.once('upload_error', (data) => {
                clearTimeout(uploadTimeout);
                // Error handling is already set up in initializeWebSocketUpload
            });
            
        } catch (error) {
            console.error('Upload start error:', error);
            this.showError(`Upload failed: ${error.message}`);
            this.hideUploadProgress();
        }
    }
    
    async uploadFileInChunks() {
        // Upload file in chunks via WebSocket - Dynamic chunk size for 80GB GPU optimization
        const file = this.currentFile;
        
        // Dynamic chunk size based on file size for optimal performance
        let CHUNK_SIZE;
        if (file.size < 100 * 1024 * 1024) { // < 100MB
            CHUNK_SIZE = 5 * 1024 * 1024;   // 5MB chunks
        } else if (file.size < 500 * 1024 * 1024) { // < 500MB  
            CHUNK_SIZE = 10 * 1024 * 1024;  // 10MB chunks
        } else { // Large files (500MB+)
            CHUNK_SIZE = 20 * 1024 * 1024;  // 20MB chunks for maximum speed
        }
        
        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        
        console.log(`🚀 Starting chunked upload: ${totalChunks} chunks of ${CHUNK_SIZE / (1024*1024)}MB each (file: ${(file.size / (1024*1024)).toFixed(1)}MB)`);
        
        for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
            const start = chunkIndex * CHUNK_SIZE;
            const end = Math.min(start + CHUNK_SIZE, file.size);
            const chunk = file.slice(start, end);
            const isLast = chunkIndex === totalChunks - 1;
            
            try {
                // Convert chunk to base64
                const base64Chunk = await this.fileToBase64(chunk);
                
                // Send chunk via WebSocket
                this.socket.emit('upload_chunk', {
                    upload_id: this.currentUploadId,
                    chunk_data: base64Chunk,
                    chunk_index: chunkIndex,
                    is_final: isLast
                });
                
                // Minimal delay only for very large uploads to prevent overwhelming
                if (totalChunks > 100 && chunkIndex % 10 === 0 && chunkIndex > 0) {
                    await new Promise(resolve => setTimeout(resolve, 2));
                }
                
            } catch (error) {
                console.error(`Chunk ${chunkIndex} upload failed:`, error);
                this.cancelWebSocketUpload();
                this.showError(`Upload failed at chunk ${chunkIndex + 1}/${totalChunks}`);
                return;
            }
        }
    }
    
    cancelWebSocketUpload() {
        // Cancel active upload (HTTP or WebSocket)
        if (this.currentUploader) {
            // Cancel fast HTTP upload
            this.currentUploader.cancelUpload();
            this.currentUploader = null;
        } else if (this.currentUploadId && this.socket) {
            // Cancel WebSocket upload
            this.socket.emit('cancel_upload', {
                upload_id: this.currentUploadId
            });
            this.currentUploadId = null;
        }
        this.stopUploadHeartbeat();
        this.hideUploadProgress();
    }
    
    fileToBase64(file) {
        // Convert file chunk to base64
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                // Remove data URL prefix (data:;base64,)
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }
    
    showUploadProgress() {
        // Show upload progress UI
        const uploadArea = document.getElementById('uploadArea');
        
        // Create progress UI if it doesn't exist
        if (!document.getElementById('uploadProgress')) {
            const progressHTML = `
                <div id="uploadProgress" class="upload-progress">
                    <div class="progress-header">
                        <h3>📤 Uploading Video...</h3>
                        <div id="percentageDisplay" class="percentage-display">0%</div>
                        <button id="cancelUploadBtn" class="cancel-btn">❌ Cancel</button>
                    </div>
                    <div class="progress-bar-container">
                        <div id="progressBar" class="progress-bar">
                            <div id="progressFill" class="progress-fill">
                                <div id="progressPercentage" class="progress-percentage">0%</div>
                            </div>
                        </div>
                        <div id="progressText" class="progress-text">0 MB/s</div>
                    </div>
                    <div id="uploadDetails" class="upload-details">
                        Preparing upload...
                    </div>
                </div>
            `;
            uploadArea.insertAdjacentHTML('afterend', progressHTML);
            
            // Add cancel button handler
            document.getElementById('cancelUploadBtn').addEventListener('click', () => {
                this.cancelWebSocketUpload();
            });
        }
        
        document.getElementById('uploadProgress').style.display = 'block';
    }
    
    updateUploadProgress(data) {
        // Update upload progress display with prominent percentage
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const uploadDetails = document.getElementById('uploadDetails');
        const percentageDisplay = document.getElementById('percentageDisplay');
        const progressPercentage = document.getElementById('progressPercentage');
        
        const percentage = data.progress.toFixed(1);
        
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
        
        if (percentageDisplay) {
            percentageDisplay.textContent = `${percentage}%`;
        }
        
        if (progressPercentage) {
            progressPercentage.textContent = `${percentage}%`;
            // Show percentage inside bar only when there's enough space (>10%)
            progressPercentage.style.display = data.progress > 10 ? 'block' : 'none';
        }
        
        if (progressText) {
            progressText.textContent = `${data.upload_speed.toFixed(1)} MB/s`;
        }
        
        if (uploadDetails) {
            uploadDetails.textContent = `${this.formatFileSize(data.bytes_received)} / ${this.formatFileSize(data.total_size)} • ${data.chunks_received} chunks received`;
        }
        
        console.log(`📊 Upload Progress: ${percentage}% (${data.upload_speed.toFixed(1)} MB/s)`);
    }
    
    hideUploadProgress() {
        // Hide upload progress UI
        const uploadProgress = document.getElementById('uploadProgress');
        if (uploadProgress) {
            uploadProgress.style.display = 'none';
        }
    }
    
    enableAnalysisButtons() {
        // Enable analysis buttons after successful upload
        const analyzeBtn = document.getElementById('analyzeBtn');
        const uploadBtn = document.getElementById('uploadBtn');
        
        if (analyzeBtn) analyzeBtn.disabled = false;
        if (uploadBtn) uploadBtn.textContent = '✅ Ready to Analyze';
    }
    
    startUploadHeartbeat() {
        // Start heartbeat to keep connection alive during upload
        this.heartbeatInterval = setInterval(() => {
            if (this.socket && this.socket.connected && this.currentUploadId) {
                this.socket.emit('ping');
            }
        }, 15000); // Ping every 15 seconds during upload
    }
    
    stopUploadHeartbeat() {
        // Stop heartbeat when upload is complete
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    isValidVideoFile(file) {
        const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/webm', 'video/x-matroska'];
        return validTypes.includes(file.type);
    }

    showFileInfo(file) {
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        
        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);
        fileInfo.style.display = 'block';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showVideoPreview(file) {
        const videoPreview = document.getElementById('videoPreview');
        const previewVideo = document.getElementById('previewVideo');
        
        // Create object URL for video preview
        const videoUrl = URL.createObjectURL(file);
        previewVideo.src = videoUrl;
        
        // Show the preview section
        videoPreview.style.display = 'block';
        
        // Scroll to preview
        videoPreview.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        console.log('🎬 Video preview shown for:', file.name);
    }

    async uploadSelectedVideo() {
        // Hide the preview
        const videoPreview = document.getElementById('videoPreview');
        videoPreview.style.display = 'none';
        
        // Check if this is a demo video preview
        const previewVideo = document.getElementById('previewVideo');
        if (previewVideo && previewVideo.src && previewVideo.src.includes('/demo-video')) {
            // This is a demo video, upload it via traditional method (demo files are small)
            await this.uploadDemoVideo();
        } else if (this.currentFile) {
            // This is a regular uploaded file - use WebSocket upload for better performance
            await this.uploadFileWebSocket(this.currentFile);
        } else {
            // If no file is selected but we're in demo mode, upload demo video
            await this.uploadDemoVideo();
        }
    }

    async uploadFileWebSocket(file) {
        // Use fast HTTP upload instead of WebSocket for better performance
        try {
            console.log('🚀 Using Fast HTTP Upload for better performance...');
            await this.startFastHTTPUpload(file);
            
        } catch (error) {
            console.error('Fast upload failed, falling back to WebSocket:', error);
            // Fallback to WebSocket upload
            try {
                await this.startWebSocketUpload();
                
                this.socket.once('upload_completed', (data) => {
                    console.log('✅ WebSocket upload completed, starting analysis...');
                    this.showFileInfo(file, data.filename, data.file_size);
                    this.showCleanupButton();
                    this.analyzeVideo();
                });
                
            } catch (wsError) {
                console.error('WebSocket upload also failed:', wsError);
                this.showError('Upload failed: ' + wsError.message);
            }
        }
    }
    
    async startFastHTTPUpload(file) {
        // Fast HTTP chunked upload implementation
        const uploader = new FastUploader();
        
        // Show upload progress UI
        this.showUploadProgress();
        
        // Configure upload callbacks
        const uploadOptions = {
            maxConcurrent: 6, // Parallel uploads for speed
            
            onProgress: (data) => {
                this.updateUploadProgress({
                    progress: data.progress,
                    bytes_received: data.bytes_uploaded,
                    total_size: data.total_size,
                    upload_speed: data.upload_speed,
                    chunks_received: data.chunks_uploaded
                });
            },
            
            onComplete: (data) => {
                console.log('✅ Fast HTTP upload completed:', data);
                this.stopUploadHeartbeat();
                this.hideUploadProgress();
                this.showSuccess(`Upload completed: ${data.filename} (${data.average_speed.toFixed(1)}MB/s avg)`);
                
                // Set up for analysis
                this.currentFilePath = data.file_path;
                this.showFileInfo(file, data.filename, data.total_size);
                this.showCleanupButton();
                this.enableAnalysisButtons();
                this.analyzeVideo();
            },
            
            onError: (error) => {
                console.error('❌ Fast HTTP upload error:', error);
                this.stopUploadHeartbeat();
                this.hideUploadProgress();
                this.showError(`Upload failed: ${error.message}`);
            }
        };
        
        // Start heartbeat for connection stability
        this.startUploadHeartbeat();
        
        // Start the upload
        await uploader.startUpload(file, uploadOptions);
        
        // Store uploader instance for cancellation
        this.currentUploader = uploader;
    }

    async uploadFile(file) {
        // Legacy HTTP upload method (fallback for small files/demos)
        const formData = new FormData();
        formData.append('video', file);

        try {
            this.showProgress();

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.hideProgress();
                this.showFileInfo(file, result.filename, result.file_size);
                this.showCleanupButton();
                this.analyzeVideo();
            } else {
                this.hideProgress();
                this.showError(result.error || 'Upload failed');
            }
        } catch (error) {
            this.hideProgress();
            this.showError('Upload failed: ' + error.message);
        }
    }

    showProgress() {
        const progress = document.getElementById('uploadProgress');
        const progressFill = progress.querySelector('.progress-fill');
        
        progress.style.display = 'block';
        progressFill.style.width = '0%';
        
        // Simulate progress
        let width = 0;
        const interval = setInterval(() => {
            if (width >= 90) {
                clearInterval(interval);
            } else {
                width += Math.random() * 10;
                progressFill.style.width = width + '%';
            }
        }, 200);
    }

    hideProgress() {
        const progress = document.getElementById('uploadProgress');
        const progressFill = progress.querySelector('.progress-fill');
        
        progressFill.style.width = '100%';
        setTimeout(() => {
            progress.style.display = 'none';
        }, 500);
    }

    async analyzeVideo() {
        try {
            console.log('🔍 Starting video analysis...');
            this.showLoadingModal('Analyzing Video');

            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    analysis_type: 'comprehensive_analysis',
                    user_focus: 'Analyze this video comprehensively for all important events and observations'
                })
            });

            const result = await response.json();
            console.log('📊 Analysis response:', result);
            
            this.hideLoadingModal();

            if (result.success) {
                console.log('✅ Analysis successful, showing chat interface...');
                this.analysisComplete = true;
                this.showChatInterface();
                
                // Show analysis completion message with evidence if available
                let completionMessage = '🎯 **Video Analysis Complete!**\n\nI\'ve thoroughly analyzed your video and captured key insights. Here\'s what I found:';
                
                if (result.evidence && result.evidence.length > 0) {
                    const screenshotCount = result.evidence.filter(e => e.type === 'screenshot').length;
                    const videoCount = result.evidence.filter(e => e.type === 'video_clip').length;
                    
                    let evidenceText = '';
                    if (screenshotCount > 0 && videoCount > 0) {
                        evidenceText = `📸 **Visual Evidence**: I've captured ${screenshotCount} screenshots and ${videoCount} video clips at key moments.`;
                    } else if (screenshotCount > 0) {
                        evidenceText = `📸 **Visual Evidence**: I've captured ${screenshotCount} screenshots at key timestamps.`;
                    } else if (videoCount > 0) {
                        evidenceText = `🎥 **Visual Evidence**: I've captured ${videoCount} video clips at key moments.`;
                    }
                    completionMessage += `\n\n${evidenceText}`;
                }
                
                completionMessage += '\n\n**Ask me anything about the video content!** I can provide detailed insights about specific moments, events, objects, or any aspect you\'re interested in.';
                
                // Add completion message with typing effect
                this.addChatMessageWithTyping('ai', completionMessage);
                
                // Display evidence if available (after message appears)
                if (result.evidence && result.evidence.length > 0) {
                    setTimeout(() => {
                        this.displayEvidence(result.evidence);
                    }, 800); // Wait for fade-in effect to complete + buffer
                }
            } else {
                console.error('❌ Analysis failed:', result.error);
                this.showError(result.error || 'Analysis failed');
            }
        } catch (error) {
            console.error('❌ Analysis error:', error);
            this.hideLoadingModal();
            this.showError('Analysis failed: ' + error.message);
        }
    }

    displayEvidence(evidence, title = 'Visual Evidence') {
        const chatMessages = document.getElementById('chatMessages');
        
        // Create evidence container
        const evidenceContainer = document.createElement('div');
        evidenceContainer.className = 'screenshot-evidence';
        
        // Add header
        const header = document.createElement('h4');
        header.innerHTML = `📸 <strong>${title}</strong>`;
        evidenceContainer.appendChild(header);
        
        // Create evidence grid
        const grid = document.createElement('div');
        grid.className = 'evidence-grid';
        
        evidence.forEach(item => {
            const evidenceItem = document.createElement('div');
            evidenceItem.className = 'evidence-item';
            
            if (item.type === 'video_clip') {
                // Create video element
                const video = document.createElement('video');
                video.src = item.url;
                video.controls = true;
                video.preload = 'metadata';
                
                // Create timestamp label for video
                const timestamp = document.createElement('div');
                timestamp.className = 'timestamp';
                timestamp.innerHTML = `<strong>${this.formatTimestamp(item.start_time)} - ${this.formatTimestamp(item.end_time)}</strong>`;
                
                evidenceItem.appendChild(video);
                evidenceItem.appendChild(timestamp);
            } else {
                // Create image for screenshot
                const img = document.createElement('img');
                img.src = item.url;
                img.alt = `Screenshot at ${item.timestamp}s`;
                img.loading = 'lazy';
                
                // Add click event to open modal
                img.addEventListener('click', () => {
                    this.openEvidenceModal(item);
                });
                
                // Create timestamp label for screenshot
                const timestamp = document.createElement('div');
                timestamp.className = 'timestamp';
                timestamp.innerHTML = `<strong>${this.formatTimestamp(item.timestamp)}</strong>`;
                
                evidenceItem.appendChild(img);
                evidenceItem.appendChild(timestamp);
            }
            
            grid.appendChild(evidenceItem);
        });
        
        evidenceContainer.appendChild(grid);
        
        // Add to chat messages with animation
        evidenceContainer.style.opacity = '0';
        evidenceContainer.style.transform = 'translateY(20px)';
        chatMessages.appendChild(evidenceContainer);
        
        // Animate in
        setTimeout(() => {
            evidenceContainer.style.transition = 'all 0.3s ease';
            evidenceContainer.style.opacity = '1';
            evidenceContainer.style.transform = 'translateY(0)';
        }, 100);
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    openEvidenceModal(evidence) {
        const modal = document.getElementById('evidenceModal');
        const modalImage = document.getElementById('evidenceModalImage');
        const modalInfo = document.getElementById('evidenceModalInfo');
        
        modalImage.src = evidence.url;
        
        if (evidence.type === 'video_clip') {
            modalInfo.textContent = `Timestamp: ${this.formatTimestamp(evidence.start_time)} - ${this.formatTimestamp(evidence.end_time)}`;
        } else {
            modalInfo.textContent = `Timestamp: ${this.formatTimestamp(evidence.timestamp)}`;
        }
        
        modal.style.display = 'flex';
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeEvidenceModal();
            }
        });
        
        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeEvidenceModal();
            }
        });
    }

    closeEvidenceModal() {
        const modal = document.getElementById('evidenceModal');
        modal.style.display = 'none';
    }

    formatTimestamp(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    showChatInterface() {
        console.log('💬 Showing chat interface...');
        
        const uploadSection = document.getElementById('uploadSection');
        const chatInterface = document.getElementById('chatInterface');
        
        // Hide upload section with animation
        uploadSection.style.transition = 'all 0.3s ease';
        uploadSection.style.opacity = '0';
        uploadSection.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            uploadSection.style.display = 'none';
            
            // Show chat interface
            chatInterface.style.display = 'flex';
            chatInterface.style.opacity = '0';
            chatInterface.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                chatInterface.style.transition = 'all 0.3s ease';
                chatInterface.style.opacity = '1';
                chatInterface.style.transform = 'translateY(0)';
            }, 50);
        }, 300);
        
        // Enable chat input
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
        
        console.log('✅ Chat interface should now be visible');
    }

    async sendMessage() {
        const chatInput = document.getElementById('chatInput');
        const message = chatInput.value.trim();

        if (!message || this.isTyping) return;

        // Add user message
        this.addChatMessage('user', message);
        chatInput.value = '';
        chatInput.style.height = 'auto';
        
        // Disable input while processing
        chatInput.disabled = true;
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.disabled = true;

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            const result = await response.json();

            // Hide typing indicator
            this.hideTypingIndicator();

            if (result.success) {
                // Add AI message with typing effect
                this.addChatMessageWithTyping('ai', result.response);
                
                // Display additional evidence if available (after message appears)
                if (result.additional_screenshots && result.additional_screenshots.length > 0) {
                    setTimeout(() => {
                        this.displayEvidence(result.additional_screenshots, 'Additional Evidence');
                    }, 800); // Wait for fade-in effect to complete + buffer
                }
            } else {
                this.addChatMessage('ai', 'Sorry, I encountered an error. Please try again.');
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.addChatMessage('ai', 'Sorry, I encountered an error. Please try again.');
        }
        
        // Re-enable input
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }

    showTypingIndicator() {
        this.isTyping = true;
        const typingIndicator = document.getElementById('typingIndicator');
        typingIndicator.style.display = 'block';
        
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    hideTypingIndicator() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typingIndicator');
        typingIndicator.style.display = 'none';
    }

    addChatMessage(type, message) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}-message`;

        const icon = type === 'user' ? 'fas fa-user' : 'fas fa-robot';
        
        // Enhanced message formatting for AI responses
        let formattedMessage = message;
        if (type === 'ai') {
            formattedMessage = this.formatAIResponse(message);
        }

        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-avatar">
                <i class="${icon}"></i>
                </div>
                <div class="message-text"></div>
            </div>
        `;

        // Set the formatted content safely
        const messageTextElement = messageDiv.querySelector('.message-text');
        messageTextElement.innerHTML = formattedMessage;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    addChatMessageWithTyping(type, message) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}-message`;

        const icon = type === 'user' ? 'fas fa-user' : 'fas fa-robot';
        
        // Enhanced message formatting for AI responses
        let formattedMessage = this.formatAIResponse(message);

        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-avatar">
                    <i class="${icon}"></i>
                </div>
                <div class="message-text"></div>
                </div>
            `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Show message with fade-in effect
        const messageText = messageDiv.querySelector('.message-text');
        this.showMessageWithEffect(messageText, formattedMessage);
    }

    showMessageWithEffect(element, text) {
        // Start with opacity 0 and add fade-in effect
        element.style.opacity = '0';
        element.style.transform = 'translateY(10px)';
        element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        // Set the content immediately
        element.innerHTML = text;
        
        // Trigger the fade-in animation
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, 50);
    }

    formatAIResponse(message) {
        // Convert markdown-style formatting to HTML
        return message
            // Bold text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic text
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Headers
            .replace(/^### (.*$)/gim, '<h4 style="margin: 15px 0 8px 0; color: #1a1a1a; font-weight: 600;">$1</h4>')
            .replace(/^## (.*$)/gim, '<h3 style="margin: 20px 0 10px 0; color: #1a1a1a; font-weight: 600;">$1</h3>')
            .replace(/^# (.*$)/gim, '<h2 style="margin: 25px 0 15px 0; color: #1a1a1a; font-weight: 600;">$1</h2>')
            // Bullet points
            .replace(/^\* (.*$)/gim, '<li>$1</li>')
            .replace(/^- (.*$)/gim, '<li>$1</li>')
            // Numbered lists
            .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
            // Wrap lists in ul/ol tags
            .replace(/(<li>.*<\/li>)/gs, '<ul style="margin: 12px 0; padding-left: 24px;">$1</ul>')
            // Line breaks
            .replace(/\n/g, '<br>')
            // Timestamps with special styling
            .replace(/(\d{2}:\d{2}-\d{2}:\d{2})/g, '<span style="background: #f3f4f6; padding: 4px 8px; border-radius: 6px; font-family: monospace; font-weight: 600; color: #374151; border: 1px solid #e5e7eb;">$1</span>')
            // Single timestamps
            .replace(/(\d{2}:\d{2})/g, '<span style="background: #f3f4f6; padding: 4px 8px; border-radius: 6px; font-family: monospace; color: #374151;">$1</span>');
    }

    showLoadingModal(message) {
        const modal = document.getElementById('loadingModal');
        const loadingMessage = document.getElementById('loadingMessage');
        
        loadingMessage.textContent = message;
        modal.style.display = 'flex';
        
        // Animate loading steps
        this.animateLoadingSteps();
    }

    animateLoadingSteps() {
        const steps = document.querySelectorAll('.loading-steps .step');
        let currentStep = 0;
        
        const interval = setInterval(() => {
            steps.forEach((step, index) => {
                if (index <= currentStep) {
                    step.classList.add('active');
                } else {
                    step.classList.remove('active');
                }
            });
            
            currentStep++;
            if (currentStep >= steps.length) {
                clearInterval(interval);
            }
        }, 1000);
    }

    hideLoadingModal() {
        const modal = document.getElementById('loadingModal');
        modal.style.display = 'none';
    }

    showError(message) {
        // Create a professional error notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 3000;
            font-weight: 500;
            max-width: 300px;
            animation: slideInRight 0.3s ease;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 5000);
    }

    async cleanupSession() {
        try {
            const response = await fetch('/session/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            
            if (result.success) {
                this.resetUpload();
                this.hideCleanupButton();
                this.showSuccess('Session cleaned up successfully! All files and data have been removed.');
            } else {
                this.showError('Failed to cleanup session: ' + result.error);
            }
        } catch (error) {
            console.error('Cleanup error:', error);
            this.showError('Error cleaning up session: ' + error.message);
        }
    }

    showSuccess(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 3000;
            font-weight: 500;
            max-width: 300px;
            animation: slideInRight 0.3s ease;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    async checkSessionStatus() {
        try {
            const response = await fetch('/session/status');
            const result = await response.json();
            
            if (result.active) {
                // Update session ID for WebSocket
                if (result.session_id && result.session_id !== this.currentSessionId) {
                    this.updateSessionId(result.session_id);
                }
                
                if (result.video_uploaded || result.evidence_count > 0) {
                    this.showCleanupButton();
                } else {
                    this.hideCleanupButton();
                }
                console.log('📊 Session status:', result);
            } else {
                this.hideCleanupButton();
            }
        } catch (error) {
            console.error('Session status check error:', error);
        }
    }

    showCleanupButton() {
        const floatingCleanup = document.getElementById('floatingCleanup');
        if (floatingCleanup) {
            floatingCleanup.style.display = 'block';
        }
    }

    hideCleanupButton() {
        const floatingCleanup = document.getElementById('floatingCleanup');
        if (floatingCleanup) {
            floatingCleanup.style.display = 'none';
        }
    }



    showDemoVideoPreview() {
        try {
            console.log('🎬 Showing demo video preview...');
            
            // Show video preview with demo video URL
            const videoPreview = document.getElementById('videoPreview');
            const previewVideo = document.getElementById('previewVideo');
            
            // Set the demo video source
            previewVideo.src = '/demo-video';
            
            // Show the preview section
            videoPreview.style.display = 'block';
            
            // Update preview header for demo video
            const previewHeader = videoPreview.querySelector('.preview-header h3');
            if (previewHeader) {
                previewHeader.textContent = 'Demo Video Preview';
            }
            
            const previewDescription = videoPreview.querySelector('.preview-header p');
            if (previewDescription) {
                previewDescription.textContent = 'Preview the BMW M4 demo video before using it for analysis';
            }
            
            console.log('🎬 Demo video preview shown');
        } catch (error) {
            console.error('Failed to show demo video preview:', error);
        }
    }

    async uploadDemoVideo() {
        try {
            console.log('🎬 Uploading demo video...');
            this.showProgress();
            
            // Upload demo video (no actual file, just trigger the server to use default)
            const formData = new FormData();
            // Don't append any file - this will trigger the server to use default video
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.hideProgress();
                this.showCleanupButton();
                
                // Create a mock file object for the demo video and show file info
                const demoFile = {
                    name: 'BMW M4 - Ultimate Racetrack - BMW Canada (720p, h264).mp4',
                    size: 0,
                    type: 'video/mp4'
                };
                this.showFileInfo(demoFile);
                
                // Update file info with actual data from server
                if (result.filename) {
                    const fileInfo = document.getElementById('fileInfo');
                    const fileName = fileInfo.querySelector('.file-name');
                    if (fileName) {
                        fileName.textContent = result.filename;
                    }
                }
                
                // Show success message
                this.showSuccess('Demo video loaded successfully! 🎬');
                
                // Start analysis
                this.analyzeVideo();
            } else {
                this.hideProgress();
                this.showError(result.error || 'Failed to load demo video');
            }
        } catch (error) {
            this.hideProgress();
            this.showError('Failed to load demo video: ' + error.message);
        }
    }

    resetUpload() {
        // Clear current file
        const videoFile = document.getElementById('videoFile');
        videoFile.value = '';
        
        // Hide file info
        const fileInfo = document.getElementById('fileInfo');
        fileInfo.style.display = 'none';
        
        // Hide video preview and clean up object URL
        const videoPreview = document.getElementById('videoPreview');
        const previewVideo = document.getElementById('previewVideo');
        if (videoPreview) {
            videoPreview.style.display = 'none';
        }
        if (previewVideo && previewVideo.src) {
            if (previewVideo.src.includes('/demo-video')) {
                // For demo video, just clear the src
                previewVideo.src = '';
            } else {
                // For uploaded videos, revoke the object URL
                URL.revokeObjectURL(previewVideo.src);
                previewVideo.src = '';
            }
        }
        
        // Clear current file reference
        this.currentFile = null;
        
        // Show upload section with animation
        const uploadSection = document.getElementById('uploadSection');
        const chatInterface = document.getElementById('chatInterface');
        
        chatInterface.style.transition = 'all 0.3s ease';
        chatInterface.style.opacity = '0';
        chatInterface.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            chatInterface.style.display = 'none';
            
            uploadSection.style.display = 'block';
            uploadSection.style.opacity = '0';
            uploadSection.style.transform = 'translateY(-20px)';
            
            setTimeout(() => {
                uploadSection.style.transition = 'all 0.3s ease';
                uploadSection.style.opacity = '1';
                uploadSection.style.transform = 'translateY(0)';
            }, 50);
        }, 300);
        
        // Clear chat messages
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';
        
        // Disable chat input
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        chatInput.disabled = true;
        sendBtn.disabled = true;
        chatInput.style.height = 'auto';
        
        // Reset analysis state
        this.analysisComplete = false;
        
        // Clean up old uploads when returning to home screen
        this.cleanupOldUploads();
        
        console.log('🔄 Upload interface reset');
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Real-time WebSocket helper methods for VideoDetective class
VideoDetective.prototype.updateAnalysisProgress = function(stage, progress, message) {
    let progressContainer = document.getElementById('analysis-progress');
    if (!progressContainer) {
        this.createProgressContainer();
        progressContainer = document.getElementById('analysis-progress');
    }
    
    const progressBar = document.getElementById('analysis-progress-bar');
    const progressText = document.getElementById('analysis-progress-text');
    
    if (progressContainer && progressBar && progressText) {
        progressContainer.style.display = 'block';
        progressBar.style.width = `${progress}%`;
        progressText.textContent = message;
        progressBar.className = `progress-bar progress-${stage}`;
        console.log(`📊 Progress: ${stage} - ${progress}% - ${message}`);
    }
};

VideoDetective.prototype.createProgressContainer = function() {
    const chatInterface = document.getElementById('chatInterface');
    if (chatInterface && !document.getElementById('analysis-progress')) {
        const progressHTML = `
            <div id="analysis-progress" class="progress-container" style="display: none;">
                <div class="progress-header">
                    <span id="analysis-progress-text">Starting analysis...</span>
                </div>
                <div class="progress-bar-container">
                    <div id="analysis-progress-bar" class="progress-bar"></div>
                </div>
            </div>`;
        
        const resultArea = document.getElementById('resultArea');
        if (resultArea) {
            resultArea.insertAdjacentHTML('beforebegin', progressHTML);
        }
    }
};

VideoDetective.prototype.showAIThinking = function(message) {
    let thinkingDiv = document.getElementById('ai-thinking');
    if (!thinkingDiv) {
        const chatInterface = document.getElementById('chatInterface');
        if (chatInterface) {
            const thinkingHTML = `<div id="ai-thinking" class="ai-thinking" style="display: none;">🧠 AI is thinking...</div>`;
            const resultArea = document.getElementById('resultArea');
            if (resultArea) {
                resultArea.insertAdjacentHTML('beforebegin', thinkingHTML);
                thinkingDiv = document.getElementById('ai-thinking');
            }
        }
    }
    
    if (thinkingDiv) {
        thinkingDiv.style.display = 'block';
        thinkingDiv.textContent = message;
    }
};

VideoDetective.prototype.hideAIThinking = function() {
    const thinkingDiv = document.getElementById('ai-thinking');
    if (thinkingDiv) {
        thinkingDiv.style.display = 'none';
    }
};

VideoDetective.prototype.hideAnalysisProgress = function() {
    const progressContainer = document.getElementById('analysis-progress');
    if (progressContainer) {
        progressContainer.style.display = 'none';
    }
};

VideoDetective.prototype.showNotification = function(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px; padding: 12px 20px; 
        border-radius: 6px; color: white; z-index: 1000; 
        animation: slideIn 0.3s ease;
        ${type === 'success' ? 'background: #28a745;' : ''}
        ${type === 'error' ? 'background: #dc3545;' : ''}
        ${type === 'warning' ? 'background: #ffc107; color: #212529;' : ''}
        ${type === 'info' ? 'background: #17a2b8;' : ''}
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 4000);
};

VideoDetective.prototype.updateSessionId = function(sessionId) {
    this.currentSessionId = sessionId;
    if (this.socket && this.socket.connected) {
        this.socket.emit('join_session', { session_id: sessionId });
    }
};

// Initialize the application
window.videoDetective = new VideoDetective();
window.closeEvidenceModal = () => window.videoDetective.closeEvidenceModal();
window.cleanupSession = () => window.videoDetective.cleanupSession();
window.uploadSelectedVideo = () => window.videoDetective.uploadSelectedVideo();

console.log('🚀 AI Video Detective Pro is ready!');