# YouTube to MP3 Converter

A web application that converts YouTube videos to MP3 files with a clean, modern interface.

## Features

- Convert YouTube videos to MP3 files
- Select audio quality (64kbps, 128kbps, or 192kbps)
- Simple, ad-free interface
- Fast conversion process
- Direct download of converted files
- Docker support for easy deployment

## Running with Docker (Recommended)

The easiest way to run this application is using Docker, which handles all dependencies and environment setup automatically.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

### Running the Application

1. Clone this repository:
   ```
   git clone https://github.com/salmanahmad16/mp3Converter.git
   cd mp3Converter
   ```

2. Build and start the Docker container:
   ```
   docker-compose up
   ```

3. Access the application in your browser at:
   ```
   http://localhost:8086
   ```

4. To stop the application, press `Ctrl+C` in the terminal where docker-compose is running, or run:
   ```
   docker-compose down
   ```

### Building Without Docker Compose

If you prefer not to use Docker Compose:

1. Build the Docker image:
   ```
   docker build -t youtube-mp3-converter .
   ```

2. Run the container:
   ```
   docker run -p 8086:8086 youtube-mp3-converter
   ```

## Alternative Deployment: PythonAnywhere (Free Hosting)

PythonAnywhere offers free hosting for Python web applications without requiring a credit card.

### Step 1: Create a PythonAnywhere Account

1. Go to [PythonAnywhere.com](https://www.pythonanywhere.com/) and sign up for a free account

### Step 2: Upload Your Code

1. From your PythonAnywhere dashboard, click on "Files" and create a new directory:
   ```
   mkdir mp3Converter
   ```

2. Upload your files using the PythonAnywhere file uploader or clone from GitHub:
   ```
   cd mp3Converter
   git clone https://github.com/salmanahmad16/mp3Converter.git .
   ```

### Step 3: Set Up a Virtual Environment

1. Open a Bash console in PythonAnywhere
2. Create and activate a virtual environment:
   ```
   mkvirtualenv --python=python3.9 mp3converter-env
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Step 4: Configure the Web App

1. Go to the "Web" tab in your PythonAnywhere dashboard
2. Click "Add a new web app"
3. Select "Manual configuration" and Python 3.9
4. Set the following configuration:
   - Source code: `/home/yourusername/mp3Converter`
   - Working directory: `/home/yourusername/mp3Converter`
   - WSGI configuration file: Use the content from `pythonanywhere_wsgi.py`
   - Virtual environment: `/home/yourusername/.virtualenvs/mp3converter-env`

### Step 5: Install FFmpeg

PythonAnywhere allows you to use FFmpeg, which is required for this application:

1. Open a Bash console
2. Run the following commands:
   ```
   mkdir -p $HOME/bin
   wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
   tar xf ffmpeg-release-amd64-static.tar.xz
   cp ffmpeg-*-static/ffmpeg $HOME/bin/
   cp ffmpeg-*-static/ffprobe $HOME/bin/
   rm -rf ffmpeg-*-static*
   ```
3. Add the bin directory to your PATH in the WSGI file

### Step 6: Configure Environment Variables

1. In the "Web" tab, scroll down to "Environment variables"
2. Add the following:
   ```
   PATH=/home/yourusername/bin:$PATH
   ```

### Step 7: Reload Your Web App

1. Click the "Reload" button for your web app
2. Your YouTube to MP3 converter should now be live at `yourusername.pythonanywhere.com`

## Local Development

To run the application locally:

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make sure FFmpeg is installed on your system
4. Run the application:
   ```
   python app.py
   ```
5. Open your browser and navigate to `http://localhost:8086`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
