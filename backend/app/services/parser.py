"""
Resume Parser Service - Orchestrates PDF extraction and LLM parsing
"""
from typing import Dict
import json
from app.services.pdf_extractor import PDFExtractor
from app.services.ollama_service import OllamaService
from app.config import settings
from app.utils.prompts import get_prompt


class ResumeParser:
    """
    Main resume parsing orchestrator
    """
    
    def __init__(self, pdf_extractor: PDFExtractor, ollama_service: OllamaService):
        self.pdf_extractor = pdf_extractor
        self.ollama_service = ollama_service
    
    async def parse(self, pdf_path: str) -> Dict:
        """
        Parse a resume PDF and return structured data
        """
        # Step 1: Extract text from PDF
        extracted_text = self.pdf_extractor.extract_text(pdf_path)
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            raise Exception("Could not extract sufficient text from PDF. The file might be corrupted or empty.")
        
        # Step 2: Parse with LLM
        parsed_data = await self._parse_with_llm(extracted_text)
        
        # Step 3: Post-process and validate
        processed_data = self._post_process(parsed_data)
        
        return processed_data
    
    async def _parse_with_llm(self, text: str) -> Dict:
        """
        Use LLM to parse resume text into structured format
        """
        # Truncate text if too long
        max_chars = settings.MAX_TOKENS * 4  # Rough estimate: 1 token ≈ 4 chars
        if len(text) > max_chars:
            text = text[:max_chars] + "...[truncated]"
        
        # Format prompt with resume text
        from app.utils.prompts import get_prompt
        prompt = get_prompt("main_parser", resume_text=text)
        
        # Generate structured data
        try:
            parsed_data = await self.ollama_service.generate_json(
                prompt=prompt,
                retry_attempts=settings.RETRY_ATTEMPTS
            )
            
            return parsed_data
        
        except Exception as e:
            raise Exception(f"Failed to parse resume with LLM: {str(e)}")
    
    def _post_process(self, data: Dict) -> Dict:
        """
        Post-process parsed data for consistency and completeness
        """
        # Ensure all required sections exist
        default_structure = {
            "personal_info": {
                "name": None,
                "email": None,
                "phone": None,
                "location": None,
                "linkedin": None,
                "github": None,
                "website": None
            },
            "summary": None,
            "experience": [],
            "education": [],
            "skills": {
                "technical": [],
                "soft_skills": [],
                "tools": []
            },
            "certifications": [],
            "projects": [],
            "languages": [],
            "achievements": []
        }
        
        # Merge with defaults
        for key, default_value in default_structure.items():
            if key not in data:
                data[key] = default_value
            elif isinstance(default_value, dict):
                # For nested dicts, ensure all sub-keys exist
                for sub_key, sub_default in default_value.items():
                    if sub_key not in data[key]:
                        data[key][sub_key] = sub_default
        
        # Clean and normalize data
        data = self._normalize_dates(data)
        data = self._clean_empty_values(data)
        
        return data
    
    def _normalize_dates(self, data: Dict) -> Dict:
        """
        Normalize date formats across the resume
        """
        # Normalize experience dates
        if "experience" in data and isinstance(data["experience"], list):
            for exp in data["experience"]:
                if isinstance(exp, dict):
                    exp["start_date"] = self._format_date(exp.get("start_date"))
                    exp["end_date"] = self._format_date(exp.get("end_date"))
        
        # Normalize education dates
        if "education" in data and isinstance(data["education"], list):
            for edu in data["education"]:
                if isinstance(edu, dict):
                    edu["start_date"] = self._format_date(edu.get("start_date"))
                    edu["end_date"] = self._format_date(edu.get("end_date"))
        
        return data
    
    def _format_date(self, date_str):
        """
        Format date string to consistent format
        """
        if not date_str or date_str in ["Present", "Current", "Now"]:
            return "Present"
        
        # Keep original format for now - could add more sophisticated parsing
        return str(date_str).strip()
    
    def _clean_empty_values(self, data: Dict) -> Dict:
        """
        Clean empty or null values from parsed data
        """
        if isinstance(data, dict):
            return {
                k: self._clean_empty_values(v) 
                for k, v in data.items() 
                if v is not None and v != "" and v != []
            }
        elif isinstance(data, list):
            return [
                self._clean_empty_values(item) 
                for item in data 
                if item is not None and item != "" and item != {}
            ]
        else:
            return data
    
    async def extract_specific_section(self, text: str, section: str) -> Dict:
        """
        Extract a specific section from resume (useful for targeted parsing)
        """
        section_prompts = {
            "experience": "Extract only work experience from this resume. Return as JSON array.",
            "education": "Extract only education information from this resume. Return as JSON array.",
            "skills": "Extract only skills from this resume. Return as JSON object with categories.",
            "personal_info": "Extract only personal/contact information from this resume. Return as JSON object."
        }
        
        if section not in section_prompts:
            raise ValueError(f"Unknown section: {section}")
        
        prompt = f"{section_prompts[section]}\n\nResume text:\n{text}"
        
        result = await self.ollama_service.generate_json(prompt=prompt)
        return result
    
    def get_extraction_confidence(self, data: Dict) -> Dict:
        """
        Analyze confidence/completeness of extracted data
        """
        confidence = {
            "overall": 0,
            "sections": {}
        }
        
        total_sections = 0
        filled_sections = 0
        
        # Check personal info completeness
        if data.get("personal_info"):
            personal = data["personal_info"]
            filled = sum(1 for v in personal.values() if v)
            total = len(personal)
            confidence["sections"]["personal_info"] = (filled / total) * 100
            total_sections += 1
            if filled > 0:
                filled_sections += 1
        
        # Check experience
        if data.get("experience") and len(data["experience"]) > 0:
            confidence["sections"]["experience"] = 100
            filled_sections += 1
        else:
            confidence["sections"]["experience"] = 0
        total_sections += 1
        
        # Check education
        if data.get("education") and len(data["education"]) > 0:
            confidence["sections"]["education"] = 100
            filled_sections += 1
        else:
            confidence["sections"]["education"] = 0
        total_sections += 1
        
        # Check skills
        if data.get("skills"):
            skills = data["skills"]
            skill_count = sum(len(v) for v in skills.values() if isinstance(v, list))
            confidence["sections"]["skills"] = min(100, skill_count * 10)
            if skill_count > 0:
                filled_sections += 1
        else:
            confidence["sections"]["skills"] = 0
        total_sections += 1
        
        # Calculate overall confidence
        confidence["overall"] = (filled_sections / total_sections) * 100
        
        return confidence