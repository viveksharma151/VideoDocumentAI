// Application State
const state = {
    geminiApiKey: localStorage.getItem('gemini_api_key') || '',
    openaiApiKey: localStorage.getItem('openai_api_key') || '',
    embeddingProvider: localStorage.getItem('embedding_provider') || 'huggingface',
    llmProvider: localStorage.getItem('llm_provider') || 'gemini',
    llmModel: localStorage.getItem('llm_model') || 'gemini-1.5-flash',
    selectedPdfFile: null,
    sources: []
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    loadSettingsFromStorage();
    updateStatusBadge();
    fetchDocuments();
    
    // Set up settings button listeners
    document.getElementById('btn-open-settings').addEventListener('click', openSettingsModal);
});

// Switch Tab
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('text-indigo-400', 'bg-slate-800/80', 'shadow-sm');
        btn.classList.add('text-slate-400');
    });

    ['form-yt', 'form-pdf', 'form-url'].forEach(id => {
        document.getElementById(id).classList.add('hidden');
    });

    if (tab === 'yt') {
        document.getElementById('tab-yt').classList.add('text-indigo-400', 'bg-slate-800/80', 'shadow-sm');
        document.getElementById('form-yt').classList.remove('hidden');
    } else if (tab === 'pdf') {
        document.getElementById('tab-pdf').classList.add('text-indigo-400', 'bg-slate-800/80', 'shadow-sm');
        document.getElementById('form-pdf').classList.remove('hidden');
    } else if (tab === 'url') {
        document.getElementById('tab-url').classList.add('text-indigo-400', 'bg-slate-800/80', 'shadow-sm');
        document.getElementById('form-url').classList.remove('hidden');
    }
}

// Handle PDF File Select
function handleFileSelected(input) {
    if (input.files && input.files[0]) {
        state.selectedPdfFile = input.files[0];
        document.getElementById('pdf-file-name').textContent = state.selectedPdfFile.name;
        document.getElementById('pdf-file-name').classList.add('text-indigo-300');
    }
}

// Ingest YouTube Video
async function ingestYoutube() {
    const url = document.getElementById('yt-url-input').value.trim();
    if (!url) {
        showStatus('Please enter a valid YouTube video URL.', 'error');
        return;
    }

    const btn = document.getElementById('btn-ingest-yt');
    setLoading(btn, true, 'Processing YouTube Transcript...');
    showStatus('Fetching YouTube video transcript & chunking text...', 'info');

    try {
        const response = await fetch('/api/ingest/youtube', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                chunk_size: 1000,
                chunk_overlap: 200
            })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to process YouTube video.');

        showStatus(data.message, 'success');
        document.getElementById('yt-url-input').value = '';
        fetchDocuments();
    } catch (err) {
        showStatus(err.message, 'error');
    } finally {
        setLoading(btn, false, 'Process YouTube Transcript');
    }
}

// Ingest PDF File Upload
async function ingestPdfFile() {
    if (!state.selectedPdfFile) {
        showStatus('Please select a PDF file first.', 'error');
        return;
    }

    const btn = document.getElementById('btn-ingest-pdf');
    setLoading(btn, true, 'Indexing PDF Document...');
    showStatus('Reading PDF pages & extracting text chunks...', 'info');

    const formData = new FormData();
    formData.append('file', state.selectedPdfFile);
    formData.append('embedding_provider', state.embeddingProvider);
    if (state.geminiApiKey) formData.append('gemini_key', state.geminiApiKey);
    if (state.openaiApiKey) formData.append('openai_key', state.openaiApiKey);

    try {
        const response = await fetch('/api/ingest/pdf-upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to process PDF upload.');

        showStatus(data.message, 'success');
        state.selectedPdfFile = null;
        document.getElementById('pdf-file-name').textContent = 'Click or drag PDF file here';
        document.getElementById('pdf-file-name').classList.remove('text-indigo-300');
        fetchDocuments();
    } catch (err) {
        showStatus(err.message, 'error');
    } finally {
        setLoading(btn, false, 'Index PDF Document');
    }
}

// Ingest PDF URL
async function ingestPdfUrl() {
    const url = document.getElementById('pdf-url-input').value.trim();
    if (!url) {
        showStatus('Please enter a valid PDF URL.', 'error');
        return;
    }

    const btn = document.getElementById('btn-ingest-url');
    setLoading(btn, true, 'Downloading PDF...');
    showStatus('Downloading PDF from web & building vector embeddings...', 'info');

    try {
        const response = await fetch('/api/ingest/pdf-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to process PDF URL.');

        showStatus(data.message, 'success');
        document.getElementById('pdf-url-input').value = '';
        fetchDocuments();
    } catch (err) {
        showStatus(err.message, 'error');
    } finally {
        setLoading(btn, false, 'Fetch & Index PDF URL');
    }
}

// Fetch Active Indexed Documents
async function fetchDocuments() {
    try {
        const res = await fetch('/api/documents');
        const data = await res.json();
        state.sources = data.sources || [];

        const countEl = document.getElementById('source-count');
        if (countEl) countEl.textContent = state.sources.length;

        const listEl = document.getElementById('sources-list');
        if (!listEl) return;

        if (state.sources.length === 0) {
            listEl.innerHTML = `
                <div class="text-center py-8 text-slate-600 text-xs">
                    <i class="fa-solid fa-folder-open text-2xl mb-2 text-slate-700"></i>
                    <p>No documents indexed yet.</p>
                    <p class="text-[11px] text-slate-600 mt-1">Add a YouTube link or PDF above to start questioning!</p>
                </div>
            `;
            return;
        }

        listEl.innerHTML = state.sources.map(src => {
            let icon = 'fa-file-alt text-slate-400';
            if (src.source_type === 'youtube') icon = 'fa-brands fa-youtube text-red-500';
            else if (src.source_type.includes('pdf')) icon = 'fa-solid fa-file-pdf text-amber-500';

            return `
                <div class="p-3 bg-slate-950/80 border border-slate-800/80 rounded-xl flex items-start space-x-3 text-xs shadow-sm hover:border-slate-700 transition">
                    <div class="mt-0.5"><i class="${icon} text-base"></i></div>
                    <div class="flex-1 min-w-0">
                        <h4 class="font-medium text-slate-200 truncate" title="${src.title}">${src.title}</h4>
                        <div class="flex items-center space-x-2 text-[10px] text-slate-500 mt-1">
                            <span><i class="fa-solid fa-cubes text-indigo-400 mr-1"></i>${src.chunks_count} chunks</span>
                            <span>•</span>
                            <span>${src.created_at}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error("Failed to fetch indexed sources:", e);
    }
}

// Clear Knowledge Base
async function clearKnowledgeBase() {
    if (!confirm("Are you sure you want to clear all indexed YouTube transcripts & PDFs from the vector database?")) return;

    try {
        const res = await fetch('/api/documents', { method: 'DELETE' });
        const data = await res.json();
        showStatus(data.message, 'success');
        fetchDocuments();
    } catch (e) {
        showStatus(e.message, 'error');
    }
}

// Send Query to RAG Pipeline
async function sendQuery() {
    const input = document.getElementById('user-input');
    const query = input.value.trim();
    if (!query) return;

    // Reset input
    input.value = '';
    autoResize(input);

    // Append User Message to Chat
    appendMessage('user', query);

    // Append Assistant Loading Indicator
    const loadingId = appendLoadingMessage();

    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                llm_provider: state.llmProvider,
                llm_model: state.llmModel,
                embedding_provider: state.embeddingProvider,
                gemini_api_key: state.geminiApiKey,
                openai_api_key: state.openaiApiKey,
                top_k: 4
            })
        });

        const data = await response.json();
        removeMessage(loadingId);

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to generate answer.');
        }

        appendMessage('assistant', data.answer, data.citations, data.llm_used);
    } catch (err) {
        removeMessage(loadingId);
        appendMessage('assistant', `**Error:** ${err.message}`);
    }
}

// Render Messages in Chat Container
function appendMessage(role, text, citations = [], llmUsed = '') {
    const chatContainer = document.getElementById('chat-messages');
    const msgId = 'msg-' + Date.now();

    const isUser = role === 'user';
    const avatar = isUser ? 
        `<div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow-md">You</div>` :
        `<div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white text-xs font-bold shadow-md shadow-indigo-500/20"><i class="fa-solid fa-robot"></i></div>`;

    const parsedMarkdown = marked.parse(text);

    let citationsHtml = '';
    if (citations && citations.length > 0) {
        citationsHtml = `
            <div class="mt-4 pt-3 border-t border-slate-800 text-xs">
                <div class="font-semibold text-slate-400 mb-2 flex items-center space-x-1.5">
                    <i class="fa-solid fa-quote-left text-indigo-400"></i>
                    <span>Retrieved Sources & Context (${citations.length})</span>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    ${citations.map((c, i) => {
                        let badge = 'PDF Page ' + (c.page || 'N/A');
                        let icon = 'fa-file-pdf text-amber-400';
                        if (c.source_type === 'youtube') {
                            badge = 'Timestamp ' + (c.timestamp || 'N/A');
                            icon = 'fa-brands fa-youtube text-red-500';
                        }
                        
                        return `
                            <div class="p-2.5 bg-slate-950/70 border border-slate-800/80 rounded-xl space-y-1">
                                <div class="flex items-center justify-between text-[11px] font-medium text-slate-300">
                                    <span class="truncate flex items-center space-x-1" title="${c.source_name}">
                                        <i class="${icon}"></i>
                                        <span class="truncate max-w-[130px]">${c.source_name}</span>
                                    </span>
                                    <span class="bg-slate-800 px-2 py-0.5 rounded text-[10px] text-indigo-300 font-mono">${badge}</span>
                                </div>
                                <p class="text-[11px] text-slate-400 line-clamp-2 italic">"${c.content}"</p>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    let modelBadge = llmUsed ? `<div class="text-[10px] text-slate-500 mt-2 flex items-center space-x-1"><span>Powered by ${llmUsed}</span></div>` : '';

    const html = `
        <div id="${msgId}" class="flex items-start space-x-3 max-w-4xl mx-auto ${isUser ? 'justify-end' : ''}">
            ${!isUser ? avatar : ''}
            <div class="flex-1 max-w-2xl ${isUser ? 'bg-indigo-600/90 text-white border border-indigo-500/50' : 'bg-slate-900/80 text-slate-200 border border-slate-800'} rounded-2xl p-4 shadow-md backdrop-blur-md">
                <div class="markdown-content text-sm leading-relaxed">${parsedMarkdown}</div>
                ${citationsHtml}
                ${modelBadge}
            </div>
            ${isUser ? avatar : ''}
        </div>
    `;

    chatContainer.insertAdjacentHTML('beforeend', html);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return msgId;
}

function appendLoadingMessage() {
    const chatContainer = document.getElementById('chat-messages');
    const loadingId = 'loading-' + Date.now();

    const html = `
        <div id="${loadingId}" class="flex items-start space-x-3 max-w-4xl mx-auto">
            <div class="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-xs font-bold">
                <i class="fa-solid fa-spinner animate-spin"></i>
            </div>
            <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 text-xs text-slate-400 flex items-center space-x-2 shadow-md">
                <span class="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>
                <span>Searching Vector DB context & generating response...</span>
            </div>
        </div>
    `;

    chatContainer.insertAdjacentHTML('beforeend', html);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return loadingId;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function useSamplePrompt(promptText) {
    const input = document.getElementById('user-input');
    input.value = promptText;
    autoResize(input);
    input.focus();
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuery();
    }
}

// Status Notifications
function showStatus(message, type) {
    const banner = document.getElementById('ingest-status');
    banner.classList.remove('hidden', 'bg-red-500/10', 'text-red-400', 'border-red-500/20', 'bg-emerald-500/10', 'text-emerald-400', 'border-emerald-500/20', 'bg-indigo-500/10', 'text-indigo-400', 'border-indigo-500/20');

    if (type === 'error') {
        banner.classList.add('bg-red-500/10', 'text-red-400', 'border', 'border-red-500/20');
    } else if (type === 'success') {
        banner.classList.add('bg-emerald-500/10', 'text-emerald-400', 'border', 'border-emerald-500/20');
    } else {
        banner.classList.add('bg-indigo-500/10', 'text-indigo-400', 'border', 'border-indigo-500/20');
    }

    banner.textContent = message;
}

function setLoading(btn, isLoading, text) {
    if (isLoading) {
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i><span>${text}</span>`;
        btn.classList.add('opacity-75');
    } else {
        btn.disabled = false;
        btn.innerHTML = `<span>${text}</span>`;
        btn.classList.remove('opacity-75');
    }
}

// Settings Modal Management
function openSettingsModal() {
    document.getElementById('setting-gemini-key').value = state.geminiApiKey;
    document.getElementById('setting-openai-key').value = state.openaiApiKey;
    document.getElementById('setting-embedding-provider').value = state.embeddingProvider;
    document.getElementById('setting-llm-provider').value = `${state.llmProvider}:${state.llmModel}`;

    document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettingsModal() {
    document.getElementById('settings-modal').classList.add('hidden');
}

function saveSettings() {
    state.geminiApiKey = document.getElementById('setting-gemini-key').value.trim();
    state.openaiApiKey = document.getElementById('setting-openai-key').value.trim();
    state.embeddingProvider = document.getElementById('setting-embedding-provider').value;
    
    const [provider, model] = document.getElementById('setting-llm-provider').value.split(':');
    state.llmProvider = provider;
    state.llmModel = model;

    localStorage.setItem('gemini_api_key', state.geminiApiKey);
    localStorage.setItem('openai_api_key', state.openaiApiKey);
    localStorage.setItem('embedding_provider', state.embeddingProvider);
    localStorage.setItem('llm_provider', state.llmProvider);
    localStorage.setItem('llm_model', state.llmModel);

    // Sync back to FastAPI config backend
    fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            gemini_api_key: state.geminiApiKey,
            openai_api_key: state.openaiApiKey,
            llm_provider: state.llmProvider,
            embedding_provider: state.embeddingProvider
        })
    });

    updateStatusBadge();
    closeSettingsModal();
}

function loadSettingsFromStorage() {
    state.geminiApiKey = localStorage.getItem('gemini_api_key') || '';
    state.openaiApiKey = localStorage.getItem('openai_api_key') || '';
    state.embeddingProvider = localStorage.getItem('embedding_provider') || 'huggingface';
    state.llmProvider = localStorage.getItem('llm_provider') || 'gemini';
    state.llmModel = localStorage.getItem('llm_model') || 'gemini-1.5-flash';
}

function updateStatusBadge() {
    const embText = document.getElementById('active-embedding-text');
    const llmText = document.getElementById('active-llm-text');

    if (embText) embText.textContent = `Embedding: ${state.embeddingProvider === 'huggingface' ? 'Local (HF)' : state.embeddingProvider}`;
    if (llmText) llmText.textContent = `LLM: ${state.llmProvider.toUpperCase()} (${state.llmModel})`;
}

function toggleKeyVisibility(inputId) {
    const input = document.getElementById(inputId);
    input.type = input.type === 'password' ? 'text' : 'password';
}
