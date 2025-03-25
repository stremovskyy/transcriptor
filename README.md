# Audio Transcription & Text Reconstruction Service

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Version 1.1.0](https://img.shields.io/badge/Release-1.1.0-green)](https://github.com/stremovskyy/transcriptor/releases)

A production-ready Flask application for audio transcription using OpenAI's Whisper models and text reconstruction with Google's Gemma models. Provides both REST API endpoints and a simple web interface.

## Project Description

This service allows users to:
- Upload audio files for transcription
- Pull audio from remote URLs
- Transcribe audio in multiple languages
- Spot keywords within transcriptions with advanced features
- Preprocess audio for improved transcription quality
- Reconstruct and improve transcribed text using Gemma models
- Convert text to speech with Ukrainian language support

## Key Features

- 🎙️ **Multi-language Transcription** (Ukrainian, English, etc.)
- 🔍 **Advanced Keyword Spotting**  
  - ✅ Negated keyword support (`!keyword`)  
  - 🎯 Fuzzy matching with confidence thresholds  
  - 📊 Context-aware word detection  
- 🎧 **Smart Audio Preprocessing**  
  - Noise reduction & silence trimming  
  - DC offset removal & normalization  
  - Pre-emphasis filtering & compression  
- ⚡ GPU Acceleration (CUDA) with memory optimization
- 📝 **Gemma Text Reconstruction**  
  - 🔒 Safe model loading with memory checks  
  - 📈 Performance metrics tracking  
- 🔊 **Text-to-Speech (TTS)**
  - 🇺🇦 Ukrainian language support
  - 👨‍👩‍ Multiple voice options
  - 💾 Download as MP3 or play on site
- 🌐 **Web Interface** with preprocessing controls
- 🔐 API Key Authentication & Rate Limiting

## Table of Contents

- [Project Description](#project-description)
- [New in 1.1.0](#new-in-110)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Architecture](#architecture)
- [Web Interface](#web-interface)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Future Development](#future-development)

## New in 1.1.0

### Enhanced Features
- **Negated keyword support**: Find segments *without* specified terms using `!keyword` syntax
- **Audio preprocessing pipeline**: Multiple enhancement stages configurable via environment variables
- **Improved GPU memory logging**: Detailed VRAM allocation tracking during model loading

### Configuration Additions
```ini
# Audio Preprocessing
AUDIO_ENABLE_PREPROCESSING=true
AUDIO_ENABLE_DC_OFFSET=true
AUDIO_PRE_EMPHASIS=0.97
AUDIO_NOISE_THRESHOLD=2.0
```

[Full migration guide](#migration-notes)

## Installation

```bash
# Clone repository
git clone https://github.com/stremovskyy/transcriptor.git
cd transcriptor

# Set up environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install FFmpeg (Ubuntu/Debian)
sudo apt-get install ffmpeg
```

## Configuration

Create `.env` file with these essential settings:

```ini
# Core
FLASK_ENV=production
API_KEY=your-secure-key-here

# Audio Processing
AUDIO_ENABLE_PREPROCESSING=true
AUDIO_ENABLE_NOISE_REDUCTION=true
AUDIO_SAMPLE_RATE=16000

# Whisper Settings
INITIAL_MODEL=base
MAX_CONTENT_LENGTH=52428800  # 50MB
```

[Full configuration options](#advanced-configuration)

## API Documentation

### Endpoints

#### POST `/transcribe`
Transcribe audio from file upload

**Request:**
```bash
curl -X POST -H "X-API-Key: your-api-key" \
  -F "file=@audio.mp3" \
  -F "pre_process_file=true" \
  http://localhost:8080/transcribe
```

**Parameters:**
- `file`: Audio file to transcribe (MP3/WAV)
- `model`: Whisper model size (base, small, medium, large)
- `lang`: Comma-separated languages (e.g., "Ukrainian,English")
- `keywords`: Comma-separated keywords to monitor
- `confidence_threshold`: Match confidence percentage (0-100)

#### POST `/pull`
Transcribe audio from remote URL

**Request:**
```json
{
  "file_url": "https://example.com/audio.mp3",
  "model": "base",
  "languages": ["Ukrainian"],
  "keywords": ["important"],
  "confidence_threshold": 85,
   "pre_process_file": true
}
```

#### POST `/reconstruct`
Improve transcription text using Gemma models

**Request:**
```json
{
  "transcription": "raw text from whisper",
  "template": "Fix errors in the text: {transcription}",
  "model_id": "google/gemma-2b-it",
  "max_length": 1500
}
```

**Parameters:**
- `transcription`: The text to be reconstructed (required)
- `template`: Template for reconstruction with `{transcription}` placeholder (optional)
- `model_id`: Gemma model ID (default: "google/gemma-2b-it")
- `max_length`: Maximum length of generated text (default: 1500)

**Response:**
```json
{
  "original_transcription": "original text with erors",
  "template": "Fix errors in the text: {transcription}",
  "reconstructed_text": "original text with errors fixed",
  "processing_time": 2.34
}
```

#### POST `/tts`
Convert text to speech using Silero TTS models

**Request:**
```json
{
  "text": "Текст для озвучення українською мовою",
  "language": "uk",
  "voice": "mykyta"
}
```

**Parameters:**
- `text`: The text to convert to speech (required)
- `language`: Language code (default: "uk" for Ukrainian, also supports "en" for English)
- `voice`: Voice to use (options: "mykyta" or "olena" for Ukrainian, "en_0" or "en_1" for English)

**Response:**
```json
{
  "status": "success",
  "audio_url": "/static/audio/f8e7d6c5-b4a3-42d1-9e8f-7a6b5c4d3e2f.mp3",
  "processing_time": 1.23
}
```

### Response Format
```json
{
  "transcriptions": {
    "Ukrainian": "full transcribed text",
    "English": "translated text"
  },
  "keyword_spots": {
    "important": [
      {
        "word": "important",
        "confidence": 92,
        "time_mark": 23.45,
        "context": "this is important because..."
      }
    ]
  },
  "processing_time": 4.56
}
```

## Architecture

The application follows a modular architecture with:
- Flask web framework for routing and API endpoints
- Middleware for authentication and rate limiting
- Preprocessing module for audio enhancement
- Transcription module using Whisper models
- Text reconstruction using Gemma models

## Web Interface

![Web Interface](./screenshots/ui-preview.png)

**New Features**:
- Preprocessing toggle switch
- Real-time processing statistics
- Enhanced keyword configuration panel
- Text reconstruction with Gemma models

### Using Text Reconstruction

The web interface provides a dedicated "Reconstruction" tab for improving transcribed text:

1. **Access the Reconstruction Tab**:
   - Click the "Reconstruction" tab in the main interface
   - Or click the "Reconstruct" button on any transcription result

2. **Input Options**:
   - **Text**: Paste or enter the text to be reconstructed
   - **Template**: Provide instructions for reconstruction (optional)
     - Use `{transcription}` as a placeholder for your text
     - Example: "Fix grammar errors in: {transcription}"
     - If left empty, a language-appropriate template will be used automatically
   - **Maximum Length**: Set the maximum output length (default: 1500)
   - **Model**: Choose between Gemma2-2B (faster) or Gemma2-9B (higher quality)

3. **Results**:
   - View both original and reconstructed text
   - Copy results with one click
   - Processing time statistics

### Using Text-to-Speech

The web interface provides a dedicated "Text to Speech" tab for converting text to speech:

1. **Access the TTS Tab**:
   - Click the "Text to Speech" tab in the main interface

2. **Input Options**:
   - **Text**: Enter the text you want to convert to speech
   - **Language**: Choose the language (Ukrainian or English)
   - **Voice**: Select a voice (Mykyta or Olena for Ukrainian, English voices for English)

3. **Results**:
   - Listen to the generated audio directly in the browser
   - Download the audio as an MP3 file
   - Processing time statistics

## Deployment

### Docker
```bash
docker run -d --gpus all \
  -p 8080:8080 \
  -e AUDIO_ENABLE_PREPROCESSING=true \
  stremovskyy/transcription-app:1.1.0
```

### Migration Notes
Update your `.env` file with these new settings:
```ini
# Audio Preprocessing Configuration
AUDIO_ENABLE_PREPROCESSING=true
AUDIO_ENABLE_DC_OFFSET=true
AUDIO_ENABLE_NORMALIZATION=true
AUDIO_PRE_EMPHASIS=0.97
AUDIO_FRAME_LENGTH=2048
```

## Contributing

We welcome contributions! Please see our [contribution guidelines](CONTRIBUTING.md) for:
- Feature request process
- Bug reporting standards
- Code style requirements
- Pull request workflow

### Development Guidelines
When contributing to this project, please:
1. Follow the established code structure and patterns
2. Ensure all new features have appropriate tests
3. Document API changes and new functionality
4. Maintain backward compatibility when possible
5. Optimize for both CPU and GPU environments

## Future Development

Areas for potential enhancement include:
- Additional language model support
- Real-time transcription capabilities
- Enhanced keyword analysis features
- Integration with more audio sources
- Additional TTS voices and languages
- Improved UI/UX for the web interface

---

**Looking for older versions?** Visit our [release archive](https://github.com/stremovskyy/transcriptor/releases)
