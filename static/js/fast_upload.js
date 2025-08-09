/**
 * Fast HTTP Chunked Upload Client
 * High-performance file upload without WebSocket overhead
 */

class FastUploader {
    constructor() {
        this.uploadId = null;
        this.currentFile = null;
        this.uploadedChunks = new Set();
        this.totalChunks = 0;
        this.startTime = null;
        this.progressCallback = null;
        this.completionCallback = null;
        this.errorCallback = null;
        this.isUploading = false;
        this.maxConcurrentUploads = 4; // Parallel chunk uploads
    }

    /**
     * Start chunked upload with progress callbacks
     */
    async startUpload(file, options = {}) {
        if (this.isUploading) {
            throw new Error('Upload already in progress');
        }

        this.currentFile = file;
        this.progressCallback = options.onProgress || (() => {});
        this.completionCallback = options.onComplete || (() => {});
        this.errorCallback = options.onError || (() => {});
        this.maxConcurrentUploads = options.maxConcurrent || 4;

        try {
            this.isUploading = true;
            this.startTime = Date.now();
            
            // Dynamic chunk size for optimal performance
            const CHUNK_SIZE = this.getOptimalChunkSize(file.size);
            this.totalChunks = Math.ceil(file.size / CHUNK_SIZE);
            
            console.log(`🚀 Fast HTTP Upload: ${file.name} (${(file.size / (1024**2)).toFixed(1)}MB)`);
            console.log(`📦 Using ${(CHUNK_SIZE / (1024**2)).toFixed(1)}MB chunks (${this.totalChunks} total)`);

            // Initialize upload session
            await this.initializeUpload(file, CHUNK_SIZE);
            
            // Upload chunks in parallel
            await this.uploadChunksParallel(file, CHUNK_SIZE);
            
        } catch (error) {
            this.isUploading = false;
            this.errorCallback(error);
            throw error;
        }
    }

    /**
     * Get optimal chunk size based on file size
     */
    getOptimalChunkSize(fileSize) {
        if (fileSize < 50 * 1024 * 1024) {        // < 50MB
            return 2 * 1024 * 1024;               // 2MB chunks
        } else if (fileSize < 200 * 1024 * 1024) { // < 200MB
            return 5 * 1024 * 1024;               // 5MB chunks  
        } else if (fileSize < 1024 * 1024 * 1024) { // < 1GB
            return 10 * 1024 * 1024;              // 10MB chunks
        } else {                                   // 1GB+
            return 20 * 1024 * 1024;              // 20MB chunks
        }
    }

    /**
     * Initialize upload session on server
     */
    async initializeUpload(file, chunkSize) {
        const response = await fetch('/upload/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: file.name,
                file_size: file.size,
                total_chunks: this.totalChunks,
                chunk_size: chunkSize
            })
        });

        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error);
        }

        this.uploadId = result.upload_id;
        console.log(`✅ Upload session created: ${this.uploadId}`);
    }

    /**
     * Upload chunks in parallel for maximum speed
     */
    async uploadChunksParallel(file, chunkSize) {
        const chunks = [];
        
        // Create chunk info array
        for (let i = 0; i < this.totalChunks; i++) {
            const start = i * chunkSize;
            const end = Math.min(start + chunkSize, file.size);
            chunks.push({
                index: i,
                start: start,
                end: end,
                blob: file.slice(start, end)
            });
        }

        // Upload chunks in parallel batches
        const batchSize = this.maxConcurrentUploads;
        
        for (let i = 0; i < chunks.length; i += batchSize) {
            const batch = chunks.slice(i, i + batchSize);
            const promises = batch.map(chunk => this.uploadSingleChunk(chunk));
            
            // Wait for batch to complete
            const results = await Promise.allSettled(promises);
            
            // Check for failures
            const failures = results.filter(r => r.status === 'rejected');
            if (failures.length > 0) {
                throw new Error(`Failed to upload ${failures.length} chunks in batch`);
            }

            // Update progress after each batch
            this.updateProgress();
        }
    }

    /**
     * Upload a single chunk
     */
    async uploadSingleChunk(chunk) {
        const formData = new FormData();
        formData.append('chunk', chunk.blob);

        const response = await fetch(`/upload/chunk/${this.uploadId}/${chunk.index}`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (!result.success) {
            throw new Error(`Chunk ${chunk.index} upload failed: ${result.error}`);
        }

        this.uploadedChunks.add(chunk.index);
        
        // Check if upload complete
        if (result.complete) {
            this.isUploading = false;
            const totalTime = (Date.now() - this.startTime) / 1000;
            const avgSpeed = (this.currentFile.size / totalTime) / (1024**2);
            
            console.log(`✅ Upload completed in ${totalTime.toFixed(1)}s (${avgSpeed.toFixed(1)}MB/s)`);
            
            this.completionCallback({
                filename: this.currentFile.name,
                file_path: result.file_path,
                upload_time: totalTime,
                average_speed: avgSpeed,
                total_size: this.currentFile.size
            });
        }

        return result;
    }

    /**
     * Update progress callback
     */
    updateProgress() {
        const progress = (this.uploadedChunks.size / this.totalChunks) * 100;
        const elapsed = (Date.now() - this.startTime) / 1000;
        const bytesUploaded = this.uploadedChunks.size * (this.currentFile.size / this.totalChunks);
        const currentSpeed = bytesUploaded / elapsed / (1024**2);

        this.progressCallback({
            progress: progress,
            bytes_uploaded: bytesUploaded,
            total_size: this.currentFile.size,
            upload_speed: currentSpeed,
            chunks_uploaded: this.uploadedChunks.size,
            total_chunks: this.totalChunks,
            elapsed_time: elapsed
        });

        console.log(`📊 Progress: ${progress.toFixed(1)}% (${currentSpeed.toFixed(1)}MB/s)`);
    }

    /**
     * Cancel active upload
     */
    async cancelUpload() {
        if (!this.uploadId || !this.isUploading) {
            return;
        }

        try {
            await fetch(`/upload/cancel/${this.uploadId}`, {
                method: 'POST'
            });
            
            this.isUploading = false;
            console.log('❌ Upload cancelled');
            
        } catch (error) {
            console.error('Error cancelling upload:', error);
        }
    }

    /**
     * Get current upload status
     */
    async getStatus() {
        if (!this.uploadId) {
            return null;
        }

        try {
            const response = await fetch(`/upload/status/${this.uploadId}`);
            const result = await response.json();
            return result.success ? result : null;
            
        } catch (error) {
            console.error('Error getting upload status:', error);
            return null;
        }
    }
}

// Export for use in main application
window.FastUploader = FastUploader;