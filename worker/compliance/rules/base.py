"""
Base classes for the compliance rule engine.

This module provides:
- RuleResult: Data class for rule evaluation results
- BaseRule: Abstract base class for all compliance rules
- RuleRegistry: Registry to look up rules by type
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class RuleResult:
    """
    Result of evaluating a single compliance rule.
    
    Attributes:
        passed: Whether the rule check passed
        message: Human-readable explanation of the result
        evidence: Evidence captured during the check (JSON-serializable)
    """
    passed: bool
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'passed': self.passed,
            'message': self.message,
            'evidence': self.evidence,
        }


@dataclass
class RepositorySnapshot:
    """
    Snapshot of a repository's structure for compliance evaluation.
    
    Contains information about files, folders, and metadata
    captured at a point in time.
    """
    # List of all file paths in the repository
    files: List[str] = field(default_factory=list)
    
    # List of all folder paths in the repository
    folders: List[str] = field(default_factory=list)
    
    # File contents (only for small files we need to inspect)
    file_contents: Dict[str, str] = field(default_factory=dict)
    
    # Repository metadata from GitHub API
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Commit information
    commit_hash: Optional[str] = None
    branch: str = 'main'
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in the snapshot."""
        # Normalize path (remove leading ./)
        normalized = path.lstrip('./')
        return normalized in self.files or path in self.files
    
    def folder_exists(self, path: str) -> bool:
        """Check if a folder exists in the snapshot."""
        # Remove trailing slash and leading './' prefix (but not just '.')
        normalized = path.rstrip('/')
        if normalized.startswith('./'):
            normalized = normalized[2:]
        
        return any(
            f == normalized or f.startswith(normalized + '/')
            for f in self.folders
        )
    
    def get_file_content(self, path: str) -> Optional[str]:
        """Get content of a file if available."""
        return self.file_contents.get(path) or self.file_contents.get(path.lstrip('./'))
    
    def has_any_file_matching(self, patterns: List[str]) -> List[str]:
        """
        Find files matching any of the given glob-like patterns.
        Returns list of matching file paths.
        """
        import fnmatch
        matches = []
        for pattern in patterns:
            for file_path in self.files:
                if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(file_path.split('/')[-1], pattern):
                    matches.append(file_path)
        return matches


class BaseRule(ABC):
    """
    Abstract base class for all compliance rules.
    
    Subclasses must implement the check() method.
    """
    
    # Rule type identifier (should match rule_type in database)
    rule_type: str = None
    
    def __init__(self, name: str, config: Dict[str, Any], weight: int = 5):
        """
        Initialize the rule.
        
        Args:
            name: Human-readable name of the rule
            config: Configuration from the rule's check_config field
            weight: Weight of this rule in score calculation
        """
        self.name = name
        self.config = config
        self.weight = weight
    
    @abstractmethod
    def check(self, snapshot: RepositorySnapshot) -> RuleResult:
        """
        Execute the rule check against the repository snapshot.
        
        Args:
            snapshot: Repository snapshot to check
            
        Returns:
            RuleResult indicating pass/fail with evidence
        """
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r})"


class RuleRegistry:
    """
    Registry for looking up rule implementations by type.
    """
    
    _rules: Dict[str, type] = {}
    
    @classmethod
    def register(cls, rule_type: str):
        """
        Decorator to register a rule implementation.
        
        Usage:
            @RuleRegistry.register('file_exists')
            class FileExistsRule(BaseRule):
                ...
        """
        def decorator(rule_class):
            cls._rules[rule_type] = rule_class
            return rule_class
        return decorator
    
    @classmethod
    def get_rule_class(cls, rule_type: str) -> Optional[type]:
        """Get the rule class for a given rule type."""
        return cls._rules.get(rule_type)
    
    @classmethod
    def create_rule(cls, rule_type: str, name: str, config: Dict[str, Any], weight: int = 5) -> Optional[BaseRule]:
        """
        Create a rule instance from its type.
        
        Args:
            rule_type: Type of rule (e.g., 'file_exists')
            name: Name of the rule
            config: Configuration for the rule
            weight: Weight of the rule
            
        Returns:
            Rule instance or None if type not found
        """
        rule_class = cls.get_rule_class(rule_type)
        if rule_class:
            return rule_class(name=name, config=config, weight=weight)
        return None
    
    @classmethod
    def available_types(cls) -> List[str]:
        """List all registered rule types."""
        return list(cls._rules.keys())
