"""
Minimal False Positive Filter - Tenant-wide ignore list

This is a lightweight FP filtering system that demonstrates the concept
without requiring a full database model and UI.

Future: Can be replaced with DB-backed FalsePositiveReport system.
"""
import fnmatch
from typing import List, Dict

# in-memory false positive fingerprints
# format: (file_path_pattern, rule_id, reason)
FALSE_POSITIVE_PATTERNS = [
    # testing files - already handled by SKIP_DIRS, but adding pattern-based backup
    ("*test*.py", "SECRET_*", "test_code"),
    ("*spec*.js", "SECRET_*", "test_code"),
    
    # database backends - test credentials in DB driver code
    ("*/backends/*/creation.py", "SECRET_PASSWORD_IN_CODE", "db_backend"),
    ("*/backends/oracle/*", "SECRET_*", "db_backend"),
    
    # migration files - often contain example data
    ("*/migrations/*", "SECRET_*", "migration"),
    
    # configuration templates - placeholder secrets
    ("*.example", "SECRET_*", "config_template"),
    (".env.example", "SECRET_*", "config_template"),
    
    # documentation
    ("*/docs/*", "SECRET_*", "documentation"),
    ("*/examples/*", "SECRET_*", "documentation"),
]

def is_false_positive(finding: Dict) -> bool:
    # checking if a finding matches known false positive patterns.
    file_path = finding.get('file_path', '')
    rule_id = finding.get('rule_id', '')
    
    for pattern, rule_pattern, reason in FALSE_POSITIVE_PATTERNS:
        # matching file path pattern
        if fnmatch.fnmatch(file_path, pattern):
            # matching rule ID pattern
            if fnmatch.fnmatch(rule_id, rule_pattern):
                print(f"  → Filtered FP: {file_path} [{rule_id}] (reason: {reason})")
                return True
    
    return False

def filter_false_positives(findings: List[Dict]) -> List[Dict]:
    # filtering out known false positives from findings list.
    original_count = len(findings)
    
    filtered = [f for f in findings if not is_false_positive(f)]
    
    filtered_count = original_count - len(filtered)
    if filtered_count > 0:
        print(f"Filtered out {filtered_count} false positive(s) based on patterns")
    
    return filtered
