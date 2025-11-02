"""
API Routes for Resume Parser
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import uuid
from datetime import datetime

from app.config import settings
from app.services.pdf_extractor import PDFExtractor
from app.services.ollama_service import OllamaService
from app.services.parser import ResumeParser
from app.utils.validators import validate_parsed_data


router = APIRouter()

pdf_extractor = PDFExtractor()
ollama_service = OllamaService()
resume_parser = ResumeParser(pdf_extractor, ollama_service)


def cleanup_file(file_path: str):
    """
    Background task to delete uploaded file
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file {file_path}: {str(e)}")


@router.post("/parse", response_model=dict)
async def parse_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Parse a resume PDF file
    """
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Save file temporarily
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.pdf")
    
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Parse the resume
        parsed_data = await resume_parser.parse(file_path)
        
        # Validate parsed data
        validated_data = validate_parsed_data(parsed_data)
        
        # Schedule file cleanup
        if settings.AUTO_DELETE_UPLOADS:
            background_tasks.add_task(cleanup_file, file_path)
        
        return {
            "success": True,
            "data": validated_data,
            "filename": file.filename,
            "parsed_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        
        import traceback
        error_details = traceback.format_exc()
        print(f"Error details: {error_details}")  # Log to console
        
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing resume: {str(e)}"
        )


@router.post("/extract-text")
async def extract_text(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Extract raw text from PDF (for debugging/testing)
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    file_content = await file.read()
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.pdf")
    
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        extracted_text = pdf_extractor.extract_text(file_path)
        
        if settings.AUTO_DELETE_UPLOADS:
            background_tasks.add_task(cleanup_file, file_path)
        
        return {
            "success": True,
            "text": extracted_text,
            "filename": file.filename,
            "text_length": len(extracted_text)
        }
    
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting text: {str(e)}"
        )


@router.get("/models")
async def get_available_models():
    """
    Get list of available Ollama models
    """
    try:
        models = await ollama_service.list_models()
        return {
            "success": True,
            "models": models,
            "current_model": settings.OLLAMA_MODEL
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching models: {str(e)}"
        )


@router.get("/test-ollama")
async def test_ollama():
    """
    Test Ollama connection and model
    """
    try:
        test_prompt = "Reply with just 'OK' if you can read this."
        response = await ollama_service.generate(test_prompt)
        
        return {
            "success": True,
            "message": "Ollama is working correctly",
            "model": settings.OLLAMA_MODEL,
            "response": response
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ollama test failed: {str(e)}"
        )