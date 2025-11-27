# screening/parsers/jd_parser.py

import json
from typing import Dict


async def parse_job_description(jd_text: str, ollama_client) -> Dict:
    """Extract structured requirements from job description text"""
    
    prompt = f"""Analyze this job description and extract key information in JSON format.

Job Description:
{jd_text}

Extract the following information:
1. Required technical skills (list)
2. Preferred/nice-to-have skills (list)
3. Minimum years of experience required (number, if not mentioned use 0)
4. Education requirements (string)
5. Role level (entry/mid/senior/lead)
6. Key responsibilities (list)
7. Company culture indicators (list of keywords like "startup", "collaborative", "fast-paced", etc.)
8. Domain/industry (string)
9. Must-have qualifications (list)
10. Red flags to watch for (list - like "frequent job hopping", "lack of relevant experience")

Return ONLY a valid JSON object with these keys:
{{
  "required_skills": [],
  "preferred_skills": [],
  "min_experience_years": 0,
  "education_requirements": "",
  "role_level": "",
  "key_responsibilities": [],
  "culture_indicators": [],
  "domain": "",
  "must_have_qualifications": [],
  "risk_factors_to_watch": []
}}

Do not include any explanation, only return the JSON object."""

    response = await ollama_client.query(prompt)
    
    try:
        # Try to parse JSON from response
        jd_requirements = json.loads(response)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from markdown code blocks
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
            jd_requirements = json.loads(json_str)
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
            jd_requirements = json.loads(json_str)
        else:
            # Last resort: return minimal structure
            jd_requirements = {
                "required_skills": [],
                "preferred_skills": [],
                "min_experience_years": 0,
                "education_requirements": "",
                "role_level": "mid",
                "key_responsibilities": [],
                "culture_indicators": [],
                "domain": "",
                "must_have_qualifications": [],
                "risk_factors_to_watch": []
            }
    
    return jd_requirements