# screening/agents/experience_agent.py

from typing import Dict
from .base_agent import BaseAgent
from utils.factual_extraction import get_factual_baseline


class ExperienceAgent(BaseAgent):
    """
    Hybrid Experience Evaluation:
    - Rule-based: Years calculation, role relevance
    - LLM: Career progression assessment, stability analysis
    """
    
    async def score(self, candidate: Dict, jd_requirements: Dict) -> Dict:
        """Score candidate using hybrid approach"""
        
        # STEP 1: Get factual baseline
        facts = get_factual_baseline(candidate, jd_requirements)
        
        years = facts["years_of_experience"]
        min_required = facts["min_required_years"]
        role_relevant = facts["role_relevant"]
        
        # Calculate base score from years
        if min_required == 0:
            year_score = min(100, 50 + (years * 10))
        elif years >= min_required * 1.5:
            year_score = 100
        elif years >= min_required:
            year_score = 90
        elif years >= min_required * 0.75:
            year_score = 70
        else:
            year_score = max(20, (years / min_required) * 70)
        
        # Adjust for role relevance
        if not role_relevant and years > 0:
            year_score = year_score * 0.6  # 40% penalty for irrelevant experience
        
        base_score = year_score
        
        # STEP 2: Build context for LLM
        experience = candidate.get("experience", [])
        experience_summary = self._format_experience(experience)
        
        candidate_context = f"""
FACTUAL DATA (VERIFIED FROM RESUME):
- Total years of experience: {years} years
- Required experience: {min_required} years
- Number of roles: {len(experience)}
- Role relevance: {"YES - has relevant technical roles" if role_relevant else "NO - roles not relevant to technical position"}
- Relevant roles: {', '.join(facts['relevant_roles']) if facts['relevant_roles'] else 'None'}
- All roles: {', '.join(facts['all_roles'])}

EXPERIENCE HISTORY:
{experience_summary}

RULE-BASED SCORE: {base_score:.0f}/100
"""
        
        jd_context = f"""
Minimum Experience: {min_required} years
Role Level: {jd_requirements.get('role_level', 'Not specified')}
"""
        
        system_message = """You are a career analyst providing context-based adjustment to a rule-based experience score.

IMPORTANT:
- Years of experience have been calculated from dates (factual)
- Role relevance has been determined by keyword matching (factual)
- Your job is to assess career progression quality and adjust score by -10 to +10

Consider:
1. Career trajectory (progression vs stagnation)
2. Job stability (tenure patterns)
3. Company quality/reputation
4. Role complexity evolution
"""
        
        instructions = f"""
Given baseline score of {base_score:.0f}/100 from:
- {years} years experience (required: {min_required})
- Role relevance: {role_relevant}

Provide adjustment (-10 to +10) based on:
1. Career progression - are they growing in responsibility?
2. Job stability - concerning frequent switches (<1.5 yr) or healthy tenure?
3. Career trajectory - upward, lateral, or downward?
4. Role alignment - even if not technical, is there transferable leadership?

Be harsh if:
- Irrelevant experience with no progression
- Very short tenures repeatedly
- Career regression evident

Be generous if:
- Clear upward trajectory
- Stable tenure with growth
- Increasing responsibility

Return JSON:
{{
  "adjustment": <-10 to +10>,
  "final_score": <baseline + adjustment>,
  "reasoning": "<justify adjustment>",
  "strengths": ["<based on actual roles>"],
  "weaknesses": ["<based on gaps/concerns>"],
  "category_scores": {{
    "years_match": <subscore>,
    "role_relevance": <subscore>,
    "progression_quality": <subscore>
  }}
}}
"""
        
        prompt = self._build_prompt(system_message, candidate_context, jd_context, instructions)
        
        # STEP 3: Get LLM adjustment
        llm_result = await self._query_llm(prompt)
        
        adjustment = max(-10, min(10, llm_result.get("adjustment", 0)))
        final_score = max(0, min(100, base_score + adjustment))
        
        return {
            "score": round(final_score, 1),
            "reasoning": f"{years} yrs experience (required: {min_required}). Roles {'relevant' if role_relevant else 'NOT relevant'}. {llm_result.get('reasoning', '')}",
            "strengths": [
                f"Has {years} years of experience",
                f"Relevant roles: {', '.join(facts['relevant_roles'][:2])}" if facts['relevant_roles'] else "Experience in different domain"
            ],
            "weaknesses": [
                f"Below {min_required} year requirement" if years < min_required else "",
                "No relevant technical experience" if not role_relevant else ""
            ],
            "category_scores": {
                "years": round(year_score, 1),
                "baseline": round(base_score, 1),
                "llm_adjustment": adjustment,
                "final": round(final_score, 1)
            }
        }
    
    def _format_experience(self, experience: list) -> str:
        """Format experience for LLM"""
        if not experience:
            return "No experience listed"
        
        formatted = []
        for exp in experience:
            company = exp.get("company", "Unknown")
            position = exp.get("position", "Unknown")
            start = exp.get("start_date", "")
            end = exp.get("end_date", "Present")
            formatted.append(f"- {position} at {company} ({start} - {end})")
        
        return '\n'.join(reversed(formatted))  # Chronological order