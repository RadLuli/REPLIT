import os
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re

def get_text_from_html(html_content):
    """Extract text from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.extract()
    # Get text
    text = soup.get_text()
    # Break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Remove blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text

def process_pdf(file_path):
    """Extract text from a PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
    except Exception as e:
        text = f"Error processing PDF: {str(e)}"
    return text

def process_epub(file_path):
    """Extract text from an EPUB file"""
    text = ""
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
    return text

def process_mobi_or_azw(file_path):
    """
    Process MOBI or AZW files
    
    Note: Full MOBI/AZW processing would require additional libraries 
    like Calibre's command-line tools. This is a simplified approach.
    """
    # This is a placeholder implementation
    # In a real implementation, you'd use a library like Calibre's CLI
    # to convert MOBI/AZW to EPUB or plain text first
    
    # For demonstration purposes, we'll return a message
    return f"Document content from {os.path.basename(file_path)}. Note: Full MOBI/AZW processing requires additional tools."

def process_document(file_path):
    """
    Process a document file and extract its text content
    
    Args:
        file_path: Path to the document file
    
    Returns:
        str: Extracted text content
    """
    file_extension = os.path.splitext(file_path.lower())[1]
    
    if file_extension == '.pdf':
        return process_pdf(file_path)
    elif file_extension == '.epub':
        return process_epub(file_path)
    elif file_extension in ['.mobi', '.azw']:
        return process_mobi_or_azw(file_path)
    else:
        return f"Unsupported file format: {file_extension}"

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
