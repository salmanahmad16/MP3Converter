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

## Local Development

To run the application without Docker:

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
