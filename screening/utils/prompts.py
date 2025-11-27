# screening/utils/prompts.py

def get_jd_parser_prompt(jd_text: str) -> str:
    """Get prompt for job description parsing"""
    return f"""Analyze this job description and extract key information in JSON format.

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


def get_skill_agent_prompt(candidate_context: str, jd_context: str) -> str:
    """Get prompt for skill evaluation agent"""
    return f"""You are an expert technical recruiter evaluating a candidate's technical competency and achievements.

Evaluate based on:
1. Core Technical Competencies - match with required skills
2. Supporting Technical Competencies - breadth of tech stack
3. Tools & Frameworks familiarity
4. Skill Depth vs Breadth (specialist vs generalist)
5. Transferable Skills evident in projects
6. Quantifiable Achievements (impact, metrics, scale)
7. Awards, Recognitions, Patents, Publications
8. Open Source / Portfolio Contributions
9. Thought Leadership Evidence

Scoring Guidelines:
- 90-100: Exceptional match, strong achievements, clear expertise
- 75-89: Strong match, good achievements, proven skills
- 60-74: Adequate match, some achievements, developing skills
- 45-59: Partial match, limited achievements, gaps in key areas
- 0-44: Poor match, no relevant achievements, significant skill gaps

=== CANDIDATE INFORMATION ===
{candidate_context}

=== JOB REQUIREMENTS ===
{jd_context}

=== INSTRUCTIONS ===
Analyze the candidate's technical profile against job requirements.

Provide category scores for:
- core_technical_match: How well do their skills match required skills?
- breadth_and_depth: Balance of specialization vs versatility
- hands_on_evidence: Quality of projects and practical work
- achievements_impact: Significance of accomplishments
- emerging_tech: Familiarity with modern/cutting-edge technologies

Consider:
- Direct skill matches vs transferable skills
- Project complexity and technologies used
- Quantifiable impact in achievements
- Continuous learning indicators

Return your response as a valid JSON object with the following structure:
{{
  "score": <number 0-100>,
  "reasoning": "<brief explanation>",
  "strengths": ["<strength1>", "<strength2>", ...],
  "weaknesses": ["<weakness1>", "<weakness2>", ...],
  "category_scores": {{
    "core_technical_match": <score>,
    "breadth_and_depth": <score>,
    "hands_on_evidence": <score>,
    "achievements_impact": <score>,
    "emerging_tech": <score>
  }}
}}

Do not include any text outside the JSON object."""


def get_experience_agent_prompt(candidate_context: str, jd_context: str) -> str:
    """Get prompt for experience evaluation agent"""
    return f"""You are an expert career analyst evaluating a candidate's employment history and progression.

Evaluate based on:
1. Career Stability & Employment History
   - Average tenure (short stints <1.5yr vs healthy tenure)
   - Consistency of roles (logical transitions vs random switches)
   - Career gaps (duration, frequency)
   - Company type exposure (startups vs MNCs)
   
2. Career Progression & Evolution
   - Trajectory (fresher → mid → senior → leadership)
   - Skill evolution (technical → strategic/leadership)
   - Promotion evidence (internal growth vs lateral moves)
   - Complexity of roles over time
   - Pattern of responsibility increase
   
3. Risk Indicators
   - Frequent job hops (<1.5 yrs repeatedly)
   - Overqualification (career regression)
   - Unexplained gaps
   - Role inconsistencies

Scoring Guidelines:
- 90-100: Exceptional stability, clear progression, strong trajectory
- 75-89: Good stability, steady growth, logical career moves
- 60-74: Adequate experience, some progression, minor concerns
- 45-59: Unstable history, limited growth, multiple red flags
- 0-44: High risk, poor stability, unclear trajectory

=== CANDIDATE INFORMATION ===
{candidate_context}

=== JOB REQUIREMENTS ===
{jd_context}

=== INSTRUCTIONS ===
Analyze the candidate's career history against job requirements.

Provide category scores for:
- stability_score: Job tenure patterns and consistency
- progression_score: Career growth and skill evolution
- role_relevance: How relevant is their experience to this role?
- risk_assessment: Any red flags or concerns?
- trajectory_strength: Quality of career path and future potential

Consider:
- Whether experience meets minimum requirements
- Quality of career moves (strategic vs reactive)
- Evidence of increasing responsibility
- Company reputation and role complexity
- Any gaps or concerning patterns

Return your response as a valid JSON object with the following structure:
{{
  "score": <number 0-100>,
  "reasoning": "<brief explanation>",
  "strengths": ["<strength1>", "<strength2>", ...],
  "weaknesses": ["<weakness1>", "<weakness2>", ...],
  "category_scores": {{
    "stability_score": <score>,
    "progression_score": <score>,
    "role_relevance": <score>,
    "risk_assessment": <score>,
    "trajectory_strength": <score>
  }}
}}

Do not include any text outside the JSON object."""


def get_fit_agent_prompt(candidate_context: str, jd_context: str) -> str:
    """Get prompt for fit evaluation agent"""
    return f"""You are an expert organizational psychologist and resume analyst evaluating candidate fit.

Evaluate based on:
1. Resume Quality & Communication
   - Clarity and structure (organized, ATS-friendly)
   - Professional presentation
   - Clarity of contributions (impact-based vs generic)
   - Use of quantifiable data
   - Career storytelling quality
   
2. Attitude, Aptitude & Psychological Indicators
   - Stability indicators (tenure patterns)
   - Learning aptitude (upskilling, certifications, cross-domain)
   - Risk appetite (startup experience, role transitions)
   - Adaptability (different domains, multi-functional exposure)
   - Ambition indicator (fast progression, challenging projects)
   - Ownership/impact orientation ("delivered, built" vs "assisted, helped")
   - Confidence balance (realistic vs inflated/humble)
   
3. Cultural & Organizational Fit
   - Team leadership/management exposure
   - Work environment familiarity (startup vs corporate)
   - Cross-cultural work experience
   - Alignment to role level (not over/under qualified)

Scoring Guidelines:
- 90-100: Exceptional fit, strong cultural alignment, outstanding presentation
- 75-89: Good fit, clear alignment, professional quality
- 60-74: Adequate fit, reasonable alignment, acceptable quality
- 45-59: Questionable fit, weak alignment, quality concerns
- 0-44: Poor fit, misalignment, significant quality issues

=== CANDIDATE INFORMATION ===
{candidate_context}

=== JOB REQUIREMENTS ===
{jd_context}

=== INSTRUCTIONS ===
Analyze the candidate's fit and soft indicators.

Provide category scores for:
- resume_quality: Presentation, clarity, professionalism
- learning_attitude: Evidence of growth mindset and adaptability
- cultural_alignment: Match with company culture and work style
- ownership_mindset: Proactive vs reactive work approach
- communication_skills: Clarity in expressing achievements and contributions

Consider:
- How well does the resume tell a compelling story?
- Evidence of continuous learning and skill development
- Balance between stability and ambition
- Alignment with role expectations and company culture
- Red flags in presentation or content

Return your response as a valid JSON object with the following structure:
{{
  "score": <number 0-100>,
  "reasoning": "<brief explanation>",
  "strengths": ["<strength1>", "<strength2>", ...],
  "weaknesses": ["<weakness1>", "<weakness2>", ...],
  "category_scores": {{
    "resume_quality": <score>,
    "learning_attitude": <score>,
    "cultural_alignment": <score>,
    "ownership_mindset": <score>,
    "communication_skills": <score>
  }}
}}

Do not include any text outside the JSON object."""