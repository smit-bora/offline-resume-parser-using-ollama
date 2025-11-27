"""
API Routes for Resume Parser
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List
from pathlib import Path
import os
import uuid
import json
from datetime import datetime

from app.config import settings
from app.services.pdf_extractor import PDFExtractor
from app.services.ollama_service import OllamaService
from app.services.parser import ResumeParser
from app.services.resume_analyzer import ResumeAnalyzer
from app.utils.validators import validate_parsed_data


router = APIRouter()

pdf_extractor = PDFExtractor()
ollama_service = OllamaService()
resume_parser = ResumeParser(pdf_extractor, ollama_service)
resume_analyzer = ResumeAnalyzer(ollama_service)


def cleanup_file(file_path: str):
    """
    Background task to delete uploaded file
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file {file_path}: {str(e)}")


@router.post("/screen-candidates")
async def screen_candidates_endpoint(
    job_description: str = ""
):
    """
    Run screening on all parsed resumes in data/parsed_resumes/
    """
    print(f"Received JD length: {len(job_description)}")
    
    if not job_description or not job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="Job description is required"
        )
    
    output_folder = get_output_folder()
    
    if not os.path.exists(output_folder):
        raise HTTPException(
            status_code=400,
            detail="No parsed resumes found. Please parse resumes first."
        )
    
    total_candidates = get_total_candidates(output_folder)
    
    if total_candidates == 0:
        raise HTTPException(
            status_code=400,
            detail="No parsed resumes found. Please parse resumes first."
        )
    
    print(f"\n{'='*60}")
    print(f"SCREENING {total_candidates} CANDIDATES")
    print(f"{'='*60}\n")
    
    try:
        import sys
        from pathlib import Path
        
        screening_path = Path(__file__).parent.parent.parent.parent / "screening"
        sys.path.insert(0, str(screening_path))
        
        from main import screen_candidates
        
        ranked_results, screening_time = await screen_candidates(
            jd_text=job_description,
            resume_dir=Path(output_folder)
        )
        
        print(f"\n✓ Screening completed in {screening_time:.1f} seconds")
        
        return {
            "success": True,
            "candidates_screened": len(ranked_results),
            "screening_time": screening_time,
            "ranked_results": ranked_results,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n✗ Screening failed: {str(e)}")
        print(error_details)
        
        raise HTTPException(
            status_code=500,
            detail=f"Screening failed: {str(e)}"
        )


@router.delete("/clear-database")
async def clear_database():
    """
    Clear all parsed resumes and reset counter
    """
    output_folder = get_output_folder()
    
    if not os.path.exists(output_folder):
        return {
            "success": True,
            "message": "Database was already empty",
            "deleted_count": 0
        }
    
    json_files = [f for f in os.listdir(output_folder) if f.endswith('.json')]
    deleted_count = len(json_files)
    
    for filename in json_files:
        file_path = os.path.join(output_folder, filename)
        os.remove(file_path)
    
    update_candidate_counter(output_folder, 0)
    
    print(f"✓ Cleared {deleted_count} candidates from database")
    
    return {
        "success": True,
        "message": f"Cleared {deleted_count} candidates",
        "deleted_count": deleted_count
    }


@router.get("/database-stats")
async def get_database_stats():
    """
    Get current database statistics
    """
    output_folder = get_output_folder()
    
    total_candidates = get_total_candidates(output_folder)
    current_counter = get_candidate_counter(output_folder)
    
    return {
        "success": True,
        "total_candidates": total_candidates,
        "current_counter": current_counter,
        "folder": output_folder
    }


@router.post("/parse-and-screen")
async def parse_and_screen(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    job_description: str = ""
):
    """
    Parse multiple resumes and run screening against job description
    """
    if not job_description or not job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="Job description is required"
        )
    
    # Validate all files first
    for file in files:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} is not a PDF"
            )
    
    parse_results = []
    output_folder = "data/parsed_resumes"
    os.makedirs(output_folder, exist_ok=True)
    
    # Step 1: Parse all resumes
    print(f"\n{'='*60}")
    print(f"STEP 1: PARSING {len(files)} RESUMES")
    print(f"{'='*60}\n")
    
    for idx, file in enumerate(files, start=1):
        try:
            # Read file content
            file_content = await file.read()
            
            if len(file_content) > settings.MAX_FILE_SIZE:
                parse_results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": f"File size exceeds {settings.MAX_FILE_SIZE} bytes"
                })
                continue
            
            # Save temporarily
            file_id = str(uuid.uuid4())
            temp_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.pdf")
            
            with open(temp_path, "wb") as f:
                f.write(file_content)
            
            # Parse resume (NO analysis)
            print(f"Parsing resume {idx}/{len(files)}: {file.filename}")
            parsed_data = await resume_parser.parse(temp_path)
            
            # Remove analysis if present
            if 'analysis' in parsed_data:
                del parsed_data['analysis']
            
            # Save to output folder
            output_path = os.path.join(output_folder, f"candidate_{idx}.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            parse_results.append({
                "filename": file.filename,
                "status": "success",
                "saved_as": f"candidate_{idx}.json"
            })
            
            print(f"✓ Saved as candidate_{idx}.json")
        
        except Exception as e:
            print(f"✗ Failed to parse {file.filename}: {str(e)}")
            parse_results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
            
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
    
    # Check if any resumes were parsed successfully
    successful_parses = sum(1 for r in parse_results if r['status'] == 'success')
    
    if successful_parses == 0:
        raise HTTPException(
            status_code=500,
            detail="All resume parsing failed. Cannot proceed with screening."
        )
    
    # Step 2: Run screening
    print(f"\n{'='*60}")
    print(f"STEP 2: SCREENING {successful_parses} CANDIDATES")
    print(f"{'='*60}\n")
    
    try:
        # Import screening system
        import sys
        from pathlib import Path
        
        # Add screening directory to path
        screening_path = Path(__file__).parent.parent.parent / "screening"
        sys.path.insert(0, str(screening_path))
        
        # Import and run screening
        from main import screen_candidates
        
        # Run screening
        ranked_results, screening_time = await screen_candidates(
            jd_text=job_description,
            resume_dir=Path(output_folder)
        )
        
        print(f"\n✓ Screening completed in {screening_time:.1f} seconds")
        
        return {
            "success": True,
            "parsing": {
                "total_files": len(files),
                "parsed_successfully": successful_parses,
                "failed": len(files) - successful_parses,
                "results": parse_results
            },
            "screening": {
                "candidates_screened": len(ranked_results),
                "screening_time": screening_time,
                "ranked_results": ranked_results
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n✗ Screening failed: {str(e)}")
        print(error_details)
        
        raise HTTPException(
            status_code=500,
            detail=f"Screening failed: {str(e)}"
        )


def get_candidate_counter(output_folder: str) -> int:
    """Get current candidate counter"""
    counter_file = os.path.join(output_folder, ".counter")
    if os.path.exists(counter_file):
        try:
            with open(counter_file, 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    return 0


def update_candidate_counter(output_folder: str, count: int):
    """Update candidate counter"""
    counter_file = os.path.join(output_folder, ".counter")
    os.makedirs(output_folder, exist_ok=True)
    with open(counter_file, 'w') as f:
        f.write(str(count))


def get_total_candidates(output_folder: str) -> int:
    """Count total JSON files in folder"""
    if not os.path.exists(output_folder):
        return 0
    return len([f for f in os.listdir(output_folder) if f.endswith('.json')])


def get_output_folder() -> str:
    """Get absolute path to parsed_resumes folder"""
    # Get project root (3 levels up from routes.py: routes.py -> api -> app -> backend -> root)
    backend_dir = Path(__file__).parent.parent.parent
    project_root = backend_dir.parent
    output_folder = project_root / "data" / "parsed_resumes"
    return str(output_folder)


@router.post("/batch-parse")
async def batch_parse_resumes(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    Parse multiple resume PDF files and save to data/parsed_resumes/ with incrementing counter
    """
    for file in files:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} is not a PDF"
            )
    
    results = []
    output_folder = get_output_folder()
    os.makedirs(output_folder, exist_ok=True)
    
    current_counter = get_candidate_counter(output_folder)
    starting_counter = current_counter
    
    print(f"Starting counter: {current_counter}")
    
    for file in files:
        try:
            file_content = await file.read()
            
            if len(file_content) > settings.MAX_FILE_SIZE:
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": f"File size exceeds {settings.MAX_FILE_SIZE} bytes"
                })
                continue
            
            file_id = str(uuid.uuid4())
            temp_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.pdf")
            
            with open(temp_path, "wb") as f:
                f.write(file_content)
            
            current_counter += 1
            print(f"Parsing resume as candidate_{current_counter}: {file.filename}")
            parsed_data = await resume_parser.parse(temp_path)
            
            if 'analysis' in parsed_data:
                del parsed_data['analysis']
            
            parsed_data['_id'] = f"candidate_{current_counter}"
            
            output_path = os.path.join(output_folder, f"candidate_{current_counter}.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "saved_as": f"candidate_{current_counter}.json",
                "output_path": output_path
            })
            
            print(f"✓ Saved as candidate_{current_counter}.json")
        
        except Exception as e:
            print(f"✗ Failed to parse {file.filename}: {str(e)}")
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
            
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
    
    update_candidate_counter(output_folder, current_counter)
    print(f"Updated counter to: {current_counter}")
    
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = len(files) - successful
    total_in_db = get_total_candidates(output_folder)
    
    return {
        "success": True,
        "total_files": len(files),
        "parsed_successfully": successful,
        "failed": failed,
        "new_candidates": successful,
        "total_in_database": total_in_db,
        "counter_range": f"{starting_counter + 1}-{current_counter}" if successful > 0 else "none",
        "output_folder": output_folder,
        "results": results,
        "parsed_at": datetime.now().isoformat()
    }


@router.post("/parse", response_model=dict)
async def parse_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Parse a resume PDF file and analyze it
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
        print(f"Parsing resume: {file.filename}")
        parsed_data = await resume_parser.parse(file_path)
        
        # Analyze the resume (if enabled in config)
        if settings.RUN_ANALYSIS:
            try:
                print(f"Analyzing resume: {file.filename}")
                analysis = await resume_analyzer.analyze(parsed_data)
                parsed_data['analysis'] = analysis
                print(f"Analysis complete. Overall score: {analysis.get('overall_score', 'N/A')}/100")
            except Exception as e:
                print(f"Analysis failed: {str(e)}")
                # Continue without analysis if it fails
                parsed_data['analysis'] = {
                    "error": "Analysis failed",
                    "message": str(e),
                    "overall_score": None
                }
        
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
        print(f"Error details: {error_details}")
        
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


@router.get("/analysis-weights")
async def get_analysis_weights():
    """
    Get current analysis scoring weights
    """
    return {
        "success": True,
        "weights": resume_analyzer.get_category_weights(),
        "analysis_enabled": settings.RUN_ANALYSIS
    }