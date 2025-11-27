# screening/agents/fit_agent.py

from typing import Dict
from .base_agent import BaseAgent


class FitAgent(BaseAgent):
    """
    Evaluates resume quality, attitude indicators, and cultural fit
    Covers: Resume Quality + Attitude/Aptitude + Cultural Fit
    Weight: 25%
    """
    
    async def score(self, candidate: Dict, jd_requirements: Dict) -> Dict:
        """Score candidate's fit and soft indicators"""
        
        # Extract candidate data
        experience = candidate.get("experience", [])
        projects = candidate.get("projects", [])
        achievements = candidate.get("achievements", [])
        personal_info = candidate.get("personal_info", {})
        
        # Analyze resume structure
        resume_quality = self._assess_resume_quality(candidate)
        
        # Build candidate context
        candidate_context = f"""
Resume Quality Assessment:
{resume_quality}

Work Experience Summary:
{self._summarize_experience(experience)}

Project Portfolio:
{len(projects)} projects demonstrating hands-on work

Achievements & Recognition:
{self._summarize_achievements(achievements)}

Communication & Presentation:
- Contact details provided: {bool(personal_info.get('email')) and bool(personal_info.get('phone'))}
- Professional online presence: {bool(personal_info.get('linkedin'))}
"""
        
        # Build JD context
        jd_context = f"""
Role Level: {jd_requirements.get('role_level', 'mid')}
Culture Indicators: {', '.join(jd_requirements.get('culture_indicators', []))}
Key Responsibilities: {', '.join(jd_requirements.get('key_responsibilities', []))}
Must-Have Qualifications: {', '.join(jd_requirements.get('must_have_qualifications', []))}
"""
        
        # System message
        system_message = """You are an expert organizational psychologist and resume analyst evaluating candidate fit.

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
- 0-44: Poor fit, misalignment, significant quality issues"""
        
        instructions = """Analyze the candidate's fit and soft indicators.

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
- Red flags in presentation or content"""
        
        prompt = self._build_prompt(system_message, candidate_context, jd_context, instructions)
        result = await self._query_llm(prompt)
        
        return result
    
    def _assess_resume_quality(self, candidate: Dict) -> str:
        """Assess overall resume quality"""
        quality_points = []
        
        # Check completeness
        has_experience = bool(candidate.get("experience"))
        has_education = bool(candidate.get("education"))
        has_skills = bool(candidate.get("skills", {}).get("technical"))
        has_projects = bool(candidate.get("projects"))
        
        completeness = sum([has_experience, has_education, has_skills, has_projects])
        quality_points.append(f"Completeness: {completeness}/4 key sections present")
        
        # Check detail level
        exp_count = len(candidate.get("experience", []))
        proj_count = len(candidate.get("projects", []))
        quality_points.append(f"Detail Level: {exp_count} roles, {proj_count} projects documented")
        
        # Check for quantifiable achievements
        achievements = candidate.get("achievements", [])
        has_achievements = bool([a for a in achievements if a])
        quality_points.append(f"Achievements: {'Yes' if has_achievements else 'None listed'}")
        
        # Check structure
        has_validation = "_validation" in candidate
        quality_points.append(f"Structure: {'Well-formatted' if has_validation else 'Basic format'}")
        
        return '\n'.join(quality_points)
    
    def _summarize_experience(self, experience: list) -> str:
        """Summarize work experience for context"""
        if not experience:
            return "No experience listed"
        
        summary = []
        for exp in experience:
            company = exp.get("company", "Unknown")
            position = exp.get("position", "Unknown")
            summary.append(f"- {position} at {company}")
        
        return '\n'.join(summary[:3])  # Top 3 roles
    
    def _summarize_achievements(self, achievements: list) -> str:
        """Summarize achievements"""
        if not achievements or not any(achievements):
            return "No specific achievements listed"
        
        valid_achievements = [a for a in achievements if a and a.get("name")]
        if not valid_achievements:
            return "No specific achievements listed"
        
        return f"{len(valid_achievements)} achievement(s) documented"