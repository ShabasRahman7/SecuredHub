"""
Prompt templates for AI Agent.

Contains system prompts and templates for compliance analysis.
"""

SYSTEM_PROMPT = """You are an expert compliance analyst for SecurED-Hub, a DevSecOps governance platform.

Your role is to:
1. Analyze compliance evaluation results
2. Prioritize fixes by business impact and dependencies
3. Map failures to compliance frameworks (SOC2, ISO-27001)
4. Provide actionable remediation steps
5. Predict score improvements

Guidelines:
- Be specific and actionable
- Consider dependencies between rules
- Focus on business impact, not just technical fixes
- Provide step-by-step remediation guidance
- Be honest about score projections

You must respond with structured JSON matching the expected schema."""


def build_analysis_prompt(
    repository_name: str,
    standard_name: str,
    current_score: float,
    grade: str,
    total_rules: int,
    passed_rules: int,
    failed_rules: int,
    failures: list[dict],
    max_recommendations: int = 5,
    include_remediation: bool = True,
    include_framework_mapping: bool = True,
) -> str:
    """Build the analysis prompt with evaluation context."""
    
    # Format failures for the prompt
    failures_text = ""
    for i, f in enumerate(failures, 1):
        failures_text += f"""
{i}. {f['rule_name']} (ID: {f['rule_id']})
   Type: {f['rule_type']}
   Severity: {f['severity']}
   Weight: {f['weight']}/10
   Message: {f['message']}
   Description: {f.get('description', 'N/A')}
"""
    
    prompt = f"""Analyze the following compliance evaluation and provide prioritized recommendations.

## Repository
- Name: {repository_name}
- Standard: {standard_name}

## Current Status
- Score: {current_score:.1f}%
- Grade: {grade}
- Rules: {passed_rules}/{total_rules} passed ({failed_rules} failed)

## Failed Rules
{failures_text}

## Your Task

Provide exactly {max_recommendations} prioritized recommendations. For each:

1. **Priority**: Rank from 1 (fix first) to {max_recommendations}
2. **Reason**: Why this should be fixed in this order
3. **Business Impact**: What happens if not fixed
4. **Score Impact**: How much fixing this improves the score
5. **Estimated Score After Fix**: Predicted score after this fix
"""

    if include_remediation:
        prompt += """6. **Remediation Steps**: Exact steps to fix (2-4 steps)
"""
    
    if include_framework_mapping:
        prompt += """7. **Framework Mappings**: Related SOC2/ISO-27001 controls
"""

    prompt += """
Also provide:
- **Summary**: One paragraph executive summary
- **Overall Assessment**: Brief assessment of compliance posture
- **Score Projection**: Current score, projected score if all fixed, quick wins score (top 3)
- **Confidence Score**: Your confidence in these recommendations (0-1)

Focus on actionable, specific guidance that developers can immediately use."""

    return prompt
