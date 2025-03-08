# Audio Transcription & Text Reconstruction Service

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Version 1.1.0](https://img.shields.io/badge/Release-1.1.0-green)](https://github.com/stremovskyy/transcriptor/releases)

A production-ready Flask application for audio transcription using OpenAI's Whisper models and text reconstruction with Google's Gemma models. Provides both REST API endpoints and a simple web interface.

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
- 🌐 **Web Interface** with preprocessing controls
- 🔐 API Key Authentication & Rate Limiting

## Table of Contents

- [New in 1.1.0](#new-in-110)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Web Interface](#web-interface)
- [Deployment](#deployment)
- [Contributing](#contributing)

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
Improve transcription text using Gemma

**Request:**
```json
{
  "transcription": "raw text from whisper",
  "template": "formal report format"
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

## Web Interface

![Web Interface](./screenshots/ui-preview.png)

**New Features**:
- Preprocessing toggle switch
- Real-time processing statistics
- Enhanced keyword configuration panel

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

---

**Looking for older versions?** Visit our [release archive](https://github.com/stremovskyy/transcriptor/releases)