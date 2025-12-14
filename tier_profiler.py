import math
from typing import Dict, Tuple

class TierProfile:
    """Reference profiles for Beginner, Intermediate, Advanced tiers"""
    
    TIER_PROFILES = {
        "beginner": {
            "structure": 5,
            "documentation": 3,
            "tests": 0,
            "commits": 4,
            "dependencies": 2,
        },
        "intermediate": {
            "structure": 14,
            "documentation": 12,
            "tests": 10,
            "commits": 12,
            "dependencies": 12,
        },
        "advanced": {
            "structure": 18,
            "documentation": 18,
            "tests": 18,
            "commits": 16,
            "dependencies": 18,
        }
    }
    
    @staticmethod
    def compute_profile_vector(signals: Dict[str, Tuple[int, str]]) -> Dict[str, int]:
        """FIXED: Extract ONLY numeric scores from signals (tuples -> ints)"""
        return {
            "structure": signals["structure"][0],      # Extract FIRST element (int)
            "documentation": signals["documentation"][0],
            "tests": signals["tests"][0],
            "commits": signals["commits"][0],
            "dependencies": signals["dependencies"][0],
        }
    
    @staticmethod
    def cosine_similarity(vec1: Dict[str, int], vec2: Dict[str, int]) -> float:
        """Calculate cosine similarity between two 5D vectors"""
        dot_product = sum(vec1[k] * vec2[k] for k in vec1.keys())
        mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0
        return dot_product / (mag1 * mag2)
    
    @staticmethod
    def match_tier(profile_vector: Dict[str, int]) -> Tuple[str, float]:
        """Find which tier the repo closest matches"""
        best_tier = None
        best_similarity = -1
        
        for tier, tier_profile in TierProfile.TIER_PROFILES.items():
            similarity = TierProfile.cosine_similarity(profile_vector, tier_profile)
            if similarity > best_similarity:
                best_similarity = similarity
                best_tier = tier
        
        return best_tier, best_similarity
    
    @staticmethod
    def compute_gaps(profile_vector: Dict[str, int], current_tier: str) -> Dict[str, int]:
        """Calculate gap between current profile and next tier up"""
        tier_order = ["beginner", "intermediate", "advanced"]
        current_idx = tier_order.index(current_tier)
        
        if current_idx == 2:  # Already advanced
            next_tier = "advanced"
        else:
            next_tier = tier_order[current_idx + 1]
        
        next_profile = TierProfile.TIER_PROFILES[next_tier]
        
        gaps = {
            dimension: max(0, next_profile[dimension] - profile_vector[dimension])
            for dimension in profile_vector.keys()
        }
        
        return gaps

