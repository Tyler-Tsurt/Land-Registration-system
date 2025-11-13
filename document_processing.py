

"""
document_processing.py

Extract text from documents for AI analysis.
"""
import os
import pytesseract
from PIL import Image
from PyPDF2 import PdfReader
import docx
import logging

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configure Poppler path for pdf2image
POPPLER_PATH = r'C:\Program Files\poppler-25.07.0\Library\bin'

logger = logging.getLogger(__name__)

def extract_document_text(file_path, mime_type):
    """
    Extract text from a document.
    
    Supports:
    - PDF files
    - Image files (JPEG, PNG) with OCR
    - Word documents (.docx)
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""
        
        # PDF files
        if mime_type == 'application/pdf' or file_path.endswith('.pdf'):
            text = extract_pdf_text(file_path)
            if text.strip():
                return text
            # If no text, try OCR
            return extract_pdf_images_text(file_path)
        
        # Image files
        elif mime_type in ['image/jpeg', 'image/png', 'image/jpg'] or \
             file_path.endswith(('.jpg', '.jpeg', '.png')):
            return extract_image_text(file_path)
        
        # Word documents
        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or \
             file_path.endswith('.docx'):
            return extract_docx_text(file_path)
        
        else:
            logger.warning(f"Unsupported file type: {mime_type}")
            return ""
    
    except Exception as e:
        logger.exception(f"Error extracting text from {file_path}: {e}")
        return ""


def extract_pdf_text(file_path):
    """Extract text from PDF using PyPDF2."""
    try:
        reader = PdfReader(file_path)
        text = []
        for page in reader.pages:
            text.append(page.extract_text())
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return ""


def extract_pdf_images_text(file_path):
    """Extract text from images in PDF using OCR."""
    # This requires pdf2image and tesseract
    try:
        from pdf2image import convert_from_path
        # Use the configured Poppler path
        images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
        text = []
        for img in images:
            text.append(pytesseract.image_to_string(img))
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error extracting PDF images: {e}")
        return ""


def extract_image_text(file_path):
    """Extract text from image using OCR."""
    try:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        logger.error(f"Error extracting image text: {e}")
        return ""


def extract_docx_text(file_path):
    """Extract text from Word document."""
    try:
        doc = docx.Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error extracting DOCX text: {e}")
        return ""