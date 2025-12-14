import os
from typing import Dict, List, Tuple
from collections import defaultdict

class SignalDetector:
    """Extract 5 key maturity signals from repo data"""
    
    def __init__(self, file_tree: List[Dict], readme: str, commits: List[Dict], 
                 branches: List[str], languages: Dict):
        self.file_tree = file_tree
        self.readme = readme
        self.commits = commits
        self.branches = branches
        self.languages = languages
        self.folder_names = self._extract_folders()
    
    def _extract_folders(self) -> List[str]:
        """Extract top-level folders from file tree"""
        folders = set()
        for item in self.file_tree:
            path = item.get("path", "").split("/")
            if len(path) > 1:
                folders.add(path[0])
        return list(folders)
    
    # SIGNAL 1: Semantic Folder Structure (0-20)
    def signal_structure(self) -> Tuple[int, str]:
        """
        Measure if folders follow domain logic vs cargo-cult patterns.
        
        Good patterns: src/, tests/, docs/, config/, models/, controllers/, services/
        Bad patterns: utils/, helpers/, misc/, constants/, functions/
        """
        semantic_keywords = {
            "good": ["src", "tests", "test", "docs", "config", "models", "controllers", 
                     "services", "api", "database", "auth", "ui", "components", "views"],
            "bad": ["utils", "helpers", "misc", "constants", "functions", "lib", "tools"]
        }
        
        good_count = sum(1 for f in self.folder_names if f.lower() in semantic_keywords["good"])
        bad_count = sum(1 for f in self.folder_names if f.lower() in semantic_keywords["bad"])
        
        total_folders = len(self.folder_names)
        
        if total_folders == 0:
            score = 5  # Flat structure, meh
        elif bad_count > good_count:
            score = 8  # Mostly cargo-cult
        elif good_count >= 3:
            score = 18  # Well-organized
        elif good_count >= 1:
            score = 12  # Some thought
        else:
            score = 5
        
        reason = f"Folders: {', '.join(self.folder_names[:5])}" if self.folder_names else "Flat structure"
        return score, reason
    
    # SIGNAL 2: Documentation Depth (0-20)
    def signal_documentation(self) -> Tuple[int, str]:
        """
        Rate README for depth of thinking, not just length.
        
        Good: Has sections like Overview, Setup, Usage, Architecture, Contributing
        Better: Includes examples, diagrams, troubleshooting
        """
        if not self.readme:
            return 0, "No README found"
        
        readme_lower = self.readme.lower()
        
        # Check for key sections (signs of mature documentation)
        sections = {
            "overview": ["overview", "about", "description", "what is"],
            "setup": ["setup", "installation", "install", "getting started"],
            "usage": ["usage", "how to use", "tutorial", "examples"],
            "architecture": ["architecture", "design", "structure"],
            "contributing": ["contributing", "contribution", "contribute"],
        }
        
        found_sections = sum(1 for section, keywords in sections.items() 
                            if any(kw in readme_lower for kw in keywords))
        
        # Bonus for examples, images, badges
        has_examples = "```"
        has_structure = len(self.readme) > 500  # Substantive content
        
        score = min(20, (found_sections * 3) + (3 if has_examples else 0) + (2 if has_structure else 0))
        reason = f"Found {found_sections}/5 key sections, {'has examples' if has_examples else 'no examples'}"
        
        return score, reason
    
    # SIGNAL 3: Test Strategy (0-20)
    def signal_tests(self) -> Tuple[int, str]:
        """
        Detect test presence and sophistication.
        
        Looks for: unit tests, integration tests, E2E tests, test coverage config
        """
        test_files = [item.get("path", "") for item in self.file_tree 
                     if "test" in item.get("path", "").lower()]
        
        test_indicators = {
            "unit": sum(1 for f in test_files if "unit" in f.lower() or "_test" in f),
            "integration": sum(1 for f in test_files if "integration" in f.lower() or "e2e" in f.lower()),
            "coverage": any("coverage" in f.lower() or ".coveragerc" in f for f in [item.get("path", "") for item in self.file_tree]),
            "config": any("pytest.ini" in f or "jest.config" in f or "vitest" in f for f in [item.get("path", "") for item in self.file_tree]),
        }
        
        test_count = len(test_files)
        
        if test_count == 0:
            score = 0
            reason = "No tests found"
        elif test_indicators["coverage"] or test_indicators["config"]:
            score = 18
            reason = f"{test_count} test files with coverage config"
        elif test_indicators["unit"] > 0 and test_indicators["integration"] > 0:
            score = 15
            reason = f"Unit + Integration tests ({test_count} files)"
        elif test_count > 5:
            score = 12
            reason = f"{test_count} test files"
        else:
            score = 6
            reason = f"Basic tests ({test_count} files)"
        
        return score, reason
    
    # SIGNAL 4: Commit Narrative Quality (0-20)
    def signal_commits(self) -> Tuple[int, str]:
        """
        Analyze commit message quality and consistency.
        
        Good: Descriptive, conventional commits (feat:, fix:, docs:), regular cadence
        Bad: "fix bug", "update", sporadic commits
        """
        if not self.commits:
            return 0, "No commits"
        
        # Analyze messages
        conventional_count = 0
        descriptive_count = 0
        quality_keywords = ["add", "fix", "refactor", "improve", "update", "implement", "feature"]
        
        for commit in self.commits[:50]:  # Check last 50
            msg = commit.get("message", "").lower()
            if any(msg.startswith(c) for c in ["feat:", "fix:", "docs:", "style:", "test:", "refactor:", "chore:"]):
                conventional_count += 1
            if len(msg.split()) > 3 and any(kw in msg for kw in quality_keywords):
                descriptive_count += 1
        
        quality_ratio = (conventional_count + descriptive_count) / max(len(self.commits), 1)
        
        score = min(20, int(quality_ratio * 20))
        reason = f"Conventional: {conventional_count}, Descriptive: {descriptive_count}/{len(self.commits[:50])}"
        
        return score, reason
    
    # SIGNAL 5: Dependency Health (0-20)
    def signal_dependencies(self) -> Tuple[int, str]:
        """
        Check for dependency management best practices.
        
        Good: requirements.txt, package.json with pinned versions, lock files
        Bad: No dependency files, all wildcard versions
        """
        dep_files = [item.get("path", "") for item in self.file_tree 
                    if any(df in item.get("path", "") for df in 
                           ["requirements.txt", "package.json", "Gemfile", "pom.xml", "go.mod"])]
        
        lock_files = [item.get("path", "") for item in self.file_tree 
                     if any(lf in item.get("path", "") for lf in 
                            ["package-lock.json", "yarn.lock", "Pipfile.lock", "poetry.lock"])]
        
        if not dep_files:
            score = 0
            reason = "No dependency files"
        elif lock_files and len(lock_files) > 0:
            score = 18
            reason = f"Dependency files + lock files present"
        elif len(dep_files) > 1:
            score = 14
            reason = f"{len(dep_files)} dependency files"
        else:
            score = 10
            reason = "Basic dependency management"
        
        return score, reason
    
    def get_all_signals(self) -> Dict[str, Tuple[int, str]]:
        """Return all 5 signals"""
        return {
            "structure": self.signal_structure(),
            "documentation": self.signal_documentation(),
            "tests": self.signal_tests(),
            "commits": self.signal_commits(),
            "dependencies": self.signal_dependencies(),
        }
