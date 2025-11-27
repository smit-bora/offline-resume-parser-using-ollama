"""
Prompt templates for LLM-based resume parsing and analysis
"""

# Main resume parsing prompt
MAIN_PARSER_PROMPT = """You are a resume parser. Parse this resume and output ONLY valid JSON.

Resume:
{resume_text}

Output this exact JSON structure (fill with extracted data):
{{
  "personal_info": {{"name": "", "email": "", "phone": "", "location": "", "linkedin": "", "github": ""}},
  "summary": "",
  "experience": [{{"company": "", "position": "", "start_date": "", "end_date": "", "responsibilities": []}}],
  "education": [{{"institution": "", "degree": "", "start_date": "", "end_date": "", "gpa": ""}}],
  "skills": {{"technical": [], "soft_skills": [], "tools": []}},
  "certifications": [{{"name": "", "issuer": "", "date": ""}}],
  "projects": [{{"name": "", "description": "", "technologies": [], "link": ""}}],
  "languages": [],
  "achievements": []
}}

CRITICAL RULES:
- Output ONLY the JSON object
- NO explanations before or after
- NO markdown code blocks
- Start response with {{ and end with }}
- Extract ALL information from resume

JSON output:"""


# Resume Analysis Prompts
ANALYSIS_PROMPTS = {
    "career_stability": """Calculate career stability score using this exact formula:

Resume Data:
{resume_json}

STEP 1: Count total jobs in experience array
STEP 2: For each job, calculate months between start_date and end_date
STEP 3: Calculate average tenure: total_months / number_of_jobs / 12
STEP 4: Count short stints: jobs with < 18 months
STEP 5: Calculate score:
   score = 100
   score = score - (short_stints * 15)
   score = score - 30 if avg_tenure < 1 year
   score = score - 20 if avg_tenure < 2 years
   score = max(0, score)

Return ONLY this JSON (NO text, NO explanations):
{{
  "score": X,
  "avg_tenure_years": X.X,
  "short_stints": X,
  "total_jobs": X
}}""",

    "career_progression": """Calculate progression score with this formula:

Resume Data:
{resume_json}

STEP 1: Look at position titles in experience array chronologically
STEP 2: Detect level: trainee/intern=1, associate/junior=2, mid=3, senior/lead=4, manager/founder=5
STEP 3: Check if levels increase over time
STEP 4: Count internal promotions (same company, higher position)
STEP 5: Calculate:
   score = 40 (base)
   score = score + 30 if levels are increasing
   score = score + 15 per internal promotion
   score = score + 15 if current level >= 4

Return ONLY this JSON:
{{
  "score": X,
  "progression": "upward/flat/downward",
  "promotions": X,
  "current_level": X
}}""",

    "skills_competency": """Count skills using exact formula:

Resume Data:
{resume_json}

STEP 1: Count items in skills.technical array
STEP 2: Count items in skills.tools array  
STEP 3: Total = technical + tools
STEP 4: Calculate:
   score = total * 6 (max 60 points)
   score = score + 20 if total >= 10
   score = score + 20 if total >= 15
   score = min(100, score)

Return ONLY this JSON:
{{
  "score": X,
  "total_skills": X,
  "technical": X,
  "tools": X
}}""",

    "resume_quality": """Check sections using formula:

Resume Data:
{resume_json}

STEP 1: Check if these keys exist and are not empty:
   - personal_info
   - experience (array with items)
   - education (array with items)  
   - skills (object with items)
STEP 2: Count sections present
STEP 3: Calculate:
   score = sections_present * 25

Return ONLY this JSON:
{{
  "score": X,
  "sections_present": X,
  "total_sections_checked": 4
}}""",

    "attitude_aptitude": """Count exact items using formula:

Resume Data:
{resume_json}

STEP 1: Count certifications array length
STEP 2: Count projects array length
STEP 3: Calculate:
   score = 0
   score = score + (certifications * 20)
   score = score + (projects * 10)
   score = min(100, score)

Return ONLY this JSON:
{{
  "score": X,
  "certifications": X,
  "projects": X
}}""",

    "achievements": """Count achievements using formula:

Resume Data:
{resume_json}

STEP 1: Search all text for numbers (50K, 3rd place, 8.11 GPA, etc.)
STEP 2: Count occurrences of quantified data
STEP 3: Count achievements/awards arrays
STEP 4: Calculate:
   score = quantified_items * 15
   score = min(100, score)

Return ONLY this JSON:
{{
  "score": X,
  "quantified_items": X,
  "awards": X
}}""",

    "cultural_fit": """Check keywords using formula:

Resume Data:
{resume_json}

STEP 1: Search for: "led", "managed", "founded", "co-founded"
STEP 2: Count unique companies in experience
STEP 3: Calculate:
   score = 0
   score = score + 40 if leadership_words found
   score = score + 20 per company (max 60)

Return ONLY this JSON:
{{
  "score": X,
  "has_leadership": true/false,
  "companies": X
}}""",

    "risk_indicators": """Count red flags using formula:

Resume Data:
{resume_json}

STEP 1: For each job, calculate duration in months
STEP 2: Count jobs with < 18 months (short_jobs)
STEP 3: Calculate:
   score = 100
   score = score - (short_jobs * 20)
   score = max(0, score)

Return ONLY this JSON:
{{
  "score": X,
  "short_jobs": X,
  "total_jobs": X
}}"""

}


# System prompts for different models
SYSTEM_PROMPTS = {
    "default": "You are a professional resume parser. Extract information accurately and return valid JSON only.",
    
    "analyzer": "You are an expert HR analyst and resume evaluator. Provide objective, data-driven assessments with specific evidence. Always return valid JSON with numeric scores 0-100.",
    
    "strict": "You are a JSON-only resume parser. You MUST return only valid JSON with no additional text, explanations, or markdown formatting."
}


# Prompt templates dictionary for easy access
PROMPTS = {
    "main_parser": MAIN_PARSER_PROMPT,
    "analysis": ANALYSIS_PROMPTS
}


def get_prompt(prompt_type: str, **kwargs) -> str:
    """
    Get a formatted prompt by type
    
    Args:
        prompt_type: Type of prompt to retrieve
        **kwargs: Variables to format into the prompt
    
    Returns:
        Formatted prompt string
    """
    if prompt_type not in PROMPTS:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    prompt_template = PROMPTS[prompt_type]
    
    try:
        return prompt_template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required variable for prompt: {e}")


def get_analysis_prompt(analysis_type: str, resume_json: dict) -> str:
    """
    Get a formatted analysis prompt
    
    Args:
        analysis_type: Type of analysis (career_stability, skills_competency, etc.)
        resume_json: Parsed resume data
    
    Returns:
        Formatted prompt string
    """
    if analysis_type not in ANALYSIS_PROMPTS:
        raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    import json
    prompt_template = ANALYSIS_PROMPTS[analysis_type]
    
    return prompt_template.format(resume_json=json.dumps(resume_json, indent=2))


def get_system_prompt(style: str = "default") -> str:
    """
    Get system prompt by style
    
    Args:
        style: Style of system prompt (default, analyzer, strict)
    
    Returns:
        System prompt string
    """
    return SYSTEM_PROMPTS.get(style, SYSTEM_PROMPTS["default"])