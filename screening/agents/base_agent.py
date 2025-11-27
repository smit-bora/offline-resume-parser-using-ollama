# screening/agents/base_agent.py

from abc import ABC, abstractmethod
from typing import Dict


class BaseAgent(ABC):
    """Abstract base class for all screening agents"""
    
    def __init__(self, ollama_client):
        self.ollama_client = ollama_client
        self.min_score = 0
        self.max_score = 100
    
    @abstractmethod
    async def score(self, candidate: Dict, jd_requirements: Dict) -> Dict:
        """
        Score a candidate based on specific criteria
        
        Args:
            candidate: Parsed resume JSON
            jd_requirements: Extracted job description requirements
            
        Returns:
            {
                "score": float (0-100),
                "reasoning": str,
                "strengths": list,
                "weaknesses": list,
                "category_scores": dict (optional breakdown)
            }
        """
        pass
    
    def _validate_score(self, score: float) -> float:
        """Ensure score is within valid range"""
        return max(self.min_score, min(self.max_score, score))
    
    def _build_prompt(self, system_message: str, candidate_context: str, jd_context: str, instructions: str) -> str:
        """Build structured prompt for LLM"""
        return f"""{system_message}

=== CANDIDATE INFORMATION ===
{candidate_context}

=== JOB REQUIREMENTS ===
{jd_context}

=== INSTRUCTIONS ===
{instructions}

Return your response as a valid JSON object with the following structure:
{{
  "score": <number 0-100>,
  "reasoning": "<brief explanation>",
  "strengths": ["<strength1>", "<strength2>", ...],
  "weaknesses": ["<weakness1>", "<weakness2>", ...],
  "category_scores": {{
    "<category1>": <score>,
    "<category2>": <score>
  }}
}}

Do not include any text outside the JSON object."""
    
    async def _query_llm(self, prompt: str) -> Dict:
        """Query LLM and parse response"""
        import json
        
        response = await self.ollama_client.query(prompt)
        
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                result = json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                result = json.loads(json_str)
            else:
                # Fallback structure
                result = {
                    "score": 50,
                    "reasoning": "Unable to parse LLM response",
                    "strengths": [],
                    "weaknesses": [],
                    "category_scores": {}
                }
        
        # Validate score
        result["score"] = self._validate_score(result.get("score", 50))
        
        return result