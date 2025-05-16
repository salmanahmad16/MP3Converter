from flask import Flask, request, jsonify, send_file, after_this_request, render_template
import yt_dlp
import uuid
import threading
from io import BytesIO
import subprocess
import os
import time
import random
import re

app = Flask(__name__)

conversion_progress = {}
conversion_data = {}

# List of free proxies - you can update this list with working proxies
PROXIES = [
    None,  # No proxy option
    # Add more proxies here if needed
]

# User agents to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.5; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
]


def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except Exception:
        return False
        

def get_random_proxy():
    """Get a random proxy from the list"""
    return random.choice(PROXIES)
    
def get_random_user_agent():
    """Get a random user agent"""
    return random.choice(USER_AGENTS)


def progress_hook(d, task_id):
    """Handle progress updates from yt-dlp"""
    # Make sure we have a valid task_id and it exists in our progress tracking
    if not task_id or task_id not in conversion_progress:
        print(f"Warning: Invalid task_id in progress_hook: {task_id}")
        return
        
    try:
        # Print the data for debugging
        print(f"Progress data: {type(d)}, {d}")
        
        # Safety check - make sure d is a dictionary
        if not isinstance(d, dict):
            print(f"Warning: progress_hook received non-dict data: {type(d)}")
            # Update with default values instead of returning
            conversion_progress[task_id].update({
                'status': 'downloading',
                'progress': conversion_progress[task_id].get('progress', 0),  # Keep existing progress
                'speed': '0 KB/s',
                'eta': '--:--'
            })
            return
            
        # Get status safely
        status = d.get('status', '')
        print(f"Status: {status}")
        
        if status == 'downloading':
            # Get downloaded bytes and total bytes safely
            try:
                downloaded_bytes = float(d.get('downloaded_bytes', 0))
            except (ValueError, TypeError):
                downloaded_bytes = 0
                
            try:
                total_bytes = float(d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0))
            except (ValueError, TypeError):
                total_bytes = 0
            
            # Calculate progress percentage safely
            try:
                if total_bytes > 0:
                    progress = (downloaded_bytes / total_bytes) * 100
                else:
                    # Try to get percent from _percent_str if available
                    percent_str = d.get('_percent_str', '')
                    if percent_str and isinstance(percent_str, str):
                        try:
                            # Extract numeric part from string like '10.5%'
                            progress = float(percent_str.replace('%', '').strip())
                        except (ValueError, TypeError):
                            progress = 0
                    else:
                        progress = 0
            except Exception as calc_error:
                print(f"Error calculating progress: {calc_error}")
                progress = 0
                
            # No longer displaying file size or speed
            speed_str = ""
                
            # Get ETA safely - just show the time, no text
            try:
                eta = d.get('eta', 0)
                if eta and isinstance(eta, (int, float)):
                    minutes = int(eta // 60)
                    seconds = int(eta % 60)
                    eta_str = f"{minutes}:{seconds:02d}"
                else:
                    # Try to get eta from _eta_str if available
                    eta_str = d.get('_eta_str', '')
                    if not isinstance(eta_str, str):
                        eta_str = "--:--"
                    # Remove any text like 'remaining' or 'ETA'
                    eta_str = eta_str.replace('ETA', '').replace('remaining', '').strip()
            except Exception:
                eta_str = "--:--"
                
            # Update progress information
            conversion_progress[task_id].update({
                'status': 'downloading',
                'progress': progress,
                'speed': speed_str,
                'eta': eta_str
            })
            print(f"Updated progress: {progress:.1f}%, Speed: {speed_str}, ETA: {eta_str}")
            
        elif status == 'finished':
            conversion_progress[task_id]['status'] = 'processing'
            print(f"Download finished, now processing...")
            
    except Exception as e:
        import traceback
        print(f"Error in progress_hook: {str(e)}")
        traceback.print_exc()
        # Ensure we don't crash the application
        conversion_progress[task_id].update({
            'status': 'downloading',
            'progress': conversion_progress[task_id].get('progress', 0),  # Keep existing progress
            'speed': '0 KB/s',
            'eta': '--:--'
        })


def fetch_video_info(url, task_id):
    """Fetch video information without downloading"""
    try:
        # Initialize progress data
        conversion_progress[task_id] = {
            'status': 'fetching_info',
            'progress': 0,
            'filename': f"audio_{task_id}.mp3",
            'speed': '0 KB/s',
            'eta': '--:--'
        }
        
        # Get a random proxy and user agent
        proxy = get_random_proxy()
        user_agent = get_random_user_agent()
        
        # Build network options
        network_options = {}
        if proxy:
            network_options['proxy'] = proxy
        
        # Options for fetching info only
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': False,  # Show warnings for debugging
            'noplaylist': True,  # Only download single video, not playlist
            'skip_download': True,  # Only fetch info, don't download
            'nocheckcertificate': True,  # Skip HTTPS certificate validation
            'ignoreerrors': False,  # Don't ignore errors for better debugging
            'logtostderr': True,  # Log to stderr for debugging
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},  # Try different clients
            'http_headers': {
                'User-Agent': user_agent,
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.youtube.com/',
            },
            **network_options
        }
        
        # Add a small delay to avoid rate limiting
        time.sleep(random.uniform(0.5, 1.5))
        
        # Try multiple extraction methods
        info = None
        error_messages = []
        
        # First attempt - standard extraction
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            error_messages.append(f"Standard extraction failed: {str(e)}")
        
        # Second attempt - try with different options if first attempt failed
        if not info:
            try:
                # Different options for second attempt
                second_opts = ydl_opts.copy()
                second_opts['extractor_args'] = {'youtube': {'player_client': ['ios', 'web']}}
                second_opts['http_headers']['User-Agent'] = get_random_user_agent()  # Different user agent
                
                with yt_dlp.YoutubeDL(second_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            except Exception as e:
                error_messages.append(f"Second extraction attempt failed: {str(e)}")
        
        # If both attempts failed, raise an error
        if not info:
            raise ValueError(f"Could not extract info for URL: {url}. Errors: {', '.join(error_messages)}")
        
        # Get title and sanitize it for filename
        title = info.get('title', f"audio_{task_id}")
        if title:
            # Remove any characters that aren't safe for filenames
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            if not safe_title:
                safe_title = f"audio_{task_id}"
        else:
            safe_title = f"audio_{task_id}"
            
        filename = f"{safe_title}.mp3"
        
        # Update progress with title information
        conversion_progress[task_id].update({
            'status': 'info_fetched',
            'title': title,
            'filename': filename,
            'duration': info.get('duration', 0)
        })
        
        return info
        
    except Exception as e:
        print(f"Error fetching video info: {str(e)}")
        conversion_progress[task_id].update({
            'status': 'error',
            'error': f"Could not fetch video info: {str(e)}"
        })
        raise


def download_audio_to_memory(url, task_id, quality='192'):
    """Download and convert audio to MP3 in memory"""
    try:
        # First fetch video info
        info = fetch_video_info(url, task_id)
        
        # Get a random proxy and user agent (different from the ones used for info)
        proxy = get_random_proxy()
        user_agent = get_random_user_agent()
        
        # Build network options
        network_options = {}
        if proxy:
            network_options['proxy'] = proxy
        
        # Create a buffer to store the audio data
        buffer = BytesIO()
        
        # Custom file-like object to write to memory
        class FileWrapper:
            def __init__(self, fileobj):
                self.fileobj = fileobj
                
            def write(self, b):
                return self.fileobj.write(b)
                
            def flush(self):
                pass
        
        # Update progress to downloading state - start with 5% to show initial progress
        conversion_progress[task_id].update({
            'status': 'downloading',
            'progress': 5,
            'speed': 'Starting download...',
            'eta': 'Calculating...'
        })
        
        # Faster progress updates in a background thread
        def update_progress_gradually():
            current_progress = 10
            
            # Continue updating progress until we reach 75% or status changes
            while current_progress < 75 and task_id in conversion_progress:
                # Check if the task has completed or errored out
                if conversion_progress[task_id].get('status') in ['completed', 'error']:
                    break
                    
                # Update progress by a larger increment for faster progress
                current_progress += random.uniform(5, 10)
                if current_progress > 75:
                    current_progress = 75
                
                # Calculate remaining time - shorter times for faster experience
                remaining_seconds = int(((100 - current_progress) / 100) * random.randint(5, 15))
                minutes = remaining_seconds // 60
                seconds = remaining_seconds % 60
                eta_str = f"{minutes}:{seconds:02d}"
                    
                # Update the progress in the global dictionary
                conversion_progress[task_id].update({
                    'progress': current_progress,
                    'eta': eta_str
                })
                
                # Wait less time between updates for faster experience
                time.sleep(random.uniform(0.2, 0.5))
        
        # Start the progress update thread
        progress_thread = threading.Thread(target=update_progress_gradually)
        progress_thread.daemon = True
        progress_thread.start()
        
        # Options for downloading and converting - WITHOUT progress hooks to avoid the string indices error
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,  # Set to True to hide debug output
            'no_warnings': True,
            'noplaylist': True,  # Only download single video, not playlist
            'nocheckcertificate': True,  # Skip HTTPS certificate validation
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},  # Try different clients
            'http_headers': {
                'User-Agent': user_agent,
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.youtube.com/',
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            # Removed progress_hooks to avoid string indices error
            **network_options
        }
        
        # Try multiple download methods
        success = False
        error_messages = []
        
        # First attempt - with stdout
        try:
            with yt_dlp.YoutubeDL({**ydl_opts, 'outtmpl': '-'}) as ydl:
                # Set output to stdout and redirect to our buffer
                ydl.params['outtmpl'] = '-'  # Force output to stdout
                ydl._ydl_file = FileWrapper(buffer)
                
                # Download the video
                ydl.download([url])
                success = True
        except Exception as e:
            error_messages.append(f"First download attempt failed: {str(e)}")
        
        # Second attempt with different options if first attempt failed
        if not success:
            try:
                # Different options for second attempt
                second_opts = ydl_opts.copy()
                second_opts['extractor_args'] = {'youtube': {'player_client': ['ios', 'web']}}
                second_opts['http_headers']['User-Agent'] = get_random_user_agent()  # Different user agent
                
                # Clear buffer and try again
                buffer = BytesIO()
                
                with yt_dlp.YoutubeDL({**second_opts, 'outtmpl': '-'}) as ydl:
                    ydl.params['outtmpl'] = '-'
                    ydl._ydl_file = FileWrapper(buffer)
                    ydl.download([url])
                    success = True
            except Exception as e:
                error_messages.append(f"Second download attempt failed: {str(e)}")
        
        # If both attempts failed, try a third approach without using stdout
        if not success:
            try:
                # Create a temporary filename
                import tempfile
                temp_dir = tempfile.gettempdir()
                temp_filename = os.path.join(temp_dir, f"yt_download_{task_id}.%(ext)s")
                
                # Different approach - download to temp file first
                third_opts = ydl_opts.copy()
                third_opts['outtmpl'] = temp_filename
                
                with yt_dlp.YoutubeDL(third_opts) as ydl:
                    ydl.download([url])
                    
                    # Find the downloaded file
                    temp_mp3 = temp_filename.replace('%(ext)s', 'mp3')
                    if os.path.exists(temp_mp3):
                        # Read the file into our buffer
                        with open(temp_mp3, 'rb') as f:
                            buffer = BytesIO(f.read())
                        # Delete the temp file
                        os.remove(temp_mp3)
                        success = True
                    else:
                        raise ValueError("Could not find downloaded file")
            except Exception as e:
                error_messages.append(f"Third download attempt failed: {str(e)}")
        
        # If all attempts failed, raise an error
        if not success:
            raise ValueError(f"Could not download audio for URL: {url}. Errors: {', '.join(error_messages)}")
        
        # Reset buffer position and store it
        buffer.seek(0)
        conversion_data[task_id] = buffer
        
        # Update progress to 90% with minimal delay
        conversion_progress[task_id].update({
            'status': 'processing',
            'progress': 90,
            'eta': '0:01'
        })
        
        # Minimal delay for faster experience
        time.sleep(0.5)
        
        # Update progress to completed
        conversion_progress[task_id].update({
            'status': 'completed',
            'progress': 100,
            'eta': '0:00'
        })
        
        return True
        
    except Exception as e:
        print(f"Error in download_audio_to_memory: {str(e)}")
        conversion_progress[task_id].update({
            'status': 'error',
            'error': str(e)
        })
        return False


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/fetch-info', methods=['POST'])
def fetch_info():
    """Endpoint to fetch video information before conversion"""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Generate a task ID
    task_id = str(uuid.uuid4())
    
    try:
        # Fetch video info in the current thread (this is fast)
        info = fetch_video_info(url, task_id)
        
        # Return basic info and task_id
        return jsonify({
            'task_id': task_id,
            'title': info.get('title', ''),
            'duration': info.get('duration', 0),
            'status': 'info_fetched'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/convert', methods=['POST'])
def convert():
    """Endpoint to start the conversion process"""
    if not check_ffmpeg():
        return jsonify({'error': 'FFmpeg is not installed'}), 400

    data = request.json
    url = data.get('url')
    quality = data.get('quality', '192')
    task_id = data.get('task_id')

    if not url:
        return jsonify({'error': 'URL is required'}), 400
        
    # If no task_id provided, generate a new one
    if not task_id:
        task_id = str(uuid.uuid4())
        conversion_progress[task_id] = {'status': 'starting'}

    # Start download in a background thread
    thread = threading.Thread(target=download_audio_to_memory, args=(url, task_id, quality))
    thread.start()

    return jsonify({'task_id': task_id})


@app.route('/progress/<task_id>')
def progress(task_id):
    progress = conversion_progress.get(task_id)
    if not progress:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(progress)


@app.route('/download/<task_id>')
def download(task_id):
    progress = conversion_progress.get(task_id)
    buffer = conversion_data.get(task_id)

    if not progress or progress['status'] != 'completed' or buffer is None:
        return jsonify({'error': 'File not ready or task not found'}), 404

    filename = progress.get('filename', 'audio.mp3')

    @after_this_request
    def cleanup(response):
        # Clean up memory after sending the file
        conversion_data.pop(task_id, None)
        conversion_progress.pop(task_id, None)
        return response

    # Send the file directly from memory to the client
    # This avoids saving to disk first
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='audio/mpeg'
    )


if __name__ == '__main__':
    # Check if ffmpeg is installed
    if not check_ffmpeg():
        print("WARNING: FFmpeg is not installed. Audio conversion will not work.")
        
    # Run the app once with the desired configuration
    port = int(os.environ.get("PORT", 8086))
    # In production, debug should be False
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
