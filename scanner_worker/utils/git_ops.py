"""Git operations for repository cloning"""
import os
import git
from typing import Optional, Dict

def clone_repository(repo_url: str, workspace_path: str, token: Optional[str] = None) -> str:
    # clone a repository to the workspace
    # inject token into URL if provided
    if token and 'github.com' in repo_url:
        repo_url = repo_url.replace('https://', f'https://{token}@')
    
    print(f"Cloning repository: {repo_url} to {workspace_path}")
    
    try:
        repo = git.Repo.clone_from(repo_url, workspace_path, depth=1)
        return workspace_path
    except git.GitCommandError as e:
        raise Exception(f"Failed to clone repository: {e}")

def get_latest_commit_hash(workspace_path: str) -> str:
    # getting the latest commit hash from the repository
    try:
        repo = git.Repo(workspace_path)
        commit_hash = repo.head.commit.hexsha
        print(f"Latest commit: {commit_hash}")
        return commit_hash
    except Exception as e:
        raise Exception(f"Failed to get commit hash: {e}")

def get_commit_info(workspace_path: str) -> Dict[str, str]:
    # getting detailed commit information
    try:
        repo = git.Repo(workspace_path)
        commit = repo.head.commit
        
        return {
            'hash': commit.hexsha,
            'short_hash': commit.hexsha[:7],
            'author': str(commit.author),
            'message': commit.message.strip(),
            'date': commit.committed_datetime.isoformat()
        }
    except Exception as e:
        raise Exception(f"Failed to get commit info: {e}")
