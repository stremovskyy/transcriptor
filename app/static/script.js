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

// File upload form handler
document.getElementById('upload-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const formData = new FormData();
    const fileField = document.querySelector('input[type="file"]');
    const langField = document.querySelector('input[name="lang"]');
    const keywordsField = document.querySelector('input[name="keywords"]');
    const confidenceThresholdField = document.querySelector('input[name="confidence_threshold"]');
    const modelField = document.querySelector('select[name="model"]');
    const button = event.target.querySelector('button');
    const loading = document.getElementById('loading');

    formData.append('file', fileField.files[0]);
    formData.append('lang', langField.value);
    formData.append('keywords', keywordsField.value);
    formData.append('confidence_threshold', confidenceThresholdField.value);
    formData.append('model', modelField.value);

    button.disabled = true;
    loading.style.display = 'block';
    loading.textContent = 'Слухаю, що говорять...';
    document.getElementById('result').textContent = '';

    try {
        const startTime = performance.now();
        const response = await fetch('/transcribe', {
            method: 'POST',
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
    const modelField = document.getElementById('url_model');
    const button = event.target.querySelector('button');
    const loading = document.getElementById('loading');

    const jsonData = {
        file_url: urlField.value,
        languages: langField.value.split(',').map(lang => lang.trim()),
        keywords: keywordsField.value ? keywordsField.value.split(',').map(kw => kw.trim()) : [],
        confidence_threshold: parseInt(confidenceThresholdField.value),
        model: modelField.value
    };

    button.disabled = true;
    loading.style.display = 'block';
    loading.textContent = 'Слухаю, що говорять...';
    document.getElementById('result').textContent = '';

    try {
        const startTime = performance.now();
        const response = await fetch('/pull', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
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
    loading.textContent = 'Реконструюю текст...';
    document.getElementById('result').textContent = '';

    try {
        const startTime = performance.now();
        const response = await fetch('/reconstruct', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
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
    let resultHtml = `<div>Processing Time: ${processingTime.toFixed(2)} seconds</div>`;

    // If URL was used, show it
    if (result.original_url) {
        resultHtml += `<div><strong>Original URL:</strong> ${result.original_url}</div><br>`;
    }

    for (const [lang, transcription] of Object.entries(result.transcriptions)) {
        resultHtml += `<div><strong>${lang}:</strong>
        <pre id="transcription-${lang}">${transcription}</pre>
        <div class="action-buttons">
            <button class="copy-button" data-text="${transcription.replace(/"/g, '&quot;')}">Копіювати</button>
            <button class="reconstruct-button" data-text="${transcription.replace(/"/g, '&quot;')}">Реконструювати</button>
        </div>
        </div><br>`;

        if (result.keyword_spots[lang]) {
            let keywordResults = '';
            for (const [keyword, positions] of Object.entries(result.keyword_spots[lang])) {
                if (positions.length === 0) {
                    continue;
                }

                keywordResults += `<div><strong>Ключове слово "${keyword}":</strong> Знайдено</div>`;
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
                    this.textContent = 'Скопійовано!';
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
    let resultHtml = `<div>Processing Time: ${result.processing_time.toFixed(2)} seconds</div><br>`;

    resultHtml += `<div><strong>Оригінальний текст:</strong><pre>${result.original_transcription}</pre></div><br>`;
    resultHtml += `<div><strong>Шаблон:</strong><pre>${result.template}</pre></div><br>`;
    resultHtml += `<div><strong>Реконструйований текст:</strong><pre id="reconstructed-text">${result.reconstructed_text}</pre>
        <div class="action-buttons">
            <button class="copy-button" data-text="${result.reconstructed_text.replace(/"/g, '&quot;')}">Копіювати</button>
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
                    this.textContent = 'Скопійовано!';
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