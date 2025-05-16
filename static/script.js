document.addEventListener('DOMContentLoaded', function() {
    const convertBtn = document.getElementById('convert-btn');
    const youtubeUrl = document.getElementById('youtube-url');
    const progressContainer = document.querySelector('.progress-container');
    const downloadComplete = document.querySelector('.download-complete');
    const videoTitle = document.getElementById('video-title');
    const downloadStatus = document.getElementById('download-status');
    const progressFill = document.getElementById('progress-fill');
    const progressPercent = document.getElementById('progress-percent');
    const downloadSpeed = document.getElementById('download-speed');
    const timeRemaining = document.getElementById('time-remaining');
    const downloadLink = document.getElementById('download-link');
    const qualitySelect = document.getElementById('quality-select');

    // Event listeners
    convertBtn.addEventListener('click', convertToMp3);
    youtubeUrl.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') convertToMp3();
    });

    // Main conversion function
    async function convertToMp3() {
        const url = youtubeUrl.value.trim();

        if (!url) {
            showError('Please enter a YouTube URL');
            return;
        }

        if (!isValidYouTubeUrl(url)) {
            showError('Please enter a valid YouTube URL');
            return;
        }

        // UI updates
        progressContainer.classList.remove('hidden');
        downloadComplete.classList.add('hidden');
        videoTitle.textContent = "Fetching video info...";
        downloadStatus.textContent = "Connecting to YouTube";
        convertBtn.disabled = true;

        try {
            // Start the conversion process
            const response = await startConversion(url);

            if (response.error) {
                showError(response.error);
                return;
            }

            // Update UI with video info
            videoTitle.textContent = response.title || "YouTube Audio";
            downloadStatus.textContent = "Starting download...";

            // Poll for progress updates
            await trackProgress(response.task_id);

        } catch (error) {
            showError('An error occurred during conversion');
            console.error('Conversion error:', error);
        } finally {
            convertBtn.disabled = false;
        }
    }

    // Start the conversion process
    async function startConversion(url) {
        const quality = qualitySelect.value;
        const response = await fetch('/convert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                quality: quality
            })
        });
        return await response.json();
    }

    // Track conversion progress
    async function trackProgress(taskId) {
        let progressData;

        do {
            // Get progress updates
            const response = await fetch(`/progress/${taskId}`);
            progressData = await response.json();

            if (progressData.error) {
                showError(progressData.error);
                return;
            }

            // Update progress UI
            updateProgressUI(progressData);

            // Wait before polling again
            await new Promise(resolve => setTimeout(resolve, 1000));

        } while (progressData.status !== 'completed');

        // Conversion complete
        downloadCompleteHandler(progressData);
    }

    // Update progress UI
    function updateProgressUI(data) {
        const progress = data.progress || 0;
        progressFill.style.width = `${progress}%`;
        progressPercent.textContent = `${Math.round(progress)}%`;

        // Update status based on progress
        if (progress < 30) {
            downloadStatus.textContent = "Downloading audio stream...";
        } else if (progress < 70) {
            downloadStatus.textContent = "Converting to MP3...";
        } else {
            downloadStatus.textContent = "Finalizing...";
        }

        // Update stats if available
        if (data.speed) {
            downloadSpeed.textContent = `${(data.speed / 1024).toFixed(1)} KB/s`;
        }

        if (data.eta) {
            timeRemaining.textContent = `${data.eta} remaining`;
        }
    }

    // Handle download completion
    function downloadCompleteHandler(data) {
        progressContainer.classList.add('hidden');
        downloadComplete.classList.remove('hidden');

        if (data.filename) {
            downloadLink.href = `/download/${encodeURIComponent(data.filename)}`;
            downloadLink.download = data.filename;
            videoTitle.textContent = data.title || "Your Audio File";
        } else {
            showError('Conversion completed but no file was generated');
        }
    }

    // Helper functions
    function isValidYouTubeUrl(url) {
        const pattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$/;
        return pattern.test(url);
    }

    function showError(message) {
        downloadStatus.textContent = message;
        downloadStatus.style.color = '#ea4335';
        setTimeout(() => {
            downloadStatus.style.color = '';
        }, 3000);
    }
});