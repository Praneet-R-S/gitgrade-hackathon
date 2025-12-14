import base64
from github_fetcher import GitHubFetcher
from signals import SignalDetector
from tier_profiler import TierProfile
from typing import Dict, Any

class RepositoryAnalyzer:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.fetcher = GitHubFetcher(repo_url)
    
    def analyze(self) -> Dict[str, Any]:
        """Main analysis pipeline - FULLY FIXED"""
        try:
            # Fetch all data
            print("📦 Fetching repository data...")
            repo_info = self.fetcher.get_repo_info()
            file_tree = self.fetcher.get_file_tree()
            readme_content = self.fetcher.get_readme()
            commits = self.fetcher.get_commits()
            branches = self.fetcher.get_branches()
            languages = self.fetcher.get_languages()
            
            # Decode README if base64 encoded
            readme = ""
            if readme_content:
                try:
                    if isinstance(readme_content, str) and len(readme_content) > 100:
                        readme = base64.b64decode(readme_content).decode('utf-8')
                    else:
                        readme = readme_content
                except:
                    readme = str(readme_content)[:2000]  # Fallback
            
            # Detect signals
            print("🔍 Analyzing signals...")
            detector = SignalDetector(file_tree, readme, commits, branches, languages)
            signals = detector.get_all_signals()
            
            # Compute profile vector (pure integers)
            profile_vector = TierProfile.compute_profile_vector(signals)
            tier, similarity = TierProfile.match_tier(profile_vector)
            gaps = TierProfile.compute_gaps(profile_vector, tier)
            
            # Compute total score (0-100)
            score = sum(profile_vector.values())
            
            # FIXED: Safe summary generation
            strengths = sorted([(k, v) for k, v in profile_vector.items()], 
                             key=lambda x: x[1], reverse=True)[:2]
            weaknesses = sorted([(k, v) for k, v in profile_vector.items()], 
                              key=lambda x: x[1])[:2]
            
            # Safe display names mapping
            display_names = {
                "structure": "Project Structure",
                "documentation": "Documentation", 
                "tests": "Testing",
                "commits": "Commit Quality",
                "dependencies": "Dependency Management"
            }
            
            strength_names = [display_names.get(s[0], s[0].title()) for s in strengths]
            weakness_names = [display_names.get(w[0], w[0].title()) for w in weaknesses]
            
            strength_text = ", ".join(strength_names)
            weakness_text = ", ".join(weakness_names)
            
            summary = f"Strong in {strength_text}. Needs improvement in {weakness_text}."
            
            # Generate personalized roadmap
            roadmap = self._generate_roadmap(gaps, profile_vector)
            
            return {
                "score": min(100, max(0, score)),  # Clamp 0-100
                "tier": tier.title(),
                "tier_similarity": round(similarity * 100, 1),
                "profile": profile_vector,
                "gaps": gaps,
                "signals": {k: v[1] for k, v in signals.items()},
                "summary": summary,
                "roadmap": roadmap,
                "repo_info": repo_info,
                "commit_count": len(commits),
                "branch_count": len(branches),
                "languages": languages,
                "status": "success"
            }
        
        except Exception as e:
            print(f"Analysis error: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "status": "error"
            }
    
    def _generate_roadmap(self, gaps: Dict[str, int], profile: Dict[str, int]) -> list:
        """Generate actionable, personalized roadmap items"""
        roadmap = []
        
        display_roadmap = {
            "structure": "📁 Reorganize into semantic folders (src/, tests/, docs/, config/) instead of utils/helpers",
            "documentation": "📝 Add comprehensive README: Overview, Setup, Usage, Architecture sections with code examples",
            "tests": "✅ Implement test strategy: unit tests for core logic, integration tests for APIs, coverage >70%",
            "commits": "📌 Use conventional commits (feat:, fix:, docs:) with descriptive messages, commit regularly",
            "dependencies": "📦 Add lock files (package-lock.json, poetry.lock) and pin dependency versions"
        }
        
        # Priority 1: Big gaps (>8 points)
        for dimension, gap in gaps.items():
            if gap > 8:
                roadmap.append(f"🔥 HIGH PRIORITY: {display_roadmap.get(dimension, 'Improve this area')}")
        
        # Priority 2: Medium gaps (4-8 points)
        for dimension, gap in gaps.items():
            if 4 <= gap <= 8:
                roadmap.append(f"📈 {display_roadmap.get(dimension, 'Address this gap')}")
        
        # Advanced recommendations for high performers
        if sum(profile.values()) > 80:
            roadmap.extend([
                "🚀 Add GitHub Actions for CI/CD: automated testing and deployment",
                "🌐 Set up issue templates and project boards for better collaboration",
                "📊 Add code coverage badges and dependency update workflows"
            ])
        
        if not roadmap:
            roadmap = ["🌟 Excellent repository! Consider open-sourcing or contributing to existing projects."]
        
        return roadmap[:5]  # Limit to top 5 recommendations
