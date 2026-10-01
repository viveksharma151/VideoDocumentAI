import os
import sys
import webbrowser
import uvicorn
from threading import Timer

def open_browser():
    webbrowser.open_new("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("==========================================================")
    print(" 🚀 Starting Multimodal RAG Application (FastAPI + Web UI)")
    print(" 📺 YouTube Videos | 📄 PDF Uploads | 🌐 PDF URLs")
    print("==========================================================")
    print("Server running at: http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server.\n")

    # Schedule browser pop-up after 1.5s
    Timer(1.5, open_browser).start()

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
