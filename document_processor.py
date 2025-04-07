import os
import re
import io
import tempfile
from pathlib import Path

# Try importing document processing libraries, with fallbacks
try:
    from PyPDF2 import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import ebooklib
    from ebooklib import epub
    HAS_EBOOKLIB = True
except ImportError:
    HAS_EBOOKLIB = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def get_text_from_html(html_content):
    """Extract text from HTML content"""
    if HAS_BS4:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        # Get text
        text = soup.get_text()
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    else:
        # Basic HTML text extraction without BeautifulSoup
        # Remove HTML tags using regex
        text = re.sub(r'<[^>]+>', ' ', html_content)
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        # Split by newlines
        lines = text.split('\n')
        # Remove empty lines
        text = '\n'.join(line.strip() for line in lines if line.strip())
        return text


def process_pdf(file_path):
    """Extract text from a PDF file"""
    text = ""
    
    if HAS_PYPDF:
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
        except Exception as e:
            text = f"Error processing PDF: {str(e)}"
    else:
        # Fallback for demonstration - in real app, you'd use another library or inform user
        text = f"PDF processing requires PyPDF2 library. Using sample content for demonstration.\n\n"
        text += "This is sample photography content for demonstration purposes.\n"
        text += "Photography principles: Rule of thirds, proper exposure, balanced composition.\n"
        text += "Good photos require attention to lighting, subject, and timing."
        
    return text


def process_epub(file_path):
    """Extract text from an EPUB file"""
    text = ""
    
    if HAS_EBOOKLIB:
        try:
            book = epub.read_epub(file_path)
            
            # Get the book title
            title = book.get_metadata('DC', 'title')
            if title:
                text += f"Title: {title[0][0]}\n\n"
            
            # Get the book content
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    html_content = item.get_content().decode('utf-8')
                    text += get_text_from_html(html_content) + "\n\n"
        except Exception as e:
            text = f"Error processing EPUB: {str(e)}"
    else:
        # Fallback for demonstration
        text = f"EPUB processing requires ebooklib. Using sample content for demonstration.\n\n"
        text += "This is sample photography content for demonstration purposes.\n"
        text += "Photography principles: Rule of thirds, proper exposure, balanced composition.\n"
        text += "Good photos require attention to lighting, subject, and timing."
        
    return text


def process_mobi_or_azw(file_path):
    """Process MOBI or AZW files with fallback for demonstration"""
    # Simplified implementation
    return f"Sample content for {os.path.basename(file_path)}.\n\n" + \
           "Photography principles: Rule of thirds, proper exposure, balanced composition.\n" + \
           "Good photos require attention to lighting, subject, and timing."


def process_document(file_path):
    """
    Process a document file and extract its text content
    
    Args:
        file_path: Path to the document file
    
    Returns:
        str: Extracted text content
    """
    try:
        file_extension = os.path.splitext(file_path.lower())[1]
        
        if file_extension == '.pdf':
            return process_pdf(file_path)
        elif file_extension == '.epub':
            return process_epub(file_path)
        elif file_extension in ['.mobi', '.azw']:
            return process_mobi_or_azw(file_path)
        else:
            return f"Unsupported file format: {file_extension}"
    except Exception as e:
        return f"Error processing document: {str(e)}\n\n" + \
               "Using sample photography content for demonstration:\n" + \
               "Photography principles: Rule of thirds, proper exposure, balanced composition.\n" + \
               "Good photos require attention to lighting, subject, and timing."

def extract_sections(text, max_section_length=1000):
    """
    Break document text into manageable sections
    
    Args:
        text: The document text
        max_section_length: Maximum length of each section
    
    Returns:
        list: List of text sections
    """
    # Simple section splitting by paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Combine paragraphs into sections of reasonable size
    sections = []
    current_section = ""
    
    for paragraph in paragraphs:
        if len(current_section) + len(paragraph) <= max_section_length:
            current_section += paragraph + "\n\n"
        else:
            if current_section:
                sections.append(current_section.strip())
            current_section = paragraph + "\n\n"
    
    # Add the last section if it's not empty
    if current_section:
        sections.append(current_section.strip())
    
    return sections
