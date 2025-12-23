"""
GitHub repository collector.

Collects repository structure and metadata from GitHub API
to create a RepositorySnapshot for compliance evaluation.
"""
import logging
import requests
from typing import Optional, Dict, Any, List
from compliance.rules.base import RepositorySnapshot

logger = logging.getLogger(__name__)


class GitHubCollector:
    """
    Collects repository information from GitHub API.
    
    Uses the GitHub API to fetch:
    - Repository file tree (all files and folders)
    - Repository metadata
    - Current commit information
    """
    
    API_BASE = "https://api.github.com"
    
    def __init__(self, owner: str, repo: str, access_token: str, branch: str = 'main'):
        """
        Initialize the collector.
        
        Args:
            owner: GitHub username or org
            repo: Repository name
            access_token: GitHub access token
            branch: Branch to collect from (default: main)
        """
        self.owner = owner
        self.repo = repo
        self.access_token = access_token
        self.branch = branch
        
        self.headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json',
        }
    
    def collect(self) -> RepositorySnapshot:
        """
        Collect repository snapshot from GitHub.
        
        Returns:
            RepositorySnapshot with files, folders, and metadata
        """
        snapshot = RepositorySnapshot(branch=self.branch)
        
        try:
            # Get repository tree
            tree = self._get_repository_tree()
            if tree:
                for item in tree.get('tree', []):
                    path = item.get('path', '')
                    item_type = item.get('type', '')
                    
                    if item_type == 'blob':  # file
                        snapshot.files.append(path)
                    elif item_type == 'tree':  # folder
                        snapshot.folders.append(path)
                
                # Get the commit hash from the tree
                snapshot.commit_hash = tree.get('sha')
            
            # Get repository metadata
            metadata = self._get_repository_metadata()
            if metadata:
                snapshot.metadata = {
                    'default_branch': metadata.get('default_branch'),
                    'description': metadata.get('description'),
                    'stars': metadata.get('stargazers_count'),
                    'forks': metadata.get('forks_count'),
                    'open_issues': metadata.get('open_issues_count'),
                    'language': metadata.get('language'),
                    'private': metadata.get('private'),
                    'archived': metadata.get('archived'),
                    'created_at': metadata.get('created_at'),
                    'updated_at': metadata.get('updated_at'),
                    'pushed_at': metadata.get('pushed_at'),
                }
            
            logger.info(
                f"Collected snapshot for {self.owner}/{self.repo}: "
                f"{len(snapshot.files)} files, {len(snapshot.folders)} folders"
            )
            
        except Exception as e:
            logger.error(f"Error collecting repository {self.owner}/{self.repo}: {e}")
            raise
        
        return snapshot
    
    def _get_repository_tree(self) -> Optional[Dict[str, Any]]:
        """Get the complete repository tree from GitHub API."""
        # First get the branch reference to find the tree SHA
        ref_url = f"{self.API_BASE}/repos/{self.owner}/{self.repo}/git/refs/heads/{self.branch}"
        
        try:
            ref_response = requests.get(ref_url, headers=self.headers, timeout=30)
            ref_response.raise_for_status()
            ref_data = ref_response.json()
            commit_sha = ref_data.get('object', {}).get('sha')
            
            if not commit_sha:
                logger.error(f"Could not find commit SHA for branch {self.branch}")
                return None
            
            # Get the tree with recursive flag to get all files
            tree_url = f"{self.API_BASE}/repos/{self.owner}/{self.repo}/git/trees/{commit_sha}?recursive=1"
            tree_response = requests.get(tree_url, headers=self.headers, timeout=60)
            tree_response.raise_for_status()
            
            return tree_response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Repository {self.owner}/{self.repo} or branch {self.branch} not found")
            else:
                logger.error(f"HTTP error fetching tree: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching tree: {e}")
            raise
    
    def _get_repository_metadata(self) -> Optional[Dict[str, Any]]:
        """Get repository metadata from GitHub API."""
        repo_url = f"{self.API_BASE}/repos/{self.owner}/{self.repo}"
        
        try:
            response = requests.get(repo_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not fetch repository metadata: {e}")
            return None
    
    @classmethod
    def from_repository_url(cls, url: str, access_token: str, branch: str = 'main') -> 'GitHubCollector':
        """
        Create a collector from a repository URL.
        
        Args:
            url: GitHub repository URL (e.g., https://github.com/owner/repo)
            access_token: GitHub access token
            branch: Branch to collect from
            
        Returns:
            GitHubCollector instance
        """
        # Parse owner and repo from URL
        # Handle both https://github.com/owner/repo and github.com/owner/repo
        url = url.rstrip('/')
        if '.git' in url:
            url = url.replace('.git', '')
        
        parts = url.split('/')
        
        # Find github.com position
        try:
            github_idx = next(i for i, p in enumerate(parts) if 'github.com' in p)
            owner = parts[github_idx + 1]
            repo = parts[github_idx + 2]
        except (StopIteration, IndexError):
            raise ValueError(f"Could not parse owner/repo from URL: {url}")
        
        return cls(owner=owner, repo=repo, access_token=access_token, branch=branch)
