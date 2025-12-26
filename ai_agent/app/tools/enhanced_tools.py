"""
Enhanced AI Tools for compliance analysis.

These tools provide:
- Knowledge search (RAG without vector DB)
- Score impact calculation
- Fix file generation
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from app.tools.base import tool

logger = logging.getLogger(__name__)

# Load knowledge base once at module level
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


def _load_json(filename: str) -> dict:
    """Load a JSON knowledge file."""
    filepath = KNOWLEDGE_DIR / filename
    try:
        with open(filepath) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {filename}: {e}")
        return {}


def _load_template(template_name: str) -> str:
    """Load a fix template file."""
    filepath = KNOWLEDGE_DIR / "templates" / f"{template_name}.template"
    try:
        with open(filepath) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load template {template_name}: {e}")
        return ""


# Pre-load knowledge bases
SOC2_CONTROLS = _load_json("soc2_controls.json")
ISO27001_CONTROLS = _load_json("iso27001_controls.json")
RULE_MAPPINGS = _load_json("rule_mappings.json")


@tool(
    name="search_knowledge",
    description="Search the compliance knowledge base for SOC2 or ISO-27001 control details, remediation guidance, and best practices",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (e.g., 'branch protection', 'CC6.1', 'access control')",
            },
            "framework": {
                "type": "string",
                "description": "Filter by framework: 'soc2', 'iso27001', or 'all'",
                "enum": ["soc2", "iso27001", "all"],
            },
        },
        "required": ["query"],
    },
)
async def search_knowledge(query: str, framework: str = "all") -> dict:
    """
    Search the knowledge base for compliance information.
    
    Uses keyword matching against control names, descriptions, and related rules.
    Returns matching controls with full remediation guidance.
    """
    query_lower = query.lower()
    results = []
    
    # Search SOC2 controls
    if framework in ["soc2", "all"]:
        for control_id, control in SOC2_CONTROLS.items():
            score = 0
            searchable = f"{control_id} {control.get('name', '')} {control.get('description', '')} {' '.join(control.get('common_failures', []))}".lower()
            
            # Score based on match quality
            if control_id.lower() in query_lower:
                score += 10
            if query_lower in searchable:
                score += 5
            for word in query_lower.split():
                if word in searchable:
                    score += 1
            
            if score > 0:
                results.append({
                    "framework": "SOC2",
                    "control_id": control_id,
                    "name": control.get("name"),
                    "description": control.get("description"),
                    "common_failures": control.get("common_failures", []),
                    "remediation": control.get("remediation"),
                    "business_impact": control.get("business_impact"),
                    "score": score,
                })
    
    # Search ISO-27001 controls
    if framework in ["iso27001", "all"]:
        for control_id, control in ISO27001_CONTROLS.items():
            score = 0
            searchable = f"{control_id} {control.get('name', '')} {control.get('description', '')} {' '.join(control.get('common_failures', []))}".lower()
            
            if control_id.lower() in query_lower:
                score += 10
            if query_lower in searchable:
                score += 5
            for word in query_lower.split():
                if word in searchable:
                    score += 1
            
            if score > 0:
                results.append({
                    "framework": "ISO-27001",
                    "control_id": control_id,
                    "name": control.get("name"),
                    "description": control.get("description"),
                    "common_failures": control.get("common_failures", []),
                    "remediation": control.get("remediation"),
                    "score": score,
                })
    
    # Sort by relevance score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "success": True,
        "query": query,
        "framework": framework,
        "total_results": len(results),
        "results": results[:5],  # Top 5 results
    }


@tool(
    name="calculate_impact",
    description="Calculate the exact score improvement if specific rules are fixed. Shows current score, projected score, and percentage impact for each fix.",
    parameters={
        "type": "object",
        "properties": {
            "evaluation_id": {
                "type": "integer",
                "description": "The evaluation ID to calculate impact for",
            },
            "current_score": {
                "type": "number",
                "description": "Current evaluation score (0-100)",
            },
            "passed_count": {
                "type": "integer",
                "description": "Number of currently passed rules",
            },
            "failed_count": {
                "type": "integer",
                "description": "Number of currently failed rules",
            },
            "failed_rules": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "rule_name": {"type": "string"},
                        "weight": {"type": "number"},
                    },
                },
                "description": "List of failed rules with their weights",
            },
        },
        "required": ["evaluation_id", "current_score", "passed_count", "failed_count", "failed_rules"],
    },
)
async def calculate_impact(
    evaluation_id: int,
    current_score: float,
    passed_count: int,
    failed_count: int,
    failed_rules: list[dict],
) -> dict:
    """
    Calculate exact score impact for fixing each failed rule.
    
    Uses the formula: score = (sum of passed weights / total weights) * 100
    """
    # Calculate total weight
    total_rules = passed_count + failed_count
    if total_rules == 0:
        return {"success": False, "error": "No rules in evaluation"}
    
    # Calculate current passed weight based on current score
    # current_score = (passed_weight / total_weight) * 100
    # So: passed_weight = (current_score / 100) * total_weight
    
    # Estimate weights from failed rules
    total_failed_weight = sum(r.get("weight", 1.0) for r in failed_rules)
    
    # If current_score is 0, all weight is in failed rules
    if current_score <= 0:
        total_weight = total_failed_weight
        passed_weight = 0
    else:
        # Estimate total weight: passed_weight + failed_weight = total
        # current_score = passed_weight / total_weight * 100
        # So: passed_weight = current_score * total_weight / 100
        # And: total_weight = passed_weight + failed_weight
        # Therefore: passed_weight = current_score * (passed_weight + failed_weight) / 100
        # Solving: passed_weight * 100 = current_score * passed_weight + current_score * failed_weight
        # passed_weight * (100 - current_score) = current_score * failed_weight
        # passed_weight = (current_score * failed_weight) / (100 - current_score)
        if current_score >= 100:
            passed_weight = total_failed_weight * 99  # Edge case
        else:
            passed_weight = (current_score * total_failed_weight) / (100 - current_score)
        total_weight = passed_weight + total_failed_weight
    
    # Calculate projected scores for each fix
    fixes = []
    cumulative_passed_weight = passed_weight
    cumulative_score = current_score
    
    # Sort by weight (highest impact first)
    sorted_rules = sorted(failed_rules, key=lambda x: x.get("weight", 1.0), reverse=True)
    
    for i, rule in enumerate(sorted_rules):
        rule_weight = rule.get("weight", 1.0)
        rule_name = rule.get("rule_name", f"Rule {i+1}")
        
        # Calculate new score if this rule is fixed
        cumulative_passed_weight += rule_weight
        new_score = (cumulative_passed_weight / total_weight) * 100 if total_weight > 0 else 100
        
        impact = new_score - cumulative_score
        
        # Get framework mapping
        mapping = RULE_MAPPINGS.get(rule_name, {})
        
        fixes.append({
            "rank": i + 1,
            "rule_name": rule_name,
            "weight": rule_weight,
            "score_before": round(cumulative_score, 2),
            "score_after": round(new_score, 2),
            "impact_percent": round(impact, 2),
            "soc2": mapping.get("soc2", []),
            "iso27001": mapping.get("iso27001", []),
            "severity": mapping.get("severity", "medium"),
            "can_generate_fix": mapping.get("can_generate_fix", False),
        })
        
        cumulative_score = new_score
    
    return {
        "success": True,
        "evaluation_id": evaluation_id,
        "current_score": round(current_score, 2),
        "current_grade": _score_to_grade(current_score),
        "total_if_all_fixed": 100.0,
        "projected_grade": "A",
        "fixes": fixes,
    }


def _score_to_grade(score: float) -> str:
    """Convert score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


@tool(
    name="generate_fix",
    description="Generate an actual fix file (CODEOWNERS, dependabot.yml, SECURITY.md, etc.) that the user can commit to their repository",
    parameters={
        "type": "object",
        "properties": {
            "rule_name": {
                "type": "string",
                "description": "The name of the failed rule to generate a fix for",
            },
            "repo_name": {
                "type": "string",
                "description": "Repository name for customization",
            },
            "repo_owner": {
                "type": "string",
                "description": "Repository owner/organization name",
            },
            "detected_languages": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Detected programming languages (python, javascript, etc.)",
            },
        },
        "required": ["rule_name"],
    },
)
async def generate_fix(
    rule_name: str,
    repo_name: str = "my-repository",
    repo_owner: str = "team-lead",
    detected_languages: Optional[list[str]] = None,
) -> dict:
    """
    Generate actual fix file content based on rule and repository context.
    
    Returns ready-to-commit file content with instructions.
    """
    mapping = RULE_MAPPINGS.get(rule_name, {})
    
    if not mapping.get("can_generate_fix"):
        return {
            "success": False,
            "error": f"Cannot auto-generate fix for '{rule_name}'. This requires manual configuration.",
            "manual_steps": mapping.get("remediation_summary", "See compliance documentation"),
        }
    
    template_name = mapping.get("template_name")
    if not template_name:
        return {"success": False, "error": "No template available"}
    
    template = _load_template(template_name)
    if not template:
        return {"success": False, "error": f"Template {template_name} not found"}
    
    # Detect file characteristics
    languages = detected_languages or []
    has_npm = any(lang in ["javascript", "typescript", "nodejs"] for lang in languages)
    has_pip = any(lang in ["python"] for lang in languages)
    has_docker = any(lang in ["docker", "dockerfile"] for lang in languages)
    
    # Apply template substitutions
    content = template
    content = content.replace("{{repo_name}}", repo_name)
    content = content.replace("{{default_owner}}", repo_owner)
    content = content.replace("{{organization}}", repo_owner.split("/")[0] if "/" in repo_owner else repo_owner)
    content = content.replace("{{github_url}}", f"https://github.com/{repo_owner}/{repo_name}")
    content = content.replace("{{description}}", f"A repository managed by {repo_owner}")
    
    # Handle conditional blocks
    content = _process_conditionals(content, {
        "has_npm": has_npm or not languages,  # Default to including if no languages detected
        "has_pip": has_pip or not languages,
        "has_docker": has_docker,
        "has_backend": True,
        "has_frontend": True,
        "has_infra": True,
    })
    
    # Determine filename
    filename_map = {
        "codeowners": ".github/CODEOWNERS",
        "dependabot": ".github/dependabot.yml",
        "security": "SECURITY.md",
        "readme": "README.md",
        "gitignore": ".gitignore",
        "license": "LICENSE",
    }
    filename = filename_map.get(template_name, f"{template_name}.txt")
    
    # Determine language for syntax highlighting
    lang_map = {
        "codeowners": "text",
        "dependabot": "yaml",
        "security": "markdown",
        "readme": "markdown",
        "gitignore": "text",
    }
    language = lang_map.get(template_name, "text")
    
    return {
        "success": True,
        "filename": filename,
        "content": content,
        "language": language,
        "instructions": f"Create this file at `{filename}` in your repository root and commit it.",
        "framework_mapping": {
            "soc2": mapping.get("soc2", []),
            "iso27001": mapping.get("iso27001", []),
        },
    }


def _process_conditionals(content: str, context: dict) -> str:
    """Process simple conditional blocks in templates."""
    # Pattern: {{#if condition}}...{{/if}}
    pattern = r"\{\{#if (\w+)\}\}(.*?)\{\{/if\}\}"
    
    def replace_conditional(match):
        condition = match.group(1)
        block = match.group(2)
        if context.get(condition):
            return block
        return ""
    
    result = re.sub(pattern, replace_conditional, content, flags=re.DOTALL)
    return result.strip()


@tool(
    name="get_framework_mapping",
    description="Get the SOC2 and ISO-27001 framework mapping for a specific rule",
    parameters={
        "type": "object",
        "properties": {
            "rule_name": {
                "type": "string",
                "description": "The name of the rule to get mapping for",
            },
        },
        "required": ["rule_name"],
    },
)
async def get_framework_mapping(rule_name: str) -> dict:
    """Get framework mapping for a rule."""
    mapping = RULE_MAPPINGS.get(rule_name, {})
    
    if not mapping:
        return {
            "success": False,
            "error": f"No mapping found for rule '{rule_name}'",
        }
    
    soc2_details = []
    for control_id in mapping.get("soc2", []):
        control = SOC2_CONTROLS.get(control_id, {})
        soc2_details.append({
            "control_id": control_id,
            "name": control.get("name"),
            "category": control.get("category"),
        })
    
    iso_details = []
    for control_id in mapping.get("iso27001", []):
        control = ISO27001_CONTROLS.get(control_id, {})
        iso_details.append({
            "control_id": control_id,
            "name": control.get("name"),
            "category": control.get("category"),
        })
    
    return {
        "success": True,
        "rule_name": rule_name,
        "severity": mapping.get("severity"),
        "business_impact": mapping.get("business_impact"),
        "soc2": soc2_details,
        "iso27001": iso_details,
        "can_generate_fix": mapping.get("can_generate_fix", False),
    }
