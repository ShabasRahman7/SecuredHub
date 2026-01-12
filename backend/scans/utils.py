import subprocess
import re
from typing import Optional


def get_remote_latest_commit(repo_url: str, branch: str = 'HEAD', access_token: Optional[str] = None) -> Optional[str]:
    try:
        url = repo_url
        if access_token:
            # inject token for authentication
            url = re.sub(r'https://', f'https://x-access-token:{access_token}@', repo_url)
        
        result = subprocess.run(
            ['git', 'ls-remote', url, branch],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout.strip():
            # output format: "commit_hash\tref_name"
            return result.stdout.split()[0]
        
        return None
        
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None
