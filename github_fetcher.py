import requests
import os
from dotenv import load_dotenv
from typing import Dict, List, Any

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

class GitHubFetcher:
    def __init__(self, repo_url: str):
        """Extract owner and repo from URL like https://github.com/user/repo"""
        parts = repo_url.rstrip('/').split('/')
        self.owner = parts[-2]
        self.repo = parts[-1]
        self.repo_url = repo_url
        
    def get_repo_info(self) -> Dict[str, Any]:
        """Fetch basic repo metadata"""
        url = f"{GITHUB_API_BASE}/repos/{self.owner}/{self.repo}"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "name": data.get("name"),
            "description": data.get("description"),
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "languages": data.get("language"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
        }
    
    def get_languages(self) -> Dict[str, int]:
        """Fetch language distribution"""
        url = f"{GITHUB_API_BASE}/repos/{self.owner}/{self.repo}/languages"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def get_file_tree(self) -> List[Dict[str, str]]:
        """Fetch repo file structure (simplified)"""
        url = f"{GITHUB_API_BASE}/repos/{self.owner}/{self.repo}/git/trees/HEAD?recursive=1"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("tree", [])
    
    def get_readme(self) -> str:
        """Fetch README content"""
        url = f"{GITHUB_API_BASE}/repos/{self.owner}/{self.repo}/readme"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("content", "")
        return ""
    
    def get_commits(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch recent commits"""
        url = f"{GITHUB_API_BASE}/repos/{self.owner}/{self.repo}/commits"
        response = requests.get(url, headers=headers, params={"per_page": per_page}, timeout=10)
        response.raise_for_status()
        commits = response.json()
        return [
            {
                "message": c.get("commit", {}).get("message", ""),
                "author": c.get("commit", {}).get("author", {}).get("name", ""),
                "date": c.get("commit", {}).get("author", {}).get("date", ""),
                "sha": c.get("sha", ""),
            }
            for c in commits
        ]
    
    def get_branches(self) -> List[str]:
        """Fetch list of branches"""
        url = f"{GITHUB_API_BASE}/repos/{self.owner}/{self.repo}/branches"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return [b.get("name") for b in response.json()]

    def get_raw_file_content(self, file_path: str) -> str:
        """Fetch raw content of a specific file"""
        url = f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/HEAD/{file_path}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
        return ""
