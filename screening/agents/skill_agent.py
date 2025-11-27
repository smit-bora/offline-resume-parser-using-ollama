# screening/agents/skill_agent.py

from typing import Dict
from .base_agent import BaseAgent
from utils.factual_extraction import get_factual_baseline


class SkillAgent(BaseAgent):
    """
    Hybrid Technical Evaluation:
    - Rule-based: Exact skill matching, education relevance
    - LLM: Context adjustment, transferable skills assessment
    """
    
    async def score(self, candidate: Dict, jd_requirements: Dict) -> Dict:
        """Score candidate using hybrid approach"""
        
        # STEP 1: Get factual baseline (rule-based)
        facts = get_factual_baseline(candidate, jd_requirements)
        
        # Calculate base score from facts
        # 60% from skill matching, 40% from education relevance
        skill_score = facts["skill_match_percentage"]
        education_score = facts["education_score"]
        base_score = (skill_score * 0.6) + (education_score * 0.4)
        
        # STEP 2: Build context for LLM
        candidate_context = f"""
FACTUAL DATA (VERIFIED FROM RESUME):
- Candidate's listed skills: {', '.join(facts['candidate_skills']) if facts['candidate_skills'] else 'NONE'}
- Education: {', '.join(facts['degrees']) if facts['degrees'] else 'None listed'}
- Projects: {facts['project_count']} technical projects
- Achievements: {facts['achievement_count']} documented

JOB REQUIREMENTS:
- Required skills: {', '.join(facts['required_skills'])}

RULE-BASED ANALYSIS:
- Exact skill matches: {', '.join(facts['matched_skills']) if facts['matched_skills'] else 'NONE'}
- Missing required skills: {', '.join(facts['missing_skills']) if facts['missing_skills'] else 'NONE'}
- Skill match rate: {facts['skill_match_percentage']:.0f}%
- Education relevance: {facts['education_score']}/100
- Baseline score: {base_score:.0f}/100

PROJECT DETAILS:
{self._format_projects(candidate)}
"""
        
        jd_context = f"""
Required Technical Skills: {', '.join(jd_requirements.get('required_skills', []))}
Preferred Skills: {', '.join(jd_requirements.get('preferred_skills', []))}
Role Level: {jd_requirements.get('role_level', 'Not specified')}
"""
        
        system_message = """You are a technical recruiter providing context-based adjustment to a rule-based score.

IMPORTANT: 
- The factual matching has already been done by rules
- You CANNOT change which skills matched or didn't match
- Your job is to adjust the baseline score by -10 to +10 points based on:
  1. Transferable skills (e.g., Java experience helps with Python)
  2. Project portfolio quality (hands-on evidence)
  3. Learning potential (related background)
  4. Depth vs breadth considerations

RULES:
- If candidate has 0 matching skills and irrelevant background: adjustment = -5 to 0
- If candidate has some matches with good projects: adjustment = 0 to +10
- Your adjustment must be justified by actual data provided
"""
        
        instructions = f"""
Given the baseline score of {base_score:.0f}/100 from rule-based matching:

Provide an adjustment (-10 to +10 points) based on:
1. Are there transferable skills? (e.g., JavaScript → Node.js, Java → backend)
2. Do projects demonstrate practical ability beyond listed skills?
3. Does education background suggest learning capability?
4. Is there potential for quick ramp-up?

Be conservative:
- No technical skills + no projects = negative adjustment
- Some matches + good projects = positive adjustment
- Irrelevant degree + no tech skills = negative adjustment

Return JSON:
{{
  "adjustment": <number -10 to +10>,
  "final_score": <baseline + adjustment>,
  "reasoning": "<justify your adjustment with specific evidence>",
  "strengths": ["<based on factual matched skills>"],
  "weaknesses": ["<based on factual missing skills>"],
  "category_scores": {{
    "skill_match": <skills subscore>,
    "education_relevance": <education subscore>,
    "project_quality": <projects subscore>
  }}
}}
"""
        
        prompt = self._build_prompt(system_message, candidate_context, jd_context, instructions)
        
        # STEP 3: Get LLM adjustment
        llm_result = await self._query_llm(prompt)
        
        # STEP 4: Combine rule-based facts with LLM context
        adjustment = llm_result.get("adjustment", 0)
        adjustment = max(-10, min(10, adjustment))  # Clamp to range
        
        final_score = base_score + adjustment
        final_score = max(0, min(100, final_score))  # Clamp to 0-100
        
        # Use factual matched/missing in output
        return {
            "score": round(final_score, 1),
            "reasoning": f"Matched {len(facts['matched_skills'])}/{len(facts['required_skills'])} skills. {llm_result.get('reasoning', '')}",
            "strengths": [
                f"Has required: {', '.join(facts['matched_skills'][:3])}" if facts['matched_skills'] else "No matching technical skills",
                f"Education: {facts['degrees'][0] if facts['degrees'] else 'Not specified'}"
            ],
            "weaknesses": [
                f"Missing: {', '.join(facts['missing_skills'][:3])}" if facts['missing_skills'] else "No critical skill gaps"
            ],
            "category_scores": {
                "skill_match": round(skill_score, 1),
                "education_relevance": education_score,
                "baseline": round(base_score, 1),
                "llm_adjustment": adjustment,
                "final": round(final_score, 1)
            }
        }
    
    def _format_projects(self, candidate: Dict) -> str:
        """Format projects for LLM context"""
        projects = candidate.get("projects", [])
        
        if not projects:
            return "No projects listed"
        
        formatted = []
        for proj in projects[:5]:
            name = proj.get("name", "Unnamed")
            desc = proj.get("description", "")
            tech = ', '.join(proj.get("technologies", []))
            formatted.append(f"- {name}: {desc[:100]} (Tech: {tech})")
        
        return '\n'.join(formatted)