"""
Resume Analyzer Service - Analyzes parsed resumes using Ollama
"""
import asyncio
from typing import Dict, List
from app.services.ollama_service import OllamaService
from app.utils.prompts import get_analysis_prompt, get_system_prompt
from app.config import settings


class ResumeAnalyzer:
    """
    Analyzes parsed resume data across 8 key parameters
    """
    
    def __init__(self, ollama_service: OllamaService):
        self.ollama = ollama_service
        
        # Analysis categories
        self.categories = [
            "career_stability",
            "career_progression",
            "skills_competency",
            "resume_quality",
            "attitude_aptitude",
            "achievements",
            "cultural_fit",
            "risk_indicators"
        ]
        
        # Weights for overall score calculation
        self.weights = {
            "career_stability": 0.15,      # 15%
            "career_progression": 0.15,    # 15%
            "skills_competency": 0.20,     # 20%
            "resume_quality": 0.10,        # 10%
            "attitude_aptitude": 0.15,     # 15%
            "achievements": 0.10,          # 10%
            "cultural_fit": 0.10,          # 10%
            "risk_indicators": 0.05        # 5%
        }
    
    async def analyze(self, parsed_resume: Dict) -> Dict:
        """
        Analyze resume across all parameters
        
        Args:
            parsed_resume: Parsed resume JSON from resume parser
        
        Returns:
            Analysis results with scores and explanations
        """
        print("Starting resume analysis across 8 parameters...")
        
        try:
            # Run all analyses in parallel for speed
            tasks = [
                self._analyze_category(category, parsed_resume)
                for category in self.categories
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Build analysis object
            analysis = {}
            for i, category in enumerate(self.categories):
                if isinstance(results[i], Exception):
                    print(f"Error analyzing {category}: {str(results[i])}")
                    # Provide default score on error
                    analysis[category] = {
                        "score": 50,
                        "error": str(results[i]),
                        "explanation": f"Analysis failed for {category}"
                    }
                else:
                    analysis[category] = results[i]
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(analysis)
            analysis["overall_score"] = overall_score
            
            # Add metadata
            analysis["_metadata"] = {
                "analysis_model": settings.OLLAMA_MODEL,
                "categories_analyzed": len(self.categories),
                "weights_used": self.weights
            }
            
            print(f"Analysis complete. Overall score: {overall_score}/100")
            
            return analysis
        
        except Exception as e:
            print(f"Critical error during analysis: {str(e)}")
            raise Exception(f"Resume analysis failed: {str(e)}")
    
    async def _analyze_category(self, category: str, resume_data: Dict) -> Dict:
        """
        Analyze a single category
        
        Args:
            category: Analysis category name
            resume_data: Parsed resume data
        
        Returns:
            Analysis result for this category
        """
        try:
            print(f"Analyzing: {category}...")
            
            # Get the appropriate prompt
            prompt = get_analysis_prompt(category, resume_data)
            
            # Call Ollama with analyzer system prompt
            result = await self.ollama.generate_json(
                prompt=prompt,
                system_prompt=get_system_prompt("analyzer"),
                retry_attempts=2
            )
            
            # Validate score is in range
            if "score" in result:
                result["score"] = max(0, min(100, result["score"]))
            
            print(f"✓ {category}: {result.get('score', 'N/A')}/100")
            
            return result
        
        except Exception as e:
            print(f"✗ {category}: Failed - {str(e)}")
            raise Exception(f"Failed to analyze {category}: {str(e)}")
    
    def _calculate_overall_score(self, analysis: Dict) -> int:
        """
        Calculate weighted overall score
        
        Args:
            analysis: Dictionary with all category results
        
        Returns:
            Weighted overall score (0-100)
        """
        total_score = 0
        total_weight = 0
        
        for category, weight in self.weights.items():
            if category in analysis and "score" in analysis[category]:
                score = analysis[category]["score"]
                total_score += score * weight
                total_weight += weight
        
        if total_weight > 0:
            overall = total_score / total_weight
        else:
            overall = 0
        
        return round(overall)
    
    async def analyze_single_category(self, category: str, resume_data: Dict) -> Dict:
        """
        Analyze just one category (useful for testing)
        
        Args:
            category: Category name to analyze
            resume_data: Parsed resume data
        
        Returns:
            Analysis result for the category
        """
        if category not in self.categories:
            raise ValueError(f"Unknown category: {category}")
        
        return await self._analyze_category(category, resume_data)
    
    def get_category_weights(self) -> Dict[str, float]:
        """
        Get the current scoring weights
        
        Returns:
            Dictionary of category weights
        """
        return self.weights.copy()
    
    def update_weights(self, new_weights: Dict[str, float]):
        """
        Update scoring weights (must sum to 1.0)
        
        Args:
            new_weights: New weight dictionary
        """
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        for category in new_weights:
            if category not in self.categories:
                raise ValueError(f"Unknown category: {category}")
        
        self.weights.update(new_weights)
        print(f"Updated weights: {self.weights}")


# Helper function to format analysis for display
def format_analysis_summary(analysis: Dict) -> str:
    """
    Create a human-readable summary of analysis
    
    Args:
        analysis: Analysis results dictionary
    
    Returns:
        Formatted summary string
    """
    summary_lines = [
        f"Overall Score: {analysis.get('overall_score', 'N/A')}/100\n",
        "=" * 50
    ]
    
    categories = [
        "career_stability",
        "career_progression",
        "skills_competency",
        "resume_quality",
        "attitude_aptitude",
        "achievements",
        "cultural_fit",
        "risk_indicators"
    ]
    
    for category in categories:
        if category in analysis:
            data = analysis[category]
            score = data.get("score", "N/A")
            explanation = data.get("explanation", "No explanation provided")
            
            summary_lines.append(f"\n{category.replace('_', ' ').title()}: {score}/100")
            summary_lines.append(f"  {explanation}")
    
    return "\n".join(summary_lines)