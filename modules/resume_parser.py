"""
Resume Parser Module
Extracts and normalizes text from PDF and DOCX resume documents.
Handles corrupted files, encryption, scanned documents, and table extraction.
"""

import io
import os
import re
from typing import Dict, Any, Tuple, Optional, Union

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    import pypdf
except Exception:
    pypdf = None

try:
    import docx
except Exception:
    docx = None

from config.settings import MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS


def normalize_extracted_text(raw_text: str) -> str:
    """
    Cleans and normalizes extracted text:
    - Normalizes line breaks
    - Removes non-printable / control characters while preserving formatting
    - Replaces multiple consecutive spaces with a single space
    - Preserves logical section headers and paragraph breaks
    """
    if not raw_text:
        return ""

    # Replace carriage returns and excessive tabs
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Remove null characters and rare control chars (keep newline and tab)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    
    # Collapse multiple inline spaces while keeping newlines intact
    lines = []
    for line in text.split("\n"):
        clean_line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(clean_line)

    # Collapse more than two consecutive empty lines to two
    normalized = "\n".join(lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def validate_file_metadata(filename: str, file_size: int, max_size_mb: int = MAX_FILE_SIZE_MB) -> Tuple[bool, Optional[str]]:
    """
    Validates file extension and size.
    """
    if not filename:
        return False, "Filename cannot be empty."

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file format '{ext}'. Only {', '.join(ALLOWED_EXTENSIONS).upper()} files are supported."

    if file_size <= 0:
        return False, "Uploaded file is empty (0 bytes)."

    max_bytes = max_size_mb * 1024 * 1024
    if file_size > max_bytes:
        return False, f"File size ({file_size / (1024*1024):.1f}MB) exceeds the maximum allowed limit of {max_size_mb}MB."

    return True, None


def extract_text_from_pdf_pypdf(file_bytes: bytes) -> Dict[str, Any]:
    """
    Fallback extractor using pure-Python pypdf library.
    """
    if pypdf is None:
        return {
            "success": False,
            "text": "",
            "error": "Neither PyMuPDF nor pypdf is available in the environment.",
            "is_scanned": False,
            "page_count": 0
        }
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            return {
                "success": False,
                "text": "",
                "error": "The PDF is password protected or encrypted. Please upload an unprotected file.",
                "is_scanned": False,
                "page_count": len(reader.pages)
            }

        page_count = len(reader.pages)
        if page_count == 0:
            return {
                "success": False,
                "text": "",
                "error": "The PDF document contains 0 pages.",
                "is_scanned": False,
                "page_count": 0
            }

        extracted_pages = []
        for page in reader.pages:
            t = page.extract_text() or ""
            extracted_pages.append(t)

        full_raw_text = "\n\n".join(extracted_pages)
        cleaned_text = normalize_extracted_text(full_raw_text)
        word_count = len(cleaned_text.split())

        is_scanned = (word_count < 25 and page_count > 0)
        if is_scanned or not cleaned_text:
            warning = (
                "Scanned or image-only PDF detected. No extractable digital text found. "
                "Optical Character Recognition (OCR) is required to process this document. "
                "Please upload a text-selectable PDF or DOCX resume."
            )
            return {
                "success": False,
                "text": "",
                "page_count": page_count,
                "word_count": word_count,
                "char_count": len(cleaned_text),
                "is_scanned": True,
                "error": warning,
                "warning": warning
            }

        return {
            "success": True,
            "text": cleaned_text,
            "page_count": page_count,
            "word_count": word_count,
            "char_count": len(cleaned_text),
            "is_scanned": False,
            "error": None,
            "warning": None
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"Failed to parse PDF document: {str(e)}",
            "is_scanned": False,
            "page_count": 0
        }


def extract_text_from_pdf(file_bytes: bytes, filename: str = "") -> Dict[str, Any]:
    """
    Extracts text from PDF bytes using PyMuPDF (fitz) with automatic fallback to pypdf.
    Handles encrypted PDFs, multi-page documents, and detects scanned image-only PDFs.
    """
    if fitz is not None:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            try:
                if doc.is_encrypted:
                    return {
                        "success": False,
                        "text": "",
                        "error": "The PDF is password protected or encrypted. Please upload an unprotected file.",
                        "is_scanned": False,
                        "page_count": len(doc)
                    }

                page_count = len(doc)
                if page_count == 0:
                    return {
                        "success": False,
                        "text": "",
                        "error": "The PDF document contains 0 pages.",
                        "is_scanned": False,
                        "page_count": 0
                    }

                extracted_pages = []
                has_images = False

                for page_num in range(page_count):
                    page = doc.load_page(page_num)
                    page_text = page.get_text("text") or ""
                    extracted_pages.append(page_text)
                    if not page_text.strip() and len(page.get_images()) > 0:
                        has_images = True

                full_raw_text = "\n\n".join(extracted_pages)
                cleaned_text = normalize_extracted_text(full_raw_text)
                word_count = len(cleaned_text.split())

                is_scanned = (word_count < 25 and page_count > 0 and (has_images or word_count == 0))
                if is_scanned or not cleaned_text:
                    warning = (
                        "Scanned or image-only PDF detected. No extractable digital text found. "
                        "Optical Character Recognition (OCR) is required to process this document. "
                        "Please upload a text-selectable PDF or DOCX resume."
                    )
                    return {
                        "success": False,
                        "text": "",
                        "page_count": page_count,
                        "word_count": word_count,
                        "char_count": len(cleaned_text),
                        "is_scanned": True,
                        "error": warning,
                        "warning": warning
                    }

                return {
                    "success": True,
                    "text": cleaned_text,
                    "page_count": page_count,
                    "word_count": word_count,
                    "char_count": len(cleaned_text),
                    "is_scanned": False,
                    "error": None,
                    "warning": None
                }
            finally:
                try:
                    doc.close()
                except Exception:
                    pass
        except Exception:
            # If fitz encounters an error (e.g. DLL issue or stream error), fall through to pypdf
            pass

    # Fallback to pure-Python pypdf
    if pypdf is not None:
        return extract_text_from_pdf_pypdf(file_bytes)

    return {
        "success": False,
        "text": "",
        "error": "PDF parser is not available. Please ensure PyMuPDF or pypdf is installed.",
        "is_scanned": False,
        "page_count": 0
    }


def extract_text_from_docx(file_bytes: bytes, filename: str = "") -> Dict[str, Any]:
    """
    Extracts text from DOCX bytes using python-docx.
    Extracts from both body paragraphs and embedded table cells.
    """
    if docx is None:
        return {
            "success": False,
            "text": "",
            "error": "python-docx is not installed in the environment.",
            "is_scanned": False,
            "page_count": 1
        }

    try:
        doc_stream = io.BytesIO(file_bytes)
        doc = docx.Document(doc_stream)
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"Failed to parse DOCX file. File may be corrupted or invalid format. ({str(e)})",
            "is_scanned": False,
            "page_count": 0
        }

    try:
        parts = []
        
        # 1. Paragraphs
        for p in doc.paragraphs:
            if p.text and p.text.strip():
                parts.append(p.text.strip())

        # 2. Tables (resumes often put contact info or skills in tables)
        for table in doc.tables:
            for row in table.rows:
                row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                # Deduplicate identical adjacent cells caused by merged cells
                deduped = []
                for cell_txt in row_texts:
                    if not deduped or deduped[-1] != cell_txt:
                        deduped.append(cell_txt)
                if deduped:
                    parts.append(" | ".join(deduped))

        raw_text = "\n".join(parts)
        cleaned_text = normalize_extracted_text(raw_text)
        word_count = len(cleaned_text.split())

        if not cleaned_text or word_count < 10:
            return {
                "success": False,
                "text": "",
                "page_count": 1,
                "word_count": word_count,
                "char_count": len(cleaned_text),
                "is_scanned": False,
                "error": "No readable text content found in this DOCX resume.",
                "warning": "Document appears empty or contains non-text elements."
            }

        return {
            "success": True,
            "text": cleaned_text,
            "page_count": max(1, word_count // 350),  # Rough estimate of page count for DOCX
            "word_count": word_count,
            "char_count": len(cleaned_text),
            "is_scanned": False,
            "error": None,
            "warning": None
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"Error parsing DOCX contents: {str(e)}",
            "is_scanned": False,
            "page_count": 0
        }


def extract_resume_text(uploaded_file: Any) -> Dict[str, Any]:
    """
    Main entry point for extracting resume text from an uploaded file object or path.
    Supports Streamlit UploadedFile, file-like objects, or file path.
    """
    # 1. Determine filename and read bytes
    if hasattr(uploaded_file, "name") and hasattr(uploaded_file, "read"):
        filename = uploaded_file.name
        # Save position, read, reset
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        file_bytes = uploaded_file.read()
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
    elif isinstance(uploaded_file, (str, os.PathLike)):
        filename = os.path.basename(str(uploaded_file))
        with open(uploaded_file, "rb") as f:
            file_bytes = f.read()
    elif isinstance(uploaded_file, tuple) and len(uploaded_file) == 2:
        filename, file_bytes = uploaded_file
    else:
        return {
            "success": False,
            "text": "",
            "filename": "unknown",
            "file_size": 0,
            "error": "Invalid file input provided.",
            "is_scanned": False
        }

    file_size = len(file_bytes)
    
    # 2. Validate metadata
    is_valid, validation_error = validate_file_metadata(filename, file_size)
    if not is_valid:
        return {
            "success": False,
            "text": "",
            "filename": filename,
            "file_size": file_size,
            "error": validation_error,
            "is_scanned": False
        }

    ext = os.path.splitext(filename)[1].lower()

    # 3. Route to specific extractor
    if ext == ".pdf":
        result = extract_text_from_pdf(file_bytes, filename)
    elif ext == ".docx":
        result = extract_text_from_docx(file_bytes, filename)
    else:
        result = {
            "success": False,
            "text": "",
            "error": f"Unsupported file extension: {ext}",
            "is_scanned": False
        }

    result["filename"] = filename
    result["file_size"] = file_size
    result["file_type"] = ext.lstrip(".").upper()
    return result
