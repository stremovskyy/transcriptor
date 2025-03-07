// Language translations
const translations = {
    'uk': {
        'page-title': 'Аудіо Транскрипція',
        'tab-file': 'Файл',
        'tab-url': 'URL',
        'tab-reconstruct': 'Реконструкція',
        'api-key': 'API Ключ:',
        'save-api-key': 'Зберегти',
        'api-key-saved': 'Збережено',
        'api-key-placeholder': 'Введіть API ключ...',
        'api-key-required': 'API ключ потрібен для цієї операції',
        'choose-file': 'Оберіть MP3 Файл:',
        'languages': 'Мови (через кому, замовчування: Ukrainian):',
        'keywords': 'Ключові слова (через кому):',
        'confidence-threshold': 'Поріг довіри (замовчування: 65):',
        'model': 'Моделька:',
        'model-tiny': 'Крихітка',
        'model-base': 'Базова',
        'model-small': 'Маленька',
        'model-medium': 'Середня',
        'model-large': 'Велика',
        'model-large-v2': 'Велика v2',
        'model-large-v3': 'Велика v3',
        'model-large-v3-turbo': 'Велика v3 Turbo',
        'model-turbo': 'Турбо',
        'upload-button': 'Завантажити',
        'url-file': 'URL MP3 файлу:',
        'url-languages': 'Мови (через кому, замовчування: Ukrainian):',
        'url-keywords': 'Ключові слова (через кому):',
        'url-confidence-threshold': 'Поріг довіри (замовчування: 65):',
        'url-model': 'Моделька:',
        'url-model-tiny': 'Крихітка',
        'url-model-base': 'Базова',
        'url-model-small': 'Маленька',
        'url-model-medium': 'Середня',
        'url-model-large': 'Велика',
        'url-model-large-v2': 'Велика v2',
        'url-model-large-v3': 'Велика v3',
        'url-model-large-v3-turbo': 'Велика v3 Turbo',
        'url-model-turbo': 'Турбо',
        'transcribe-button': 'Транскрибувати',
        'reconstruction-text': 'Текст для реконструкції:',
        'reconstruction-template': 'Шаблон реконструкції:',
        'max-length': 'Максимальна довжина (замовчування: 1500):',
        'model-id': 'Моделька:',
        'model-gemma-2b': 'Gemma2 -2B',
        'model-gemma-9b': 'Gemma2 -9B',
        'reconstruct-button': 'Реконструювати',
        'result-title': 'Результат',
        'processing': 'Обробка запиту...',
        'listening': 'Слухаю, що говорять...',
        'reconstructing': 'Реконструюю текст...',
        'copy-button': 'Копіювати',
        'copied': 'Скопійовано!',
        'reconstruct-button-text': 'Реконструювати',
        'processing-time': 'Час обробки: {time} секунд',
        'original-url': 'Оригінальний URL:',
        'keyword-found': 'Ключове слово "{keyword}": Знайдено',
        'original-text': 'Оригінальний текст:',
        'template': 'Шаблон:',
        'pre_process_file' : 'Препроцессінг файлу',
        'pre_process_file-false' : 'Не обробляти файл',
        'pre_process_file-true' : 'Обробити файл',
    },
    'en': {
        'page-title': 'Audio Transcription',
        'tab-file': 'File',
        'tab-url': 'URL',
        'tab-reconstruct': 'Reconstruction',
        'api-key': 'API Key:',
        'save-api-key': 'Save',
        'api-key-saved': 'Saved',
        'api-key-placeholder': 'Enter API key...',
        'api-key-required': 'API key is required for this operation',
        'choose-file': 'Choose MP3 File:',
        'languages': 'Languages (comma-separated, default: Ukrainian):',
        'keywords': 'Keywords (comma-separated):',
        'confidence-threshold': 'Confidence Threshold (default: 65):',
        'model': 'Model:',
        'model-tiny': 'Tiny',
        'model-base': 'Base',
        'model-small': 'Small',
        'model-medium': 'Medium',
        'model-large': 'Large',
        'model-large-v2': 'Large v2',
        'model-large-v3': 'Large v3',
        'model-large-v3-turbo': 'Large v3 Turbo',
        'model-turbo': 'Turbo',
        'upload-button': 'Upload',
        'url-file': 'MP3 File URL:',
        'url-languages': 'Languages (comma-separated, default: Ukrainian):',
        'url-keywords': 'Keywords (comma-separated):',
        'url-confidence-threshold': 'Confidence Threshold (default: 65):',
        'url-model': 'Model:',
        'url-model-tiny': 'Tiny',
        'url-model-base': 'Base',
        'url-model-small': 'Small',
        'url-model-medium': 'Medium',
        'url-model-large': 'Large',
        'url-model-large-v2': 'Large v2',
        'url-model-large-v3': 'Large v3',
        'url-model-large-v3-turbo': 'Large v3 Turbo',
        'url-model-turbo': 'Turbo',
        'transcribe-button': 'Transcribe',
        'reconstruction-text': 'Text for Reconstruction:',
        'reconstruction-template': 'Reconstruction Template:',
        'max-length': 'Maximum Length (default: 1500):',
        'model-id': 'Model:',
        'model-gemma-2b': 'Gemma2 -2B',
        'model-gemma-9b': 'Gemma2 -9B',
        'reconstruct-button': 'Reconstruct',
        'result-title': 'Result',
        'processing': 'Processing request...',
        'listening': 'Listening to audio...',
        'reconstructing': 'Reconstructing text...',
        'copy-button': 'Copy',
        'copied': 'Copied!',
        'reconstruct-button-text': 'Reconstruct',
        'processing-time': 'Processing Time: {time} seconds',
        'original-url': 'Original URL:',
        'keyword-found': 'Keyword "{keyword}": Found',
        'original-text': 'Original Text:',
        'template': 'Template:',
        'pre_process_file' : 'Pre-process file',
        'pre_process_file-false' : 'Do not pre-process file',
        'pre_process_file-true' : 'Pre-process file',
    }
};

// Current language
let currentLang = 'uk';

// Function to set page language
function setLanguage(lang) {
    currentLang = lang;
    document.documentElement.lang = lang;

    // Update all elements with data-lang-key attribute
    document.querySelectorAll('[data-lang-key]').forEach(element => {
        const key = element.getAttribute('data-lang-key');
        if (translations[lang][key]) {
            if (element.tagName === 'INPUT' && element.getAttribute('placeholder')) {
                element.setAttribute('placeholder', translations[lang][key]);
            } else {
                element.textContent = translations[lang][key];
            }
        }
    });

    // Update placeholders for textareas and API key
    if (lang === 'uk') {
        document.getElementById('reconstruction_text').placeholder = 'Вставте транскрибований текст тут...';
        document.getElementById('reconstruction_template').placeholder = 'Опишіть формат або структуру для реконструкції...';
        document.getElementById('api-key').placeholder = 'Введіть API ключ...';
    } else {
        document.getElementById('reconstruction_text').placeholder = 'Paste transcribed text here...';
        document.getElementById('reconstruction_template').placeholder = 'Describe format or structure for reconstruction...';
        document.getElementById('api-key').placeholder = 'Enter API key...';
    }

    // Update active button
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.lang-btn[data-lang="${lang}"]`).classList.add('active');

    // Save preference
    localStorage.setItem('preferredLanguage', lang);
}

// Language switcher functionality
document.querySelectorAll('.lang-btn').forEach(button => {
    button.addEventListener('click', function() {
        const lang = this.getAttribute('data-lang');
        setLanguage(lang);
    });
});

// API Key functionality
document.addEventListener('DOMContentLoaded', function() {
    const apiKeyField = document.getElementById('api-key');
    const saveButton = document.getElementById('save-api-key');
    const statusSpan = document.getElementById('api-key-status');

    // Load saved API key
    const savedApiKey = localStorage.getItem('apiKey');
    if (savedApiKey) {
        apiKeyField.value = savedApiKey;
    }

    // Save API key
    saveButton.addEventListener('click', function() {
        const apiKey = apiKeyField.value.trim();
        if (apiKey) {
            localStorage.setItem('apiKey', apiKey);
            statusSpan.classList.remove('hidden');
            setTimeout(() => {
                statusSpan.classList.add('hidden');
            }, 2000);
        }
    });

    // Load saved language preference
    const savedLang = localStorage.getItem('preferredLanguage');
    if (savedLang && ['uk', 'en'].includes(savedLang)) {
        setLanguage(savedLang);
    }
});

// Helper function to get API key
function getApiKey() {
    return localStorage.getItem('apiKey') || '';
}

// Helper function to create headers with API key
function createHeaders(contentType = null) {
    const headers = {};
    const apiKey = getApiKey();

    if (apiKey) {
        headers['x-api-key'] = apiKey;
    }

    if (contentType) {
        headers['Content-Type'] = contentType;
    }

    return headers;
}

// Tab functionality
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function() {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        this.classList.add('active');
        const tabId = this.getAttribute('data-tab');
        if (tabId === 'file-upload') {
            document.getElementById('upload-form').classList.add('active');
        } else if (tabId === 'url-upload') {
            document.getElementById('url-form').classList.add('active');
        } else if (tabId === 'reconstruct') {
            document.getElementById('reconstruct-form').classList.add('active');
        }
    });
});

// Utility function to get localized text
function getLocalizedText(key, replacements = {}) {
    let text = translations[currentLang][key] || key;

    // Replace placeholders with actual values
    Object.keys(replacements).forEach(placeholder => {
        text = text.replace(`{${placeholder}}`, replacements[placeholder]);
    });

    return text;
}

// File upload form handler
document.getElementById('upload-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const formData = new FormData();
    const fileField = document.querySelector('input[type="file"]');
    const langField = document.querySelector('input[name="lang"]');
    const keywordsField = document.querySelector('input[name="keywords"]');
    const confidenceThresholdField = document.querySelector('input[name="confidence_threshold"]');
    const preProcessFileField = document.querySelector('select#pre_process_file');
    const modelField = document.querySelector('select[name="model"]');
    const button = event.target.querySelector('button');
    const loading = document.getElementById('loading');

    formData.append('file', fileField.files[0]);
    formData.append('lang', langField.value);
    formData.append('keywords', keywordsField.value);
    formData.append('confidence_threshold', confidenceThresholdField.value);
    formData.append('model', modelField.value);
    formData.append('pre_process_file', preProcessFileField.value);

    button.disabled = true;
    loading.style.display = 'block';
    loading.textContent = getLocalizedText('listening');
    document.getElementById('result').textContent = '';

    try {
        const startTime = performance.now();
        const response = await fetch('/transcribe', {
            method: 'POST',
            headers: createHeaders(), // No Content-Type for FormData
            body: formData
        });
        const endTime = performance.now();
        const result = await response.json();
        if (response.ok) {
            displayResult(result, (endTime - startTime) / 1000);
        } else {
            document.getElementById('result').textContent = `Error: ${result.error}`;
        }
    } catch (error) {
        document.getElementById('result').textContent = `Error: ${error.message}`;
    } finally {
        button.disabled = false;
        loading.style.display = 'none';
    }
});

// URL form handler
document.getElementById('url-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const urlField = document.getElementById('file_url');
    const langField = document.getElementById('url_lang');
    const keywordsField = document.getElementById('url_keywords');
    const confidenceThresholdField = document.getElementById('url_confidence_threshold');
    const preProcessFileField = document.querySelector('select#url_pre_process_file');
    const modelField = document.getElementById('url_model');
    const button = event.target.querySelector('button');
    const loading = document.getElementById('loading');

    const jsonData = {
        file_url: urlField.value,
        languages: langField.value.split(',').map(lang => lang.trim()),
        keywords: keywordsField.value ? keywordsField.value.split(',').map(kw => kw.trim()) : [],
        confidence_threshold: parseInt(confidenceThresholdField.value),
        model: modelField.value,
        pre_process_file: preProcessFileField.value
    };

    button.disabled = true;
    loading.style.display = 'block';
    loading.textContent = getLocalizedText('listening');
    document.getElementById('result').textContent = '';

    try {
        const startTime = performance.now();
        const response = await fetch('/pull', {
            method: 'POST',
            headers: createHeaders('application/json'),
            body: JSON.stringify(jsonData)
        });
        const endTime = performance.now();
        const result = await response.json();
        if (response.ok) {
            displayResult(result, result.processing_time || (endTime - startTime) / 1000);
        } else {
            document.getElementById('result').textContent = `Error: ${result.error}`;
        }
    } catch (error) {
        document.getElementById('result').textContent = `Error: ${error.message}`;
    } finally {
        button.disabled = false;
        loading.style.display = 'none';
    }
});

// Reconstruction form handler
document.getElementById('reconstruct-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const textField = document.getElementById('reconstruction_text');
    const templateField = document.getElementById('reconstruction_template');
    const maxLengthField = document.getElementById('max_length');
    const modelField = document.getElementById('model_id');
    const button = event.target.querySelector('button');
    const loading = document.getElementById('loading');

    const jsonData = {
        transcription: textField.value,
        template: templateField.value,
        max_length: parseInt(maxLengthField.value),
        model_id: modelField.value
    };

    button.disabled = true;
    loading.style.display = 'block';
    loading.textContent = getLocalizedText('reconstructing');
    document.getElementById('result').textContent = '';

    try {
        const startTime = performance.now();
        const response = await fetch('/reconstruct', {
            method: 'POST',
            headers: createHeaders('application/json'),
            body: JSON.stringify(jsonData)
        });
        const endTime = performance.now();
        const result = await response.json();
        if (response.ok) {
            displayReconstructionResult(result);
        } else {
            document.getElementById('result').textContent = `Error: ${result.error}`;
        }
    } catch (error) {
        document.getElementById('result').textContent = `Error: ${error.message}`;
    } finally {
        button.disabled = false;
        loading.style.display = 'none';
    }
});

// Function to display transcription results
function displayResult(result, processingTime) {
    let resultHtml = `<div>${getLocalizedText('processing-time', { time: processingTime.toFixed(2) })}</div>`;

    // If URL was used, show it
    if (result.original_url) {
        resultHtml += `<div><strong>${getLocalizedText('original-url')}</strong> ${result.original_url}</div><br>`;
    }

    for (const [lang, transcription] of Object.entries(result.transcriptions)) {
        resultHtml += `<div><strong>${lang}:</strong>
        <div id="transcription-${lang}" class="result-content">${transcription}</div>
        <div class="action-buttons">
            <button class="copy-button" data-text="${transcription.replace(/"/g, '&quot;')}">${getLocalizedText('copy-button')}</button>
            <button class="reconstruct-button" data-text="${transcription.replace(/"/g, '&quot;')}">${getLocalizedText('reconstruct-button-text')}</button>
        </div>
        </div><br>`;

        if (result.keyword_spots[lang]) {
            let keywordResults = '';
            for (const [keyword, positions] of Object.entries(result.keyword_spots[lang])) {
                if (positions.length === 0) {
                    continue;
                }

                keywordResults += `<div><strong>${getLocalizedText('keyword-found', { keyword: keyword })}</strong></div>`;
            }
            if (keywordResults) {
                resultHtml += `<div>${keywordResults}</div><br>`;
            }
        }
    }
    document.getElementById('result').innerHTML = resultHtml;

    // Add event listeners for copy buttons
    document.querySelectorAll('.copy-button').forEach(button => {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-text');
            navigator.clipboard.writeText(text)
                .then(() => {
                    const originalText = this.textContent;
                    this.textContent = getLocalizedText('copied');
                    setTimeout(() => {
                        this.textContent = originalText;
                    }, 2000);
                })
                .catch(err => {
                    console.error('Copy failed: ', err);
                });
        });
    });

    // Add event listeners for reconstruct buttons
    document.querySelectorAll('.reconstruct-button').forEach(button => {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-text');

            // Switch to reconstruct tab
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            document.querySelector('.tab[data-tab="reconstruct"]').classList.add('active');
            document.getElementById('reconstruct-form').classList.add('active');

            // Fill in the reconstruction form with the text
            document.getElementById('reconstruction_text').value = text;
            document.getElementById('reconstruction_text').focus();
        });
    });
}

// Function to display reconstruction results
function displayReconstructionResult(result) {
    let resultHtml = `<div>${getLocalizedText('processing-time', { time: result.processing_time.toFixed(2) })}</div><br>`;

    resultHtml += `<div><strong>${getLocalizedText('original-text')}</strong><div class="result-content">${result.original_transcription}</div></div><br>`;
    resultHtml += `<div><strong>${getLocalizedText('template')}</strong><div class="result-content">${result.template}</div></div><br>`;
    resultHtml += `<div><strong>${currentLang === 'uk' ? 'Реконструйований текст' : 'Reconstructed Text'}:</strong><div id="reconstructed-text" class="result-content">${result.reconstructed_text}</div>
        <div class="action-buttons">
            <button class="copy-button" data-text="${result.reconstructed_text.replace(/"/g, '&quot;')}">${getLocalizedText('copy-button')}</button>
        </div>
    </div>`;

    document.getElementById('result').innerHTML = resultHtml;

    // Add event listeners for copy buttons
    document.querySelectorAll('.copy-button').forEach(button => {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-text');
            navigator.clipboard.writeText(text)
                .then(() => {
                    const originalText = this.textContent;
                    this.textContent = getLocalizedText('copied');
                    setTimeout(() => {
                        this.textContent = originalText;
                    }, 2000);
                })
                .catch(err => {
                    console.error('Copy failed: ', err);
                });
        });
    });
}