# 🚀 Multimodal RAG Application (YouTube + PDF)

A production-grade **Retrieval-Augmented Generation (RAG)** application supporting:
- 📺 **YouTube Video Links** (Transcripts parsed with timestamps)
- 📄 **PDF File Uploads** (Extracts text with page citations)
- 🌐 **PDF Web URLs** (Downloads & indexes remote PDFs)
- 🤖 **Multi-Provider LLM & Embeddings** (Google Gemini 1.5/2.0, OpenAI GPT-4o, Free Local HuggingFace embeddings)

Built with **FastAPI**, **LangChain**, **FAISS Vector DB**, and a sleek **Responsive Dashboard Web UI**.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+, FastAPI, Uvicorn, Pydantic
- **RAG & Vector DB**: LangChain, FAISS (`faiss-cpu`), `youtube-transcript-api`, `pypdf`
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (Free Local CPU), Google Gemini `text-embedding-004`, OpenAI `text-embedding-3-small`
- **LLM Models**: Google Gemini (`gemini-1.5-flash`, `gemini-2.0-flash`), OpenAI (`gpt-4o-mini`, `gpt-4o`)
- **Frontend**: HTML5, Tailwind CSS, FontAwesome, Marked.js (Markdown rendering)

---

## 📁 Directory Structure

```
RAG_application/
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI server & route handlers
│   ├── config.py                # Environment & model settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic request & response models
│   └── services/
│       ├── __init__.py
│       ├── document_processor.py# YouTube transcript, PDF upload, & PDF URL processor
│       ├── vector_store.py      # FAISS vector store manager
│       ├── llm_factory.py       # Multi-provider LLM & Embedding factory
│       └── rag_chain.py         # RAG pipeline with context retrieval & prompt builder
├── frontend/
│   ├── index.html               # Responsive Dashboard UI
│   ├── css/
│   │   └── style.css            # Custom CSS & markdown formatting
│   └── js/
│       └── app.js               # Frontend controller & API interactions
├── requirements.txt             # Project dependencies
├── .env.example                 # Environment variables template
├── run.py                       # Single-command launcher script
└── README.md                    # Documentation
```

---

## 🚀 How to Run the Application

### 1. Activate Virtual Environment (if not already activated)
```bash
# Windows
.\venv\Scripts\activate
```

### 2. Install Dependencies (if not already installed)
```bash
pip install -r requirements.txt
```

### 3. Launch Application
Run the launcher script:
```bash
python run.py
```
This will start the FastAPI backend server on `http://127.0.0.1:8000` and automatically open your web browser!

---

## 🔑 Setting Up API Keys

1. Click on the **Settings** button in the top-right corner of the Web Dashboard.
2. Enter your **Google Gemini API Key** (or OpenAI API Key).
   - Get your free Gemini API Key from: [Google AI Studio](https://aistudio.google.com/)
3. Select your preferred **Embedding Model** (Default: `HuggingFace CPU` - Free & Local, no API key required for vector search!).
4. Select your preferred **LLM Model** (e.g. `Gemini 1.5 Flash`).
5. Click **Save Configuration**.

---

## 🎯 Features & Usage

### 📺 1. YouTube Video Ingestion
- Paste any YouTube link (e.g. `https://www.youtube.com/watch?v=...` or `https://youtu.be/...`).
- Automatically extracts transcript segments with exact timestamps.
- Returns timestamps in citations when answering user questions.

### 📄 2. PDF File Upload
- Drag & drop or select any local `.pdf` file.
- Extracts multi-page text and tracks page numbers for exact citations.

### 🌐 3. PDF Web Links
- Provide a direct link to a online PDF (e.g. `https://arxiv.org/pdf/...`).
- Asynchronously downloads, parses, and indexes the document.

### 💬 4. Interactive Chat & Citation Viewer
- Ask any question in English, Hindi, or Hinglish.
- View structured answers along with expandable citation cards showing exact text passages, scores, and YouTube timestamps/PDF page numbers.
