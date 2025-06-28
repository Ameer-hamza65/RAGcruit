import os
import tempfile
from pypdf import PdfReader
import magic
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_pdf(file_bytes: bytes) -> bool:
    """Check if the file is a valid PDF"""
    try:
        # Check if file is empty
        if len(file_bytes) == 0:
            return False
            
        # Check file type using magic
        file_type = magic.from_buffer(file_bytes)
        if "PDF" not in file_type:
            return False
            
        # Try to read the PDF
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        
        try:
            reader = PdfReader(tmp_path)
            if len(reader.pages) == 0:
                return False
            return True
        except:
            return False
        finally:
            os.unlink(tmp_path)
    except:
        return False

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    # First check if it's a valid PDF
    if not is_valid_pdf(file_bytes):
        return ""
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    
    text = ""
    try:
        reader = PdfReader(tmp_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}")
        return ""
    finally:
        os.unlink(tmp_path)
    return text