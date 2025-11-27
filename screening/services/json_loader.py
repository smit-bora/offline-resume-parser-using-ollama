# screening/services/json_loader.py

import json
from pathlib import Path
from typing import List, Dict, Optional


def load_resumes(directory: Path, limit: Optional[int] = None) -> List[Dict]:
    """
    Load all parsed resume JSONs from directory
    
    Args:
        directory: Path to directory containing JSON files
        limit: Maximum number of resumes to load (None for all)
        
    Returns:
        List of resume dictionaries
    """
    if not directory.exists():
        raise FileNotFoundError(f"Resume directory not found: {directory}")
    
    json_files = list(directory.glob("*.json"))
    
    if not json_files:
        raise ValueError(f"No JSON files found in {directory}")
    
    if limit:
        json_files = json_files[:limit]
    
    resumes = []
    
    for idx, filepath in enumerate(json_files, 1):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)
                
                # Add metadata
                resume_data['_id'] = filepath.stem
                resume_data['_filename'] = filepath.name
                
                # Validate basic structure
                if not _validate_resume_structure(resume_data):
                    print(f"Warning: Invalid structure in {filepath.name}, skipping...")
                    continue
                
                resumes.append(resume_data)
        
        except json.JSONDecodeError as e:
            print(f"Error parsing {filepath.name}: {str(e)}")
            continue
        except Exception as e:
            print(f"Error loading {filepath.name}: {str(e)}")
            continue
    
    if not resumes:
        raise ValueError("No valid resume JSONs could be loaded")
    
    print(f"Loaded {len(resumes)} valid resume(s)")
    return resumes


def _validate_resume_structure(resume: Dict) -> bool:
    """
    Validate that resume has minimum required structure
    
    Args:
        resume: Resume dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["personal_info"]
    
    for field in required_fields:
        if field not in resume:
            return False
    
    # Check personal_info has name
    personal_info = resume.get("personal_info", {})
    if not personal_info.get("name"):
        return False
    
    return True


def load_single_resume(filepath: Path) -> Dict:
    """
    Load a single resume JSON file
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Resume dictionary
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        resume_data = json.load(f)
    
    resume_data['_id'] = filepath.stem
    resume_data['_filename'] = filepath.name
    
    if not _validate_resume_structure(resume_data):
        raise ValueError(f"Invalid resume structure in {filepath.name}")
    
    return resume_data


def get_resume_count(directory: Path) -> int:
    """
    Get count of JSON files in directory
    
    Args:
        directory: Path to directory
        
    Returns:
        Number of JSON files
    """
    if not directory.exists():
        return 0
    
    return len(list(directory.glob("*.json")))