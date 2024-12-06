# **Transcription Service Application**

## **Overview**
The Transcription Service Application is a Flask-based API that provides robust audio transcription capabilities using the Whisper model. This application supports multiple languages, keyword spotting, and real-time transcription of uploaded audio files. It includes advanced GPU/CPU handling and integrates rate-limiting to ensure performance and security.

---

## **Features**
- **Audio Transcription**: Transcribe audio files into text using Whisper's advanced models.
- **Multi-language Support**: Process audio in multiple languages (e.g., Ukrainian).
- **Keyword Spotting**: Identify and highlight keywords within transcriptions.
- **Rate Limiting**: Prevent abuse with customizable limits for API endpoints.
- **Scalable**: Efficiently manages GPU and CPU resources for high-performance processing.
- **Configurable**: Environment-based configurations for easy customization.

---

## **Getting Started**

### **Prerequisites**
Ensure you have the following installed:
- Python 3.8+
- pip (Python package installer)
- GPU (optional but recommended for performance)

---

### **Setup Instructions**

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/transcription-service.git
   cd transcription-service
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   Create a `.env` file in the root directory and add the following:
   ```env
   FLASK_ENV=development
   FLASK_HOST=0.0.0.0
   FLASK_PORT=8080
   UPLOAD_FOLDER=/tmp
   ALLOWED_EXTENSIONS=mp3,wav,m4a
   ```

4. **Run the Application**:
   ```bash
   python app.py
   ```

5. **Access the Application**:
   Visit [http://localhost:8080](http://localhost:8080) in your browser.

---

## **Project Structure**
```plaintext
transcription_project/
│
├── app/
│   ├── __init__.py        # Initializes Flask app
│   ├── routes.py          # API route handlers
│   ├── config.py          # Application configurations
│   ├── limiter.py         # Rate limiter logic
│   ├── models.py          # Whisper model caching and loading
│   ├── services.py        # Transcription logic
│   ├── managers.py        # Config and logger managers
│   └── utils.py           # Helper functions
│
├── templates/
│   └── index.html         # Frontend HTML templates
│
├── logs/
│   └── transcription_app.log # Log files
│
├── .env                   # Environment variables
├── app.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── README.md              # Documentation
├── Dockerfile             # Docker configuration
└── docker-compose.yml     # Docker Compose configuration
```

---

## **API Documentation**

### **Endpoints**
#### **1. Home**
- **URL**: `/`
- **Method**: `GET`
- **Description**: Returns the index page.

#### **2. Preload Model**
- **URL**: `/preload_model`
- **Method**: `POST`
- **Rate Limit**: 10 requests per minute
- **Payload**:
  ```json
  {
      "model": "base"
  }
  ```
- **Response**:
  ```json
  {
      "status": "Model preloaded successfully"
  }
  ```

#### **3. Transcribe Audio**
- **URL**: `/transcribe`
- **Method**: `POST`
- **Rate Limit**: 500 requests per hour
- **Payload**:
  - Multipart form-data:
    - `file` (required): The audio file to transcribe.
    - `lang` (optional): Comma-separated list of languages. Default: `Ukrainian`.
    - `model` (optional): Model type (`tiny`, `base`, `small`). Default: `base`.
    - `keywords` (optional): Comma-separated list of keywords for spotting.
    - `confidence_threshold` (optional): Minimum confidence score for keyword matching. Default: `80`.
- **Response**:
  ```json
  {
      "transcriptions": {
          "Ukrainian": "Transcribed text in Ukrainian",
          "English": "Transcribed text in English"
      },
      "keyword_spots": {
          "Ukrainian": {
              "keyword1": [
                  {
                      "word": "keyword1",
                      "confidence": 85,
                      "time_mark": 12.5,
                      "context": "context of the keyword"
                  }
              ]
          }
      },
      "processing_time": 15.2
  }
  ```

---

## **Configuration**

All configurations are managed via environment variables in a `.env` file:

| Variable             | Description                              | Default Value |
|----------------------|------------------------------------------|---------------|
| `FLASK_ENV`          | Environment (`development` or `production`) | `development` |
| `FLASK_HOST`         | Hostname for the Flask app              | `localhost`   |
| `FLASK_PORT`         | Port for the Flask app                  | `8080`        |
| `UPLOAD_FOLDER`      | Directory for uploaded files            | `/tmp`        |
| `MAX_CONTENT_LENGTH` | Maximum upload size in bytes            | `50MB`        |
| `ALLOWED_EXTENSIONS` | Allowed file extensions (comma-separated) | `mp3`         |

---

## **Logging**
Logs are saved to `logs/transcription_app.log`. They include:
- API requests
- File handling details
- Model loading status
- Errors and exceptions

---

## **Testing**
To test the application:
1. Use a tool like [Postman](https://www.postman.com/) or `curl` to send requests to the endpoints.
2. Example `curl` command for transcription:
   ```bash
   curl -X POST http://localhost:8080/transcribe \
        -F "file=@example.mp3" \
        -F "lang=Ukrainian" \
        -F "keywords=hello,world" \
        -F "confidence_threshold=90"
   ```

---

## **Contributing**
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m "Add feature"`).
4. Push to the branch (`git push origin feature-name`).
5. Create a pull request.

---

## **License**
This project has no license and is open-source.

---

## **Acknowledgments**
- [Whisper by OpenAI](https://github.com/openai/whisper)
- [Flask Framework](https://flask.palletsprojects.com/)
- [RapidFuzz Library](https://github.com/maxbachmann/RapidFuzz)
