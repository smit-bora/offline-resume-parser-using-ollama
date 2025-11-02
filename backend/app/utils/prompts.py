"""
Prompt templates for LLM-based resume parsing
"""

# Main resume parsing prompt
MAIN_PARSER_PROMPT = """You are an expert resume parser. Extract ALL information from the following resume text and return it as valid JSON.

Resume Text:
{resume_text}

IMPORTANT: Extract EVERY piece of information. Do not skip any sections.

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
4. Extract dates SEPARATELY - do NOT combine "Sept 2023 – May 2027" into one field
5. Don't invent or assume information not in the resume
6. If a section is completely missing, include it with null or empty values
7. Extract ALL skills mentioned anywhere in the resume
8. Extract ALL work experience, internships, and professional roles
9. Include project descriptions in the "description" field
10. Look for LinkedIn, GitHub usernames in the header section

Return the JSON now:"""


# Prompt for extracting specific sections
SECTION_EXTRACTOR_PROMPT = """Extract only the {section_name} section from this resume.

Resume Text:
{resume_text}

Return ONLY a valid JSON {structure_type} with the {section_name} information. No additional text or explanations.

{section_schema}

JSON response:"""


# Personal info extraction prompt
PERSONAL_INFO_PROMPT = """Extract contact and personal information from this resume:

{resume_text}

Return ONLY a valid JSON object:
{{
    "name": "Full name",
    "email": "email@example.com",
    "phone": "phone number",
    "location": "city, state/country",
    "linkedin": "LinkedIn URL",
    "github": "GitHub URL",
    "website": "Personal website"
}}

Use null for any missing information. Return only the JSON."""


# Experience extraction prompt
EXPERIENCE_PROMPT = """Extract all work experience from this resume:

{resume_text}

Return ONLY a valid JSON array of experience entries:
[
    {{
        "company": "Company name",
        "position": "Job title",
        "location": "Location",
        "start_date": "Start date",
        "end_date": "End date or Present",
        "responsibilities": ["Responsibility 1", "Responsibility 2"]
    }}
]

List experiences in reverse chronological order (most recent first). Return only the JSON array."""


# Education extraction prompt
EDUCATION_PROMPT = """Extract all education information from this resume:

{resume_text}

Return ONLY a valid JSON array of education entries:
[
    {{
        "institution": "School/University name",
        "degree": "Degree type and major",
        "location": "Location",
        "start_date": "Start date",
        "end_date": "End date or Present",
        "gpa": "GPA if present"
    }}
]

List in reverse chronological order. Return only the JSON array."""


# Skills extraction prompt
SKILLS_PROMPT = """Extract all skills from this resume and categorize them:

{resume_text}

Return ONLY a valid JSON object:
{{
    "technical": ["Programming languages, frameworks, databases"],
    "soft_skills": ["Communication, leadership, etc"],
    "tools": ["Software tools, platforms"]
}}

Return only the JSON object."""


# Projects extraction prompt
PROJECTS_PROMPT = """Extract all projects from this resume:

{resume_text}

Return ONLY a valid JSON array:
[
    {{
        "name": "Project name",
        "description": "Brief description",
        "technologies": ["tech1", "tech2"],
        "link": "URL if available"
    }}
]

Return only the JSON array."""


# Verification prompt
VERIFICATION_PROMPT = """Review this extracted resume data for accuracy. Original resume:

{resume_text}

Extracted Data:
{extracted_data}

Check for:
1. Incorrect dates or date formats
2. Missing critical information
3. Duplicated entries
4. Misplaced information

If you find any issues, return the corrected JSON. If everything is correct, return the same JSON.

Return ONLY the JSON, no explanations:"""


# Improvement prompt for failed parsing
RETRY_PROMPT = """The previous parsing attempt failed. Please try again with extra care.

Resume Text:
{resume_text}

Previous Error:
{error_message}

Extract resume information and return ONLY valid JSON with no markdown formatting, no code blocks, no explanations.

Start your response with {{ and end with }}

JSON response:"""


# Summary generation prompt
SUMMARY_GENERATION_PROMPT = """Based on this resume data, generate a concise professional summary (2-3 sentences):

{resume_data}

Return only the summary text, no JSON, no additional formatting."""


# Skill categorization prompt
SKILL_CATEGORIZATION_PROMPT = """Categorize these skills into technical, soft_skills, and tools:

Skills: {skills_list}

Return ONLY a valid JSON object:
{{
    "technical": [],
    "soft_skills": [],
    "tools": []
}}"""


# Date normalization prompt
DATE_NORMALIZATION_PROMPT = """Normalize these dates to "MMM YYYY" format or "Present":

Dates to normalize:
{dates_list}

Return ONLY a JSON object mapping original dates to normalized dates:
{{
    "original_date_1": "Jan 2020",
    "original_date_2": "Present"
}}"""


# Few-shot examples for better parsing
FEW_SHOT_EXAMPLE = """Here's an example of correct parsing:

Example Resume Text:
"John Smith
john.smith@email.com | (555) 123-4567 | San Francisco, CA

EXPERIENCE
Software Engineer at Tech Corp
Jan 2020 - Present
- Built scalable microservices
- Led team of 5 engineers"

Example JSON Output:
{{
    "personal_info": {{
        "name": "John Smith",
        "email": "john.smith@email.com",
        "phone": "(555) 123-4567",
        "location": "San Francisco, CA",
        "linkedin": null,
        "github": null,
        "website": null
    }},
    "experience": [
        {{
            "company": "Tech Corp",
            "position": "Software Engineer",
            "location": null,
            "start_date": "Jan 2020",
            "end_date": "Present",
            "responsibilities": [
                "Built scalable microservices",
                "Led team of 5 engineers"
            ]
        }}
    ]
}}

Now parse this resume:
{resume_text}"""


# System prompts for different models
SYSTEM_PROMPTS = {
    "default": "You are a professional resume parser. Extract information accurately and return valid JSON only.",
    
    "detailed": "You are an expert HR professional and data extraction specialist. Your task is to carefully read resumes and extract all relevant information into structured JSON format. Pay attention to dates, job titles, company names, and skills. Be precise and thorough.",
    
    "strict": "You are a JSON-only resume parser. You MUST return only valid JSON with no additional text, explanations, or markdown formatting. Any non-JSON response is incorrect."
}


# Prompt templates dictionary for easy access
PROMPTS = {
    "main_parser": MAIN_PARSER_PROMPT,
    "personal_info": PERSONAL_INFO_PROMPT,
    "experience": EXPERIENCE_PROMPT,
    "education": EDUCATION_PROMPT,
    "skills": SKILLS_PROMPT,
    "projects": PROJECTS_PROMPT,
    "verification": VERIFICATION_PROMPT,
    "retry": RETRY_PROMPT,
    "summary_generation": SUMMARY_GENERATION_PROMPT,
    "skill_categorization": SKILL_CATEGORIZATION_PROMPT,
    "date_normalization": DATE_NORMALIZATION_PROMPT,
    "few_shot": FEW_SHOT_EXAMPLE,
    "section_extractor": SECTION_EXTRACTOR_PROMPT
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


def get_system_prompt(style: str = "default") -> str:
    """
    Get system prompt by style
    
    Args:
        style: Style of system prompt (default, detailed, strict)
    
    Returns:
        System prompt string
    """
    return SYSTEM_PROMPTS.get(style, SYSTEM_PROMPTS["default"])