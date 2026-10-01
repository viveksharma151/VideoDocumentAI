import os
import re
import uuid
import tempfile
import httpx
from typing import List, Dict, Any
from io import BytesIO
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    @staticmethod
    def extract_youtube_video_id(url: str) -> str:
        """Extract YouTube video ID from various YouTube URL formats."""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
            r'youtube\.com\/embed\/([0-9A-Za-z_-]{11})',
            r'youtube\.com\/shorts\/([0-9A-Za-z_-]{11})'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError("Invalid YouTube URL. Could not extract Video ID.")

    @staticmethod
    def process_youtube(url: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
        video_id = DocumentProcessor.extract_youtube_video_id(url)
        source_id = f"yt_{video_id}"
        video_title = f"YouTube Video ({video_id})"

        try:
            # Try getting English transcript first, fallback to available language
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi', 'en-US', 'auto'])
        except Exception as e:
            # Try listing transcripts if exact match fails
            try:
                transcript_obj = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_obj.find_transcript(['en', 'hi', 'en-US', 'auto'])
                transcript_list = transcript.fetch()
            except Exception as inner_e:
                raise RuntimeError(f"Could not fetch transcript for video ID '{video_id}'. Reason: {str(e)}")

        raw_documents = []
        for item in transcript_list:
            text = item.get('text', '').strip()
            if not text:
                continue
            start_sec = int(item.get('start', 0))
            minutes = start_sec // 60
            seconds = start_sec % 60
            timestamp_str = f"{minutes:02d}:{seconds:02d}"

            doc = Document(
                page_content=text,
                metadata={
                    "source_id": source_id,
                    "source_type": "youtube",
                    "source_name": video_title,
                    "video_id": video_id,
                    "url": f"https://www.youtube.com/watch?v={video_id}&t={start_sec}s",
                    "timestamp": timestamp_str,
                    "start_sec": start_sec
                }
            )
            raw_documents.append(doc)

        if not raw_documents:
            raise ValueError("No transcript text could be extracted from this YouTube video.")

        # Group text into logical chunks while preserving timestamp metadata
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(raw_documents)
        return chunks

    @staticmethod
    def process_pdf_bytes(file_bytes: bytes, filename: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
        source_id = f"pdf_{uuid.uuid4().hex[:8]}"
        reader = PdfReader(BytesIO(file_bytes))
        
        raw_documents = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if not text:
                continue

            doc = Document(
                page_content=text,
                metadata={
                    "source_id": source_id,
                    "source_type": "pdf_upload",
                    "source_name": filename,
                    "page": page_num,
                    "total_pages": len(reader.pages)
                }
            )
            raw_documents.append(doc)

        if not raw_documents:
            raise ValueError(f"No text could be extracted from PDF: {filename}. It might be scanned/image-only.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        return text_splitter.split_documents(raw_documents)

    @staticmethod
    async def process_pdf_url(url: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
        filename = url.split("/")[-1].split("?")[0] or "document.pdf"
        if not filename.endswith(".pdf"):
            filename += ".pdf"

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise ValueError(f"Failed to download PDF from URL (Status code: {response.status_code})")
            pdf_bytes = response.content

        docs = DocumentProcessor.process_pdf_bytes(pdf_bytes, filename, chunk_size, chunk_overlap)
        for doc in docs:
            doc.metadata["source_type"] = "pdf_url"
            doc.metadata["url"] = url
        return docs
