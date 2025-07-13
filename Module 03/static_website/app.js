// Configuration - Update with your Azure API Management URL
const API_BASE_URL = 'https://your-api-management-name.azure-api.net/your-api-path';

// Global variables
let currentFiles = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    setupEventListeners();
    
    // Load files on page load
    loadAllFiles();
});

function setupEventListeners() {
    // File input change event
    document.getElementById('fileInput').addEventListener('change', handleFileUpload);
    
    // Drag and drop events
    const uploadSection = document.querySelector('.upload-section');
    uploadSection.addEventListener('dragover', handleDragOver);
    uploadSection.addEventListener('drop', handleDrop);
    uploadSection.addEventListener('dragleave', handleDragLeave);
    
    // Form select styling
    const selects = document.querySelectorAll('select');
    selects.forEach(select => {
        select.style.width = '100%';
        select.style.padding = '12px';
        select.style.border = '2px solid #ddd';
        select.style.borderRadius = '5px';
        select.style.fontSize = '16px';
    });
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#667eea';
    e.currentTarget.style.backgroundColor = '#f8f9ff';
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#ddd';
    e.currentTarget.style.backgroundColor = '';
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#ddd';
    e.currentTarget.style.backgroundColor = '';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

function handleFileUpload(e) {
    const file = e.target.files[0];
    if (file) {
        uploadFile(file);
    }
}

async function uploadFile(file) {
    const userId = document.getElementById('userId').value.trim();
    
    if (!userId) {
        showStatus('uploadStatus', 'Please enter a User ID', 'error');
        return;
    }
    
    // Show loading
    showLoading('uploadLoading', true);
    hideStatus('uploadStatus');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/media/upload_media_file?userId=${encodeURIComponent(userId)}`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('uploadStatus', result.message, 'success');
            // Clear file input
            document.getElementById('fileInput').value = '';
            // Reload file list
            setTimeout(() => loadAllFiles(), 1000);
        } else {
            showStatus('uploadStatus', result.message || 'Upload failed', 'error');
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        showStatus('uploadStatus', 'Upload failed: ' + error.message, 'error');
    } finally {
        showLoading('uploadLoading', false);
    }
}

async function loadAllFiles() {
    const userId = document.getElementById('userId').value.trim();
    
    if (!userId) {
        showStatus('fileStatus', 'Please enter a User ID', 'error');
        return;
    }
    
    showLoading('fileLoading', true);
    hideStatus('fileStatus');
    
    try {
        const response = await fetch(`${API_BASE_URL}/media/get_media_metadata?userId=${encodeURIComponent(userId)}`);
        const result = await response.json();
        
        if (result.success) {
            currentFiles = result.data.files || [];
            displayFiles(currentFiles);
            showStatus('fileStatus', `Loaded ${currentFiles.length} files`, 'success');
        } else {
            showStatus('fileStatus', result.message || 'Failed to load files', 'error');
            currentFiles = [];
            displayFiles([]);
        }
        
    } catch (error) {
        console.error('Load files error:', error);
        showStatus('fileStatus', 'Failed to load files: ' + error.message, 'error');
        currentFiles = [];
        displayFiles([]);
    } finally {
        showLoading('fileLoading', false);
    }
}

async function searchFiles() {
    const userId = document.getElementById('userId').value.trim();
    
    if (!userId) {
        showStatus('fileStatus', 'Please enter a User ID', 'error');
        return;
    }
    
    // Get filter values
    const fileType = document.getElementById('fileTypeFilter').value;
    const tag = document.getElementById('tagFilter').value.trim();
    const fromDate = document.getElementById('fromDate').value;
    const toDate = document.getElementById('toDate').value;
    
    // Build query parameters
    const params = new URLSearchParams();
    params.append('userId', userId);
    
    if (fileType) params.append('fileType', fileType);
    if (tag) params.append('tag', tag);
    if (fromDate) params.append('fromDate', fromDate + ':00.000Z');
    if (toDate) params.append('toDate', toDate + ':59.999Z');
    
    showLoading('fileLoading', true);
    hideStatus('fileStatus');
    
    try {
        const response = await fetch(`${API_BASE_URL}/media/search_media?${params.toString()}`);
        const result = await response.json();
        
        if (result.success) {
            currentFiles = result.data.files || [];
            displayFiles(currentFiles);
            showStatus('fileStatus', result.message, 'success');
        } else {
            showStatus('fileStatus', result.message || 'Search failed', 'error');
            currentFiles = [];
            displayFiles([]);
        }
        
    } catch (error) {
        console.error('Search error:', error);
        showStatus('fileStatus', 'Search failed: ' + error.message, 'error');
        currentFiles = [];
        displayFiles([]);
    } finally {
        showLoading('fileLoading', false);
    }
}

function displayFiles(files) {
    const fileList = document.getElementById('fileList');
    
    if (files.length === 0) {
        fileList.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">No files found</p>';
        return;
    }
    
    fileList.innerHTML = files.map(file => `
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">${escapeHtml(file.file_name)}</div>
                <div class="file-details">
                    Type: ${file.file_type} | Size: ${formatFileSize(file.file_size)} | 
                    Uploaded: ${formatDate(file.upload_date)}
                </div>
                <div class="metadata-details" id="metadata-${file.id}">
                    <div class="metadata-item">
                        <span class="metadata-label">File ID:</span>
                        <span class="metadata-value">${file.id}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">MIME Type:</span>
                        <span class="metadata-value">${file.mime_type}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Blob URL:</span>
                        <span class="metadata-value"><a href="${file.blob_url}" target="_blank">View File</a></span>
                    </div>
                    ${file.tags && file.tags.length > 0 ? `
                    <div class="metadata-item">
                        <span class="metadata-label">Tags:</span>
                        <span class="metadata-value">${file.tags.join(', ')}</span>
                    </div>
                    ` : ''}
                    ${Object.keys(file.extracted_metadata || {}).length > 0 ? `
                    <div class="metadata-item">
                        <span class="metadata-label">Extracted Metadata:</span>
                        <div class="metadata-value">
                            <pre style="background: #f1f1f1; padding: 10px; border-radius: 5px; font-size: 12px; max-height: 200px; overflow-y: auto;">${JSON.stringify(file.extracted_metadata, null, 2)}</pre>
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
            <div class="file-actions">
                <button class="btn" onclick="toggleMetadata('${file.id}')">Details</button>
                <button class="btn btn-danger" onclick="deleteFile('${file.id}', '${escapeHtml(file.file_name)}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function toggleMetadata(fileId) {
    const metadataDiv = document.getElementById(`metadata-${fileId}`);
    metadataDiv.classList.toggle('show');
}

async function deleteFile(fileId, fileName) {
    const userId = document.getElementById('userId').value.trim();
    
    if (!userId) {
        showStatus('fileStatus', 'Please enter a User ID', 'error');
        return;
    }
    
    if (!confirm(`Are you sure you want to delete "${fileName}"?`)) {
        return;
    }
    
    try {
        const deleteUrl = `${API_BASE_URL}/media/delete_media_file?fileId=${encodeURIComponent(fileId)}&userId=${encodeURIComponent(userId)}`;
        
        const response = await fetch(deleteUrl, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('fileStatus', result.message, 'success');
            // Remove from current files and refresh display
            currentFiles = currentFiles.filter(file => file.id !== fileId);
            displayFiles(currentFiles);
        } else {
            showStatus('fileStatus', result.message || 'Delete failed', 'error');
        }
        
    } catch (error) {
        console.error('Delete error:', error);
        showStatus('fileStatus', 'Delete failed: ' + error.message, 'error');
    }
}

// Utility functions
function showStatus(elementId, message, type) {
    const statusElement = document.getElementById(elementId);
    statusElement.textContent = message;
    statusElement.className = `status ${type}`;
    statusElement.style.display = 'block';
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => hideStatus(elementId), 5000);
    }
}

function hideStatus(elementId) {
    const statusElement = document.getElementById(elementId);
    statusElement.style.display = 'none';
}

function showLoading(elementId, show) {
    const loadingElement = document.getElementById(elementId);
    loadingElement.style.display = show ? 'block' : 'none';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    try {
        return new Date(dateString).toLocaleString();
    } catch {
        return dateString;
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}
