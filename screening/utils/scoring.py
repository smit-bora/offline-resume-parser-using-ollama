# screening/utils/scoring.py

from typing import Dict


def combine_scores(technical: Dict, career: Dict, fit: Dict, weights: Dict) -> Dict:
    """
    Combine agent scores into final weighted score
    
    Args:
        technical: Score dict from SkillAgent
        career: Score dict from ExperienceAgent
        fit: Score dict from FitAgent
        weights: Weight dictionary from config
        
    Returns:
        {
            "total": float (0-100),
            "breakdown": {
                "technical": {...},
                "career": {...},
                "fit": {...}
            },
            "weighted_scores": {
                "technical": float,
                "career": float,
                "fit": float
            }
        }
    """
    # Extract scores
    tech_score = technical.get("score", 0)
    career_score = career.get("score", 0)
    fit_score = fit.get("score", 0)
    
    # Apply weights
    weighted_tech = tech_score * weights["technical"]
    weighted_career = career_score * weights["career"]
    weighted_fit = fit_score * weights["fit"]
    
    # Calculate total
    total_score = weighted_tech + weighted_career + weighted_fit
    
    return {
        "total": round(total_score, 2),
        "breakdown": {
            "technical": technical,
            "career": career,
            "fit": fit
        },
        "weighted_scores": {
            "technical": round(weighted_tech, 2),
            "career": round(weighted_career, 2),
            "fit": round(weighted_fit, 2)
        }
    }


def normalize_score(score: float, min_val: float = 0, max_val: float = 100) -> float:
    """
    Normalize score to be within valid range
    
    Args:
        score: Raw score
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Normalized score
    """
    return max(min_val, min(max_val, score))


def calculate_percentile_rank(scores: list, target_score: float) -> float:
    """
    Calculate percentile rank of a score within a list
    
    Args:
        scores: List of all scores
        target_score: Score to rank
        
    Returns:
        Percentile (0-100)
    """
    if not scores:
        return 50.0
    
    below_count = sum(1 for s in scores if s < target_score)
    percentile = (below_count / len(scores)) * 100
    
    return round(percentile, 1)


def get_score_tier(score: float) -> str:
    """
    Get qualitative tier for a score
    
    Args:
        score: Score value (0-100)
        
    Returns:
        Tier label
    """
    if score >= 90:
        return "Exceptional"
    elif score >= 75:
        return "Strong"
    elif score >= 60:
        return "Adequate"
    elif score >= 45:
        return "Below Average"
    else:
        return "Poor"


def calculate_confidence_score(agent_scores: Dict) -> float:
    """
    Calculate confidence level based on score variance
    
    Args:
        agent_scores: Dictionary of agent scores
        
    Returns:
        Confidence score (0-100)
    """
    scores = [
        agent_scores.get("technical", {}).get("score", 50),
        agent_scores.get("career", {}).get("score", 50),
        agent_scores.get("fit", {}).get("score", 50)
    ]
    
    # Calculate variance
    mean_score = sum(scores) / len(scores)
    variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
    std_dev = variance ** 0.5
    
    # Lower variance = higher confidence
    # Max std_dev of 50 (scores 0, 50, 100) = 0% confidence
    # Min std_dev of 0 (all same) = 100% confidence
    confidence = max(0, 100 - (std_dev * 2))
    
    return round(confidence, 2)


def aggregate_category_scores(breakdown: Dict) -> Dict:
    """
    Aggregate all category scores from agent breakdowns
    
    Args:
        breakdown: Breakdown dict with all agent results
        
    Returns:
        Dictionary of all category scores
    """
    categories = {}
    
    # Extract from technical agent
    tech_categories = breakdown.get("technical", {}).get("category_scores", {})
    for key, value in tech_categories.items():
        categories[f"tech_{key}"] = value
    
    # Extract from career agent
    career_categories = breakdown.get("career", {}).get("category_scores", {})
    for key, value in career_categories.items():
        categories[f"career_{key}"] = value
    
    # Extract from fit agent
    fit_categories = breakdown.get("fit", {}).get("category_scores", {})
    for key, value in fit_categories.items():
        categories[f"fit_{key}"] = value
    
    return categories


def compare_candidates(candidate1: Dict, candidate2: Dict) -> Dict:
    """
    Compare two candidates and return differences
    
    Args:
        candidate1: First candidate result dict
        candidate2: Second candidate result dict
        
    Returns:
        Comparison summary
    """
    score_diff = candidate1["total_score"] - candidate2["total_score"]
    
    comparison = {
        "score_difference": round(score_diff, 2),
        "winner": candidate1["name"] if score_diff > 0 else candidate2["name"],
        "technical_diff": (
            candidate1["breakdown"]["technical"]["score"] - 
            candidate2["breakdown"]["technical"]["score"]
        ),
        "career_diff": (
            candidate1["breakdown"]["career"]["score"] - 
            candidate2["breakdown"]["career"]["score"]
        ),
        "fit_diff": (
            candidate1["breakdown"]["fit"]["score"] - 
            candidate2["breakdown"]["fit"]["score"]
        )
    }
    
    return comparison