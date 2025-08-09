/*!
 * Production-Grade Streaming Upload Client
 * Fast, reliable 2GB+ video uploads with parallel chunks
 * Optimized for 80GB GPU environment
 */

class StreamingUploader {
    constructor(options = {}) {
        // Configuration optimized for 80GB GPU performance
        this.CHUNK_SIZE = options.chunkSize || 16 * 1024 * 1024; // 16MB chunks
        this.MAX_PARALLEL = options.maxParallel || 6; // Parallel uploads for speed
        this.MAX_RETRIES = options.maxRetries || 3;
        this.RETRY_DELAY = options.retryDelay || 1000; // 1 second
        
        // Upload state
        this.uploadId = null;
        this.file = null;
        this.totalSize = 0;
        this.uploadedBytes = 0;
        this.workers = [];
        this.aborted = false;
        
        // Callbacks
        this.onProgress = options.onProgress || (() => {});
        this.onComplete = options.onComplete || (() => {});
        this.onError = options.onError || (() => {});
        this.onStarted = options.onStarted || (() => {});
        
        // Performance tracking
        this.startTime = null;
        this.lastProgressTime = null;
        this.lastUploadedBytes = 0;
    }
    
    /**
     * Start uploading a file
     * @param {File} file - The file to upload
     */
    async startUpload(file) {
        if (!file) {
            this.onError(new Error('No file provided'));
            return;
        }
        
        this.file = file;
        this.totalSize = file.size;
        this.aborted = false;
        this.startTime = Date.now();
        this.lastProgressTime = this.startTime;
        this.lastUploadedBytes = 0;
        
        console.log(`🚀 Starting streaming upload: ${file.name} (${(file.size / (1024**2)).toFixed(1)}MB)`);
        
        try {
            // Initialize upload session
            const initResponse = await fetch('/upload/init', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: file.name,
                    size: file.size
                })
            });
            
            if (!initResponse.ok) {
                const error = await initResponse.json();
                throw new Error(error.error || 'Upload initialization failed');
            }
            
            const initData = await initResponse.json();
            this.uploadId = initData.upload_id;
            
            console.log(`📋 Upload initialized: ${this.uploadId}`);
            
            this.onStarted({
                uploadId: this.uploadId,
                filename: initData.filename,
                totalSize: this.totalSize
            });
            
            // Start parallel chunk upload
            await this.uploadChunks();
            
            // Complete the upload
            await this.completeUpload();
            
        } catch (error) {
            console.error('❌ Upload failed:', error);
            this.onError(error);
        }
    }
    
    /**
     * Upload file in parallel chunks
     */
    async uploadChunks() {
        const totalChunks = Math.ceil(this.totalSize / this.CHUNK_SIZE);
        console.log(`📦 Uploading ${totalChunks} chunks of ${(this.CHUNK_SIZE / (1024**2))}MB each`);
        
        // Create chunk queue
        let nextChunkIndex = 0;
        
        // Start worker promises
        const workers = [];
        for (let i = 0; i < this.MAX_PARALLEL; i++) {
            workers.push(this.worker(nextChunkIndex, totalChunks, () => nextChunkIndex++));
        }
        
        // Wait for all workers to complete
        await Promise.all(workers);
        
        if (this.aborted) {
            throw new Error('Upload aborted');
        }
        
        console.log('✅ All chunks uploaded successfully');
    }
    
    /**
     * Worker function for parallel chunk upload
     */
    async worker(startIndex, totalChunks, getNextIndex) {
        while (true) {
            if (this.aborted) {
                return;
            }
            
            const chunkIndex = getNextIndex();
            if (chunkIndex >= totalChunks) {
                return; // No more chunks to process
            }
            
            const start = chunkIndex * this.CHUNK_SIZE;
            const end = Math.min(start + this.CHUNK_SIZE - 1, this.totalSize - 1);
            const chunkSize = end - start + 1;
            
            let retries = 0;
            let success = false;
            
            while (retries < this.MAX_RETRIES && !success && !this.aborted) {
                try {
                    await this.uploadChunk(start, end, chunkIndex, totalChunks);
                    success = true;
                    
                    // Update progress
                    this.uploadedBytes += chunkSize;
                    this.updateProgress();
                    
                } catch (error) {
                    retries++;
                    console.warn(`⚠️ Chunk ${chunkIndex} failed (attempt ${retries}/${this.MAX_RETRIES}):`, error.message);
                    
                    if (retries < this.MAX_RETRIES) {
                        // Exponential backoff
                        const delay = this.RETRY_DELAY * Math.pow(2, retries - 1);
                        await new Promise(resolve => setTimeout(resolve, delay));
                    } else {
                        throw new Error(`Chunk ${chunkIndex} failed after ${this.MAX_RETRIES} attempts: ${error.message}`);
                    }
                }
            }
        }
    }
    
    /**
     * Upload a single chunk
     */
    async uploadChunk(start, end, chunkIndex, totalChunks) {
        const chunkData = this.file.slice(start, end + 1);
        
        const response = await fetch(`/upload/${this.uploadId}`, {
            method: 'PUT',
            headers: {
                'Content-Range': `bytes ${start}-${end}/${this.totalSize}`,
                'Content-Type': 'application/octet-stream'
            },
            body: chunkData
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        console.log(`📦 Chunk ${chunkIndex + 1}/${totalChunks} uploaded [${start}-${end}]`);
        
        return await response.json();
    }
    
    /**
     * Complete the upload
     */
    async completeUpload() {
        console.log('🔄 Completing upload...');
        
        const response = await fetch(`/upload/${this.uploadId}/complete`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload completion failed');
        }
        
        const result = await response.json();
        
        const totalTime = (Date.now() - this.startTime) / 1000;
        const averageSpeed = (this.totalSize / (1024**2)) / totalTime;
        
        console.log(`✅ Upload completed: ${result.filename} (${averageSpeed.toFixed(1)}MB/s average)`);
        
        this.onComplete({
            ...result,
            totalTime,
            averageSpeed
        });
        
        return result;
    }
    
    /**
     * Update progress and calculate speed
     */
    updateProgress() {
        const now = Date.now();
        const progress = (this.uploadedBytes / this.totalSize) * 100;
        
        // Calculate upload speed
        let uploadSpeed = 0;
        if (this.lastProgressTime) {
            const timeDiff = (now - this.lastProgressTime) / 1000; // seconds
            const bytesDiff = this.uploadedBytes - this.lastUploadedBytes;
            uploadSpeed = (bytesDiff / (1024**2)) / timeDiff; // MB/s
        }
        
        this.lastProgressTime = now;
        this.lastUploadedBytes = this.uploadedBytes;
        
        this.onProgress({
            progress,
            uploadedBytes: this.uploadedBytes,
            totalSize: this.totalSize,
            uploadSpeed,
            elapsedTime: (now - this.startTime) / 1000
        });
    }
    
    /**
     * Get upload status from server
     */
    async getStatus() {
        if (!this.uploadId) {
            throw new Error('No active upload');
        }
        
        const response = await fetch(`/upload/${this.uploadId}/status`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to get status');
        }
        
        return await response.json();
    }
    
    /**
     * Cancel the upload
     */
    async cancelUpload() {
        this.aborted = true;
        
        if (this.uploadId) {
            try {
                const response = await fetch(`/upload/${this.uploadId}/cancel`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    console.log('🚫 Upload cancelled successfully');
                } else {
                    console.warn('⚠️ Failed to cancel upload on server');
                }
            } catch (error) {
                console.warn('⚠️ Error cancelling upload:', error);
            }
        }
        
        this.uploadId = null;
        this.file = null;
        this.uploadedBytes = 0;
    }
    
    /**
     * Resume an interrupted upload
     */
    async resumeUpload(uploadId) {
        this.uploadId = uploadId;
        
        try {
            // Get current status
            const status = await this.getStatus();
            
            if (status.is_complete) {
                throw new Error('Upload is already complete');
            }
            
            this.totalSize = status.total_size;
            this.uploadedBytes = status.bytes_received;
            
            console.log(`🔄 Resuming upload: ${uploadId} (${status.progress.toFixed(1)}% complete)`);
            
            // Continue uploading missing chunks
            await this.uploadMissingChunks(status.received_ranges);
            
            // Complete the upload
            await this.completeUpload();
            
        } catch (error) {
            console.error('❌ Resume failed:', error);
            this.onError(error);
        }
    }
    
    /**
     * Upload missing chunks for resume functionality
     */
    async uploadMissingChunks(receivedRanges) {
        // Calculate missing ranges
        const missingRanges = this.calculateMissingRanges(receivedRanges);
        
        if (missingRanges.length === 0) {
            console.log('✅ No missing chunks to upload');
            return;
        }
        
        console.log(`📦 Uploading ${missingRanges.length} missing ranges`);
        
        // Upload missing ranges in parallel
        const workers = [];
        let rangeIndex = 0;
        
        for (let i = 0; i < this.MAX_PARALLEL; i++) {
            workers.push(this.uploadMissingRangeWorker(missingRanges, () => rangeIndex++));
        }
        
        await Promise.all(workers);
    }
    
    /**
     * Worker for uploading missing ranges
     */
    async uploadMissingRangeWorker(missingRanges, getNextIndex) {
        while (true) {
            if (this.aborted) {
                return;
            }
            
            const index = getNextIndex();
            if (index >= missingRanges.length) {
                return;
            }
            
            const [start, end] = missingRanges[index];
            
            try {
                await this.uploadChunk(start, end, index, missingRanges.length);
                this.uploadedBytes += (end - start + 1);
                this.updateProgress();
                
            } catch (error) {
                console.error(`❌ Failed to upload missing range [${start}-${end}]:`, error);
                throw error;
            }
        }
    }
    
    /**
     * Calculate missing byte ranges
     */
    calculateMissingRanges(receivedRanges) {
        if (!receivedRanges || receivedRanges.length === 0) {
            return [[0, this.totalSize - 1]];
        }
        
        const missing = [];
        let pos = 0;
        
        // Sort received ranges
        const sorted = receivedRanges.sort((a, b) => a[0] - b[0]);
        
        for (const [start, end] of sorted) {
            if (pos < start) {
                missing.push([pos, start - 1]);
            }
            pos = Math.max(pos, end + 1);
        }
        
        if (pos < this.totalSize) {
            missing.push([pos, this.totalSize - 1]);
        }
        
        return missing;
    }
}

// Export for use in main app
window.StreamingUploader = StreamingUploader;