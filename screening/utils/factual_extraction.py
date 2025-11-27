# screening/utils/factual_extraction.py

from typing import Dict, List, Tuple, Set
from datetime import datetime
from dateutil import parser as date_parser


def extract_skills(candidate: Dict) -> List[str]:
    """Extract all skills from candidate resume"""
    skills = []
    
    # Technical skills
    tech_skills = candidate.get("skills", {}).get("technical", [])
    skills.extend(tech_skills)
    
    # Tools
    tools = candidate.get("skills", {}).get("tools", [])
    skills.extend(tools)
    
    # Technologies from projects
    projects = candidate.get("projects", [])
    for proj in projects:
        technologies = proj.get("technologies", [])
        skills.extend(technologies)
    
    # Remove duplicates, normalize
    unique_skills = list(set(s.strip() for s in skills if s))
    return unique_skills


def match_skills(candidate_skills: List[str], required_skills: List[str]) -> Tuple[List[str], List[str]]:
    """
    Match candidate skills against required skills
    Returns: (matched_skills, missing_skills)
    """
    candidate_lower = [s.lower().strip() for s in candidate_skills]
    
    matched = []
    missing = []
    
    for req_skill in required_skills:
        req_lower = req_skill.lower().strip()
        if req_lower in candidate_lower:
            matched.append(req_skill)
        else:
            missing.append(req_skill)
    
    return matched, missing


def calculate_experience_years(candidate: Dict) -> float:
    """Calculate total years of experience from date ranges"""
    experience = candidate.get("experience", [])
    
    if not experience:
        return 0.0
    
    total_months = 0
    
    for exp in experience:
        start_str = exp.get("start_date", "")
        end_str = exp.get("end_date", "Present")
        
        try:
            # Clean date strings
            if "–" in start_str or "—" in start_str:
                start_str = start_str.replace("–", " ").replace("—", " ").split()[0]
            
            start_date = date_parser.parse(start_str, fuzzy=True)
            
            if end_str.lower() in ["present", "current", "now"]:
                end_date = datetime.now()
            else:
                if "–" in end_str or "—" in end_str:
                    end_str = end_str.replace("–", " ").replace("—", " ").split()[-1]
                end_date = date_parser.parse(end_str, fuzzy=True)
            
            months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            total_months += max(0, months)
        except Exception as e:
            # If parse fails, assume 1 year per role
            total_months += 12
    
    return round(total_months / 12, 1)


def check_education_relevance(candidate: Dict, domain: str = "technical") -> Dict:
    """
    Check if education is relevant to the domain
    Returns: {score: 0-100, relevant: bool, degrees: []}
    """
    education = candidate.get("education", [])
    
    if not education:
        return {"score": 0, "relevant": False, "degrees": []}
    
    degrees = [edu.get("degree", "") for edu in education]
    degrees_text = " ".join(degrees).lower()
    
    # Define relevance keywords by domain
    if domain.lower() == "technical":
        high_relevance = ["computer science", "software engineering", "information technology", "cs", "computer engineering"]
        medium_relevance = ["engineering", "electronics", "telecommunication", "mathematics", "physics", "data science"]
        
        if any(kw in degrees_text for kw in high_relevance):
            return {"score": 100, "relevant": True, "degrees": degrees}
        elif any(kw in degrees_text for kw in medium_relevance):
            return {"score": 70, "relevant": True, "degrees": degrees}
        elif any(kw in degrees_text for kw in ["bachelor", "b.tech", "b.e", "master", "m.tech"]):
            return {"score": 30, "relevant": False, "degrees": degrees}
        else:
            return {"score": 10, "relevant": False, "degrees": degrees}
    
    # For non-technical roles, just check if degree exists
    if any(kw in degrees_text for kw in ["bachelor", "master", "phd"]):
        return {"score": 70, "relevant": True, "degrees": degrees}
    
    return {"score": 30, "relevant": False, "degrees": degrees}


def check_role_relevance(candidate: Dict, jd_requirements: Dict) -> Dict:
    """
    Check if candidate's past roles are relevant to JD
    Returns: {relevant: bool, relevant_roles: [], all_roles: []}
    """
    experience = candidate.get("experience", [])
    
    if not experience:
        return {"relevant": False, "relevant_roles": [], "all_roles": []}
    
    # Extract keywords from JD
    role_level = jd_requirements.get("role_level", "").lower()
    domain = jd_requirements.get("domain", "").lower()
    
    # Define relevant keywords based on JD (default to technical)
    relevant_keywords = ["software", "developer", "engineer", "programmer", "technical", "backend", "frontend", "fullstack", "devops", "data"]
    
    all_roles = []
    relevant_roles = []
    
    for exp in experience:
        position = exp.get("position", "")
        company = exp.get("company", "")
        all_roles.append(position)
        
        # Check if position contains relevant keywords
        position_lower = position.lower()
        if any(kw in position_lower for kw in relevant_keywords):
            relevant_roles.append(position)
    
    return {
        "relevant": len(relevant_roles) > 0,
        "relevant_roles": relevant_roles,
        "all_roles": all_roles
    }


def get_factual_baseline(candidate: Dict, jd_requirements: Dict) -> Dict:
    """
    Extract all factual information before LLM evaluation
    This prevents LLM from making up facts
    """
    
    # Skills analysis
    candidate_skills = extract_skills(candidate)
    required_skills = jd_requirements.get("required_skills", [])
    matched_skills, missing_skills = match_skills(candidate_skills, required_skills)
    
    # Calculate skill match percentage
    if required_skills:
        skill_match_percentage = (len(matched_skills) / len(required_skills)) * 100
    else:
        skill_match_percentage = 50
    
    # Experience analysis
    years_of_experience = calculate_experience_years(candidate)
    min_required_years = jd_requirements.get("min_experience_years", 0)
    
    # Education analysis
    education_info = check_education_relevance(candidate, "technical")
    
    # Role relevance analysis
    role_info = check_role_relevance(candidate, jd_requirements)
    
    # Projects count
    projects = candidate.get("projects", [])
    achievements = candidate.get("achievements", [])
    
    return {
        "candidate_skills": candidate_skills,
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "skill_match_percentage": round(skill_match_percentage, 1),
        "years_of_experience": years_of_experience,
        "min_required_years": min_required_years,
        "education_score": education_info["score"],
        "education_relevant": education_info["relevant"],
        "degrees": education_info["degrees"],
        "role_relevant": role_info["relevant"],
        "relevant_roles": role_info["relevant_roles"],
        "all_roles": role_info["all_roles"],
        "project_count": len(projects),
        "achievement_count": len([a for a in achievements if a])
    }