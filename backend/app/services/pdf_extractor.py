"""
PDF Text Extraction Service
"""
import pdfplumber
import PyPDF2
import re
from typing import Optional
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path

class PDFExtractor:
    """
    Extract text from PDF files using multiple methods
    """
    
    def __init__(self):
        self.method = "pdfplumber"  # Default method
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF file
        """
        try:
            # Try primary method (pdfplumber)
            text = self._extract_with_pdfplumber(pdf_path)
            
            # If extraction yields poor results, try fallback
            if not text or len(text.strip()) < 50:
                text = self._extract_with_pypdf2(pdf_path)
            
            # Clean and normalize text
            text = self._clean_text(text)
            
            return text
        
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
        
        

    # def _extract_with_pymupdf(self, pdf_path: str) -> str:
    #     text = ""
    #     doc = fitz.open(pdf_path)
    #     for page in doc:
    #         text += page.get_text("text") + "\n\n"
    #     doc.close()
    #     return text
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """
        Extract text using pdfplumber (best for complex layouts)
        """
        text = ""
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        
        return text
    
    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """
        Extract text using PyPDF2 (fallback method)
        """
        text = ""
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        
        return text
    
    def _extract_with_ocr(self, pdf_path: str) -> str:
        images = convert_from_path(pdf_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image) + "\n\n"
        return text
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with parsing
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove multiple consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Trim whitespace
        text = text.strip()
        
        return text
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get number of pages in PDF
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
    
    def extract_metadata(self, pdf_path: str) -> dict:
        """
        Extract PDF metadata
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = pdf_reader.metadata
                
                return {
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "subject": metadata.get("/Subject", ""),
                    "creator": metadata.get("/Creator", ""),
                    "producer": metadata.get("/Producer", ""),
                    "creation_date": metadata.get("/CreationDate", ""),
                    "pages": len(pdf_reader.pages)
                }
        except Exception as e:
            return {"error": str(e)}