"""
Configuration settings for Resume Parser API
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # API Settings
    APP_NAME: str = "Resume Parser API"
    VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]
    
    # Ollama Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    OLLAMA_TIMEOUT: int = 120  # seconds
    OLLAMA_TEMPERATURE: float = 0.05  # Lower = more deterministic
    PDF_EXTRACTION_METHOD: str = "pymupdf"
    USE_OCR_FALLBACK: bool = True 
    
    # Alternative models you can use:
    # - llama3.1:8b (recommended for speed/accuracy balance)
    # - llama3.1:70b (more accurate, slower)
    # - mistral:7b (good alternative)
    # - gemma2:9b (another good option)
    
    # File Upload Settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB in bytes
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]
    
    # PDF Processing Settings
    PDF_EXTRACTION_METHOD: str = "pdfplumber"  # Options: pdfplumber, pypdf2, pymupdf
    USE_OCR_FALLBACK: bool = True  # Use OCR if text extraction fails
    OCR_LANGUAGE: str = "eng"  # Tesseract language code
    
    # Parsing Settings
    MAX_TOKENS: int = 8000  # Maximum tokens for LLM context
    RETRY_ATTEMPTS: int = 3  # Number of retry attempts for failed parsing
    RETRY_DELAY: int = 2  # Seconds to wait between retries
    
    # Resume Sections to Extract (can be customized)
    EXTRACT_SECTIONS: List[str] = [
        "personal_info",
        "summary",
        "experience",
        "education",
        "skills",
        "certifications",
        "projects",
        "languages",
        "achievements"
    ]
    
    # Validation Settings
    VALIDATE_EMAIL: bool = True
    VALIDATE_PHONE: bool = True
    VALIDATE_DATES: bool = True
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "resume_parser.log"
    
    # Cleanup Settings
    AUTO_DELETE_UPLOADS: bool = True  # Delete uploaded files after processing
    UPLOAD_RETENTION_HOURS: int = 1  # How long to keep uploads before cleanup
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def get_upload_path(self) -> Path:
        """
        Get the absolute path for uploads directory
        """
        return Path(self.UPLOAD_DIR).absolute()
    
    def is_allowed_file(self, filename: str) -> bool:
        """
        Check if file extension is allowed
        """
        return any(filename.lower().endswith(ext) for ext in self.ALLOWED_EXTENSIONS)
    
    def get_ollama_endpoint(self, endpoint: str) -> str:
        """
        Get full Ollama API endpoint URL
        """
        return f"{self.OLLAMA_BASE_URL}/api/{endpoint}"


# Create settings instance
settings = Settings()


# Prompt templates for different parsing strategies
PROMPTS = {
    "main_parser": """You are an expert resume parser. Extract information from the following resume text and return it as valid JSON.

Resume Text:
{resume_text}

Extract the following information and return ONLY a valid JSON object with this exact structure:

{{
    "personal_info": {{
        "name": "Full name",
        "email": "email@example.com",
        "phone": "phone number",
        "location": "city, state/country",
        "linkedin": "LinkedIn URL if present",
        "github": "GitHub URL if present",
        "website": "Personal website if present"
    }},
    "summary": "Professional summary or objective",
    "experience": [
        {{
            "company": "Company name",
            "position": "Job title",
            "location": "Location",
            "start_date": "Start date",
            "end_date": "End date or 'Present'",
            "responsibilities": ["Responsibility 1", "Responsibility 2"]
        }}
    ],
    "education": [
        {{
            "institution": "School/University name",
            "degree": "Degree type and major",
            "location": "Location",
            "start_date": "Start date",
            "end_date": "End date or 'Present'",
            "gpa": "GPA if present"
        }}
    ],
    "skills": {{
        "technical": ["skill1", "skill2"],
        "soft_skills": ["skill1", "skill2"],
        "tools": ["tool1", "tool2"]
    }},
    "certifications": [
        {{
            "name": "Certification name",
            "issuer": "Issuing organization",
            "date": "Date obtained"
        }}
    ],
    "projects": [
        {{
            "name": "Project name",
            "description": "Brief description",
            "technologies": ["tech1", "tech2"],
            "link": "Project link if available"
        }}
    ],
    "languages": ["Language1", "Language2"],
    "achievements": ["Achievement 1", "Achievement 2"]
}}

Important rules:
1. Return ONLY valid JSON, no additional text or explanations
2. Use null for missing information
3. Keep arrays empty [] if section not found
4. Preserve exact dates and formatting from resume
5. Don't invent or assume information not in the resume
6. If a section is completely missing, include it with null or empty values

Return the JSON now:""",

    "extraction_verification": """Review this extracted resume data for accuracy and completeness. The original resume text is:

{resume_text}

Extracted Data:
{extracted_data}

Verify:
1. All dates are correctly formatted
2. Email and phone numbers are valid
3. No information is duplicated
4. All experiences are chronologically ordered (most recent first)
5. Skills are properly categorized

Return the corrected JSON if any issues found, or the same JSON if everything is correct."""
}


# Model configuration for different Ollama models
MODEL_CONFIGS = {
    "llama3.1:8b": {
        "temperature": 0.1,
        "top_p": 0.9,
        "max_tokens": 4000,
    },
    "llama3.1:70b": {
        "temperature": 0.05,
        "top_p": 0.95,
        "max_tokens": 6000,
    },
    "mistral:7b": {
        "temperature": 0.1,
        "top_p": 0.9,
        "max_tokens": 4000,
    }
}