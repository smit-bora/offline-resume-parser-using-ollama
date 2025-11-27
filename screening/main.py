# screening/main.py

import asyncio
import json
from pathlib import Path
from typing import List, Dict
import time

from config import RESUME_DIR, WEIGHTS, OLLAMA_MODEL
from services.json_loader import load_resumes
from services.ollama_client import OllamaClient
from parsers.jd_parser import parse_job_description
from agents.skill_agent import SkillAgent
from agents.experience_agent import ExperienceAgent
from agents.fit_agent import FitAgent
from utils.scoring import combine_scores


async def score_candidate(
    candidate: Dict,
    jd_requirements: Dict,
    ollama_client: OllamaClient
) -> Dict:
    """Score a single candidate using all three agents in parallel"""
    
    skill_agent = SkillAgent(ollama_client)
    exp_agent = ExperienceAgent(ollama_client)
    fit_agent = FitAgent(ollama_client)
    
    # Run agents in parallel
    results = await asyncio.gather(
        skill_agent.score(candidate, jd_requirements),
        exp_agent.score(candidate, jd_requirements),
        fit_agent.score(candidate, jd_requirements)
    )
    
    # Combine scores
    final_score = combine_scores(
        technical=results[0],
        career=results[1],
        fit=results[2],
        weights=WEIGHTS
    )
    
    return {
        "candidate_id": candidate.get("_id", "unknown"),
        "name": candidate["personal_info"]["name"],
        "email": candidate["personal_info"]["email"],
        "phone": candidate["personal_info"].get("phone", "N/A"),
        "total_score": final_score["total"],
        "breakdown": final_score["breakdown"]
    }


async def screen_candidates(jd_text: str, resume_dir: Path = RESUME_DIR) -> List[Dict]:
    """Main screening pipeline"""
    
    start_time = time.time()
    
    # Initialize Ollama client
    ollama_client = OllamaClient()
    
    # Parse job description
    print("Parsing job description...")
    jd_requirements = await parse_job_description(jd_text, ollama_client)
    
    # Load resume JSONs
    print(f"Loading resumes from {resume_dir}...")
    candidates = load_resumes(resume_dir)
    print(f"Found {len(candidates)} candidates")
    
    # Score each candidate
    results = []
    for idx, candidate in enumerate(candidates, 1):
        print(f"Screening candidate {idx}/{len(candidates)}: {candidate['personal_info']['name']}...")
        result = await score_candidate(candidate, jd_requirements, ollama_client)
        results.append(result)
    
    # Rank by score
    ranked_results = sorted(results, key=lambda x: x["total_score"], reverse=True)
    
    end_time = time.time()
    screening_time = end_time - start_time
    
    return ranked_results, screening_time


def display_results(results: List[Dict], screening_time: float):
    """Display screening results in terminal"""
    
    print("\n" + "="*60)
    print("SCREENING RESULTS")
    print("="*60 + "\n")
    
    for rank, candidate in enumerate(results, 1):
        print(f"{rank}. {candidate['name']} - Score: {candidate['total_score']:.1f}/100")
        print(f"   Email: {candidate['email']}")
        print(f"   Phone: {candidate['phone']}")
        print()
    
    print("="*60)
    print(f"Total screening time: {screening_time:.1f} seconds")
    print("="*60)


async def main():
    """Entry point"""
    
    # Example job description (replace with user input)
    jd_text = """
    We are looking for a Python Developer with 2+ years of experience.
    
    Required Skills:
    - Strong Python programming
    - Web development (Django/Flask)
    - Git version control
    - Database knowledge (SQL)
    
    Nice to have:
    - JavaScript/React
    - Docker/AWS
    - Machine Learning basics
    
    The ideal candidate should have:
    - Strong problem-solving skills
    - Team collaboration experience
    - Good communication skills
    - Startup experience preferred
    """
    
    results, screening_time = await screen_candidates(jd_text)
    display_results(results, screening_time)


if __name__ == "__main__":
    asyncio.run(main())