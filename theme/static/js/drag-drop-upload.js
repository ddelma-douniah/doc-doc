/**
 * Drag and Drop File Upload
 * Enhances file upload UX with drag-and-drop functionality
 */

(function() {
    'use strict';

    // Initialize drag and drop for all file upload forms
    function initializeDragDrop() {
        const uploadForms = document.querySelectorAll('form[enctype="multipart/form-data"]');

        uploadForms.forEach(form => {
            const fileInput = form.querySelector('input[type="file"][name="file"]');
            if (!fileInput) return;

            // Create drag-drop zone
            const dropZone = createDropZone();
            form.parentNode.insertBefore(dropZone, form);

            // Hide the original form initially (show on demand)
            const uploadButton = form.querySelector('button[type="submit"]');
            if (uploadButton) {
                uploadButton.classList.add('hidden');
            }

            // Drag and drop event handlers
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, preventDefaults, false);
                document.body.addEventListener(eventName, preventDefaults, false);
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, () => highlight(dropZone), false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, () => unhighlight(dropZone), false);
            });

            dropZone.addEventListener('drop', (e) => handleDrop(e, fileInput, form), false);

            // Click to browse
            dropZone.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', () => handleFiles(fileInput.files, form));
        });
    }

    function createDropZone() {
        const zone = document.createElement('div');
        zone.className = 'drag-drop-zone bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-all mb-4';
        zone.innerHTML = `
            <div class="flex flex-col items-center">
                <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                    <i class="fas fa-cloud-upload-alt text-3xl text-blue-600"></i>
                </div>
                <p class="text-lg font-medium text-gray-900 mb-2">
                    Drag and drop your files here
                </p>
                <p class="text-sm text-gray-500 mb-4">
                    or click to browse from your computer
                </p>
                <p class="text-xs text-gray-400">
                    Maximum file size: 10 MB
                </p>
            </div>
        `;
        return zone;
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(dropZone) {
        dropZone.classList.add('border-blue-500', 'bg-blue-50');
    }

    function unhighlight(dropZone) {
        dropZone.classList.remove('border-blue-500', 'bg-blue-50');
    }

    function handleDrop(e, fileInput, form) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        handleFiles(files, form);
    }

    function handleFiles(files, form) {
        if (files.length === 0) return;

        // Show file info
        const dropZone = form.previousElementSibling;
        const fileInfo = document.createElement('div');
        fileInfo.className = 'mt-4 p-4 bg-white border border-gray-200 rounded-lg';

        const file = files[0]; // Only handle first file for now
        fileInfo.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <i class="fas fa-file text-2xl text-blue-600"></i>
                    <div>
                        <p class="text-sm font-medium text-gray-900">${file.name}</p>
                        <p class="text-xs text-gray-500">${formatBytes(file.size)}</p>
                    </div>
                </div>
                <button type="button" onclick="this.closest('form').previousElementSibling.querySelector('.file-info')?.remove(); this.closest('form').querySelector('input[type=file]').value = '';" class="text-red-600 hover:text-red-900">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <button type="submit" class="mt-4 w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors">
                <i class="fas fa-upload mr-2"></i>
                Upload File
            </button>
        `;
        fileInfo.classList.add('file-info');

        // Remove any existing file info
        dropZone.querySelector('.file-info')?.remove();
        dropZone.appendChild(fileInfo);

        // Handle form submission
        const submitBtn = fileInfo.querySelector('button[type="submit"]');
        submitBtn.addEventListener('click', (e) => {
            e.preventDefault();
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Uploading...';
            form.submit();
        });
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDragDrop);
    } else {
        initializeDragDrop();
    }
})();
