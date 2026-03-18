/**
 * TransLingua — Frontend Application
 * Handles file upload, OCR processing, translation, and feedback.
 */

// ============================================================
// State Management
// ============================================================
const state = {
    selectedFile: null,
    sourceLanguage: 'nepali',
    processingMode: 'pipeline', // 'pipeline' or 'ocr'
    textLanguage: 'nepali',
    lastResult: null,
    feedbackRating: 0,
};

// ============================================================
// DOM Elements
// ============================================================
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// Navigation
const navLinks = $$('.nav-link');
const sections = {
    translator: $('#translator'),
    'text-translate': $('#text-translate'),
    status: $('#status'),
};

// Upload
const uploadArea = $('#uploadArea');
const dropZone = $('#dropZone');
const fileInput = $('#fileInput');
const browseBtn = $('#browseBtn');
const filePreview = $('#filePreview');
const previewFilename = $('#previewFilename');
const previewSize = $('#previewSize');
const previewImageContainer = $('#previewImageContainer');
const previewImage = $('#previewImage');
const removeFileBtn = $('#removeFile');

// Controls
const langButtons = $$('.lang-btn[data-lang]:not(.small)');
const modeButtons = $$('.mode-btn');
const processBtn = $('#processBtn');

// Progress
const progressArea = $('#progressArea');
const progressText = $('#progressText');
const progressBar = $('#progressBar');
const steps = {
    upload: $('#stepUpload'),
    ocr: $('#stepOCR'),
    translate: $('#stepTranslate'),
    done: $('#stepDone'),
};

// Results
const resultsArea = $('#resultsArea');
const sourceText = $('#sourceText');
const translatedText = $('#translatedText');
const confidenceValue = $('#confidenceValue');
const pagesValue = $('#pagesValue');
const resultPages = $('#resultPages');
const sourceLangLabel = $('#sourceLangLabel');
const feedbackSection = $('#feedbackSection');

// Text Translation
const sourceInput = $('#sourceInput');
const translationOutput = $('#translationOutput');
const charCount = $('#charCount');
const translateTextBtn = $('#translateTextBtn');
const textLangButtons = $$('.lang-btn.small');

// Toast
const toastContainer = $('#toastContainer');

// ============================================================
// Navigation
// ============================================================
navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const section = link.dataset.section;

        navLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');

        Object.values(sections).forEach(s => {
            if (s) s.style.display = 'none';
        });
        if (sections[section]) {
            sections[section].style.display = 'block';
        }

        // Load status on status tab
        if (section === 'status') {
            loadSystemStatus();
        }
    });
});

// ============================================================
// Theme Toggle
// ============================================================
const themeToggle = $('#themeToggle');
themeToggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
});

// Load saved theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
}

// ============================================================
// File Upload & Drag/Drop
// ============================================================
browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
});

dropZone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

// Drag and drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => {
    uploadArea.addEventListener(event, (e) => {
        e.preventDefault();
        e.stopPropagation();
    });
});

uploadArea.addEventListener('dragenter', () => uploadArea.classList.add('drag-over'));
uploadArea.addEventListener('dragover', () => uploadArea.classList.add('drag-over'));
uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('drag-over'));
uploadArea.addEventListener('drop', (e) => {
    uploadArea.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

function handleFileSelect(file) {
    const allowedExts = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.pdf'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedExts.includes(ext)) {
        showToast('Unsupported file type. Please upload an image or PDF.', 'error');
        return;
    }

    state.selectedFile = file;
    showFilePreview(file);
    processBtn.disabled = false;
}

function showFilePreview(file) {
    dropZone.style.display = 'none';
    filePreview.style.display = 'block';
    previewFilename.textContent = file.name;
    previewSize.textContent = formatFileSize(file.size);

    // Show image preview for image files
    const ext = file.name.split('.').pop().toLowerCase();
    if (['png', 'jpg', 'jpeg', 'bmp', 'webp'].includes(ext)) {
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewImageContainer.style.display = 'flex';
        };
        reader.readAsDataURL(file);
    } else {
        previewImageContainer.style.display = 'none';
    }
}

removeFileBtn.addEventListener('click', () => {
    state.selectedFile = null;
    fileInput.value = '';
    filePreview.style.display = 'none';
    dropZone.style.display = 'flex';
    previewImageContainer.style.display = 'none';
    processBtn.disabled = true;
});

// ============================================================
// Language & Mode Selection
// ============================================================
langButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        langButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.sourceLanguage = btn.dataset.lang;
    });
});

modeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        modeButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.processingMode = btn.dataset.mode;
    });
});

textLangButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        textLangButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.textLanguage = btn.dataset.lang;
    });
});

// ============================================================
// Process Document
// ============================================================
processBtn.addEventListener('click', processDocument);

async function processDocument() {
    if (!state.selectedFile) {
        showToast('Please select a file first.', 'error');
        return;
    }

    const endpoint = state.processingMode === 'pipeline' ? '/api/pipeline' : '/api/ocr';

    // Show progress
    resultsArea.style.display = 'none';
    progressArea.style.display = 'block';
    processBtn.disabled = true;

    // Animate progress
    updateProgress('Uploading document...', 15, 'upload');

    const formData = new FormData();
    formData.append('file', state.selectedFile);
    formData.append('language', state.sourceLanguage);

    try {
        setTimeout(() => updateProgress('Extracting text with OCR...', 40, 'ocr'), 1000);

        if (state.processingMode === 'pipeline') {
            setTimeout(() => updateProgress('Translating to English...', 70, 'translate'), 2500);
        }

        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Processing failed');
        }

        const result = await response.json();
        state.lastResult = result;

        updateProgress('Complete!', 100, 'done');

        setTimeout(() => {
            progressArea.style.display = 'none';
            displayResults(result);
        }, 800);

    } catch (error) {
        console.error('Processing error:', error);
        progressArea.style.display = 'none';
        showToast(`Error: ${error.message}`, 'error');
        processBtn.disabled = false;
    }
}

function updateProgress(text, percent, activeStep) {
    progressText.textContent = text;
    progressBar.style.width = percent + '%';

    const stepOrder = ['upload', 'ocr', 'translate', 'done'];
    const activeIdx = stepOrder.indexOf(activeStep);

    stepOrder.forEach((step, idx) => {
        const el = steps[step];
        if (!el) return;
        el.classList.remove('active', 'done');
        if (idx < activeIdx) el.classList.add('done');
        if (idx === activeIdx) el.classList.add('active');
    });
}

// ============================================================
// Display Results
// ============================================================
function displayResults(result) {
    resultsArea.style.display = 'block';
    processBtn.disabled = false;

    const langLabel = state.sourceLanguage === 'nepali' ? 'Nepali' : 'Sinhalese';
    sourceLangLabel.textContent = langLabel;

    if (state.processingMode === 'pipeline' && result.ocr_result) {
        // Full pipeline result
        sourceText.textContent = result.ocr_result.text || 'No text extracted';
        translatedText.textContent = result.translation_result?.translated_text || 'Translation not available';
        confidenceValue.textContent = Math.round(result.ocr_result.confidence || 0);

        if (result.ocr_result.total_pages > 1) {
            resultPages.style.display = 'inline-flex';
            pagesValue.textContent = result.ocr_result.total_pages;
        } else {
            resultPages.style.display = 'none';
        }

        feedbackSection.style.display = 'block';
    } else {
        // OCR-only result
        sourceText.textContent = result.text || 'No text extracted';
        translatedText.textContent = 'OCR-only mode — no translation performed';
        confidenceValue.textContent = Math.round(result.confidence || 0);

        if (result.total_pages > 1) {
            resultPages.style.display = 'inline-flex';
            pagesValue.textContent = result.total_pages;
        } else {
            resultPages.style.display = 'none';
        }

        feedbackSection.style.display = 'none';
    }

    showToast('Document processed successfully!', 'success');

    // Scroll to results
    resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ============================================================
// Text-Only Translation
// ============================================================
sourceInput.addEventListener('input', () => {
    charCount.textContent = `${sourceInput.value.length} characters`;
});

translateTextBtn.addEventListener('click', translateText);

async function translateText() {
    const text = sourceInput.value.trim();
    if (!text) {
        showToast('Please enter text to translate.', 'error');
        return;
    }

    translateTextBtn.disabled = true;
    translationOutput.textContent = 'Translating...';
    translationOutput.style.opacity = '0.5';

    try {
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                language: state.textLanguage,
            }),
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Translation failed');
        }

        const result = await response.json();
        translationOutput.textContent = result.translated_text || 'No translation available';
        translationOutput.style.opacity = '1';
        showToast('Translation complete!', 'success');

    } catch (error) {
        console.error('Translation error:', error);
        translationOutput.textContent = 'Translation failed. Please try again.';
        translationOutput.style.opacity = '1';
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        translateTextBtn.disabled = false;
    }
}

// ============================================================
// Copy to Clipboard
// ============================================================
$$('.btn-copy').forEach(btn => {
    btn.addEventListener('click', () => {
        const targetId = btn.dataset.target;
        const targetEl = document.getElementById(targetId);
        if (targetEl) {
            const text = targetEl.textContent || targetEl.value;
            navigator.clipboard.writeText(text).then(() => {
                showToast('Copied to clipboard!', 'success');
            }).catch(() => {
                showToast('Failed to copy to clipboard.', 'error');
            });
        }
    });
});

// ============================================================
// Feedback System
// ============================================================
const stars = $$('.star');
stars.forEach(star => {
    star.addEventListener('click', () => {
        state.feedbackRating = parseInt(star.dataset.rating);
        stars.forEach(s => {
            s.classList.toggle('active', parseInt(s.dataset.rating) <= state.feedbackRating);
        });
    });

    star.addEventListener('mouseenter', () => {
        const hoverRating = parseInt(star.dataset.rating);
        stars.forEach(s => {
            s.style.color = parseInt(s.dataset.rating) <= hoverRating
                ? 'var(--warning)' : 'var(--text-muted)';
        });
    });

    star.addEventListener('mouseleave', () => {
        stars.forEach(s => {
            s.style.color = '';
        });
    });
});

$('#submitFeedback').addEventListener('click', async () => {
    if (state.feedbackRating === 0) {
        showToast('Please rate the translation quality.', 'error');
        return;
    }

    const correctedTranslation = $('#correctedTranslation').value.trim();
    const machineTranslation = translatedText.textContent;
    const srcText = sourceText.textContent;

    try {
        const response = await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source_text: srcText,
                machine_translation: machineTranslation,
                corrected_translation: correctedTranslation || machineTranslation,
                source_language: state.sourceLanguage,
                rating: state.feedbackRating,
            }),
        });

        if (!response.ok) throw new Error('Failed to submit feedback');

        showToast('Thank you! Your feedback helps improve translations.', 'success');

        // Reset feedback form
        state.feedbackRating = 0;
        stars.forEach(s => s.classList.remove('active'));
        $('#correctedTranslation').value = '';

    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
    }
});

// ============================================================
// Download Results
// ============================================================
$('#downloadResult').addEventListener('click', () => {
    const src = sourceText.textContent;
    const translated = translatedText.textContent;
    const lang = state.sourceLanguage === 'nepali' ? 'Nepali' : 'Sinhalese';

    const content = `TransLingua — Translation Report
========================================
Source Language: ${lang}
Target Language: English
Date: ${new Date().toLocaleString()}
========================================

--- EXTRACTED TEXT (${lang}) ---

${src}

--- ENGLISH TRANSLATION ---

${translated}

========================================
Generated by TransLingua AI Translation System
`;

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `translation_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('Translation downloaded!', 'success');
});

// ============================================================
// New Translation
// ============================================================
$('#newTranslation').addEventListener('click', () => {
    resultsArea.style.display = 'none';
    state.selectedFile = null;
    fileInput.value = '';
    filePreview.style.display = 'none';
    dropZone.style.display = 'flex';
    previewImageContainer.style.display = 'none';
    processBtn.disabled = true;
    state.lastResult = null;

    uploadArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
});

// ============================================================
// System Status
// ============================================================
async function loadSystemStatus() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) throw new Error('Failed to fetch status');

        const data = await response.json();

        // Update Tesseract status
        const tesseractStatus = $('#tesseractStatus');
        tesseractStatus.innerHTML = `
            <div class="status-row">
                <span>Status</span>
                <span class="status-value ${data.tesseract.available ? 'online' : 'offline'}">
                    ${data.tesseract.available ? '● Online' : '● Offline'}
                </span>
            </div>
            <div class="status-row">
                <span>Nepali Support</span>
                <span class="status-value ${data.tesseract.nepali_support ? 'online' : 'offline'}">
                    ${data.tesseract.nepali_support ? '✓ Available' : '✗ Not installed'}
                </span>
            </div>
            <div class="status-row">
                <span>Sinhalese Support</span>
                <span class="status-value ${data.tesseract.sinhalese_support ? 'online' : 'offline'}">
                    ${data.tesseract.sinhalese_support ? '✓ Available' : '✗ Not installed'}
                </span>
            </div>
        `;

        // Update translation models
        const translationStatus = $('#translationStatus');
        const models = data.translation_models;
        translationStatus.innerHTML = `
            <div class="status-row">
                <span>Nepali → English</span>
                <span class="status-value ${models.nepali?.loaded ? 'online' : models.nepali?.cached_locally ? 'online' : 'offline'}">
                    ${models.nepali?.loaded ? '● Loaded' : models.nepali?.cached_locally ? '● Cached' : '○ Not downloaded'}
                </span>
            </div>
            <div class="status-row">
                <span>Sinhalese → English</span>
                <span class="status-value ${models.sinhalese?.loaded ? 'online' : models.sinhalese?.cached_locally ? 'online' : 'offline'}">
                    ${models.sinhalese?.loaded ? '● Loaded' : models.sinhalese?.cached_locally ? '● Cached' : '○ Not downloaded'}
                </span>
            </div>
        `;

        // Update feedback counts
        const fb = data.feedback_entries;
        $('#feedbackNepali').textContent = `${fb.nepali || 0} entries`;
        $('#feedbackSinhalese').textContent = `${fb.sinhalese || 0} entries`;

    } catch (error) {
        console.error('Status load error:', error);
        showToast('Failed to load system status.', 'error');
    }
}

// ============================================================
// Toast Notifications
// ============================================================
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        error: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        info: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    };

    toast.innerHTML = `
        <span style="color: var(--${type === 'success' ? 'success' : type === 'error' ? 'error' : 'info'})">${icons[type]}</span>
        <span>${message}</span>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ============================================================
// Utility Functions
// ============================================================
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

// ============================================================
// Initialize
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    // Smooth scroll for hero section
    const hero = $('#hero');
    if (hero) {
        window.addEventListener('scroll', () => {
            const scrollY = window.scrollY;
            const heroVisual = document.querySelector('.hero-visual');
            if (heroVisual && scrollY < 600) {
                heroVisual.style.transform = `translateY(${scrollY * 0.1}px)`;
            }
        });
    }
});
