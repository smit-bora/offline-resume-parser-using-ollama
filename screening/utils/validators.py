# screening/utils/validators.py

from typing import Dict, List, Tuple, Optional


def validate_agent_output(output: Dict, agent_name: str) -> Tuple[bool, List[str]]:
    """
    Validate agent output structure and content
    
    Args:
        output: Agent output dictionary
        agent_name: Name of the agent for error messages
        
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    required_fields = ["score", "reasoning", "strengths", "weaknesses"]
    for field in required_fields:
        if field not in output:
            errors.append(f"{agent_name}: Missing required field '{field}'")
    
    # Validate score
    if "score" in output:
        score = output["score"]
        if not isinstance(score, (int, float)):
            errors.append(f"{agent_name}: Score must be numeric, got {type(score)}")
        elif score < 0 or score > 100:
            errors.append(f"{agent_name}: Score {score} out of valid range (0-100)")
    
    # Validate reasoning
    if "reasoning" in output:
        if not isinstance(output["reasoning"], str):
            errors.append(f"{agent_name}: Reasoning must be string")
        elif len(output["reasoning"]) < 10:
            errors.append(f"{agent_name}: Reasoning too short")
    
    # Validate strengths/weaknesses
    for field in ["strengths", "weaknesses"]:
        if field in output:
            if not isinstance(output[field], list):
                errors.append(f"{agent_name}: {field} must be a list")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def validate_jd_requirements(jd_req: Dict) -> Tuple[bool, List[str]]:
    """
    Validate parsed job description requirements
    
    Args:
        jd_req: Parsed JD dictionary
        
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    required_fields = [
        "required_skills",
        "preferred_skills",
        "min_experience_years",
        "role_level"
    ]
    
    for field in required_fields:
        if field not in jd_req:
            errors.append(f"JD Parser: Missing field '{field}'")
    
    # Validate data types
    if "required_skills" in jd_req and not isinstance(jd_req["required_skills"], list):
        errors.append("JD Parser: required_skills must be a list")
    
    if "preferred_skills" in jd_req and not isinstance(jd_req["preferred_skills"], list):
        errors.append("JD Parser: preferred_skills must be a list")
    
    if "min_experience_years" in jd_req:
        exp = jd_req["min_experience_years"]
        if not isinstance(exp, (int, float)) or exp < 0:
            errors.append(f"JD Parser: Invalid min_experience_years value: {exp}")
    
    # Validate role level
    valid_levels = ["entry", "mid", "senior", "lead", "principal", "staff"]
    if "role_level" in jd_req:
        level = jd_req["role_level"].lower()
        if level not in valid_levels:
            errors.append(f"JD Parser: Invalid role_level '{level}'")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def validate_resume_json(resume: Dict) -> Tuple[bool, List[str]]:
    """
    Validate resume JSON structure
    
    Args:
        resume: Resume dictionary
        
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check top-level fields
    if "personal_info" not in resume:
        errors.append("Resume: Missing 'personal_info' section")
    else:
        personal = resume["personal_info"]
        if "name" not in personal or not personal["name"]:
            errors.append("Resume: Missing candidate name")
        if "email" not in personal or not personal["email"]:
            errors.append("Resume: Missing candidate email")
    
    # Check optional but important fields
    if "experience" in resume and not isinstance(resume["experience"], list):
        errors.append("Resume: 'experience' must be a list")
    
    if "skills" in resume and not isinstance(resume["skills"], dict):
        errors.append("Resume: 'skills' must be a dictionary")
    
    if "education" in resume and not isinstance(resume["education"], list):
        errors.append("Resume: 'education' must be a list")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def validate_final_results(results: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate final screening results
    
    Args:
        results: List of candidate result dictionaries
        
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    if not results:
        errors.append("Results: Empty results list")
        return False, errors
    
    required_fields = ["candidate_id", "name", "total_score", "breakdown"]
    
    for idx, result in enumerate(results):
        for field in required_fields:
            if field not in result:
                errors.append(f"Result {idx}: Missing field '{field}'")
        
        # Validate score
        if "total_score" in result:
            score = result["total_score"]
            if not isinstance(score, (int, float)):
                errors.append(f"Result {idx}: Score must be numeric")
            elif score < 0 or score > 100:
                errors.append(f"Result {idx}: Score {score} out of range")
    
    # Check if properly ranked
    scores = [r.get("total_score", 0) for r in results]
    if scores != sorted(scores, reverse=True):
        errors.append("Results: Not properly sorted by score")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def sanitize_llm_output(text: str) -> str:
    """
    Clean up LLM output to extract JSON
    
    Args:
        text: Raw LLM output
        
    Returns:
        Cleaned text
    """
    # Remove markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    
    # Remove common prefixes
    prefixes = ["Here is", "Here's", "The JSON", "Output:", "Result:"]
    for prefix in prefixes:
        if text.strip().startswith(prefix):
            text = text.split(":", 1)[-1]
    
    return text.strip()


def check_score_consistency(breakdown: Dict, total: float, weights: Dict) -> bool:
    """
    Verify that total score matches weighted breakdown
    
    Args:
        breakdown: Agent breakdown dictionary
        total: Reported total score
        weights: Weight configuration
        
    Returns:
        True if consistent, False otherwise
    """
    tech_score = breakdown.get("technical", {}).get("score", 0)
    career_score = breakdown.get("career", {}).get("score", 0)
    fit_score = breakdown.get("fit", {}).get("score", 0)
    
    calculated_total = (
        tech_score * weights["technical"] +
        career_score * weights["career"] +
        fit_score * weights["fit"]
    )
    
    # Allow small floating point difference
    return abs(calculated_total - total) < 0.1