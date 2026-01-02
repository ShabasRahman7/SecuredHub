"""Workspace management for scan isolation"""
import os
import shutil
import tempfile
from pathlib import Path

class WorkspaceManager:
    
    def __init__(self, base_path: str = '/tmp/scanner_workspace'):
        # initializing workspace manager
        self.base_path = base_path
        Path(base_path).mkdir(parents=True, exist_ok=True)
    
    def create_workspace(self, repo_id: int) -> str:
        # creating a temporary workspace for a repository scan
        workspace_path = os.path.join(
            self.base_path, 
            f"repo_{repo_id}_{os.getpid()}"
        )
        
        # cleaning up if exists (from previous failed run)
        if os.path.exists(workspace_path):
            shutil.rmtree(workspace_path)
        
        os.makedirs(workspace_path, exist_ok=True)
        print(f"Created workspace: {workspace_path}")
        
        return workspace_path
    
    def cleanup_workspace(self, workspace_path: str) -> None:
        # removing workspace after scan completion
        try:
            if os.path.exists(workspace_path):
                shutil.rmtree(workspace_path)
                print(f"Cleaned up workspace: {workspace_path}")
        except Exception as e:
            print(f"Failed to cleanup workspace {workspace_path}: {e}")
    
    def get_workspace_size(self, workspace_path: str) -> int:
        # calculating workspace size in bytes
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(workspace_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass
        return total_size
