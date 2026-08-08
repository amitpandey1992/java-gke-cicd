import json
import re

def build_analysis_prompt(sanitized_log: str, provider: str, job_name: str = None) -> str:
    """Build a structured prompt for AI log analysis."""
    job = job_name or 'Unknown'
    prompt = f"""You are an expert CI/CD failure analyst. Analyze this build failure log and provide a structured diagnosis.

CI Platform: {provider}
Job/Pipeline: {job}

=== BUILD LOG ===
{sanitized_log}
=== END LOG ===

Provide your analysis as a JSON object with these exact fields:
{{
  "failure_category": "one of: DEPENDENCY_CONFLICT, COMPILATION_ERROR, TEST_FAILURE, INFRASTRUCTURE_ERROR, CONFIGURATION_ERROR, NETWORK_ERROR, PERMISSION_ERROR, RESOURCE_EXHAUSTION, TIMEOUT, UNKNOWN",
  "summary": "one-line human-readable summary of the failure",
  "failing_step": "the exact build step or command that failed",
  "root_cause": "detailed explanation of why it failed",
  "suggested_fix": "specific actionable steps to fix the issue"
}}

Respond ONLY with the JSON object, no markdown formatting or explanation."""
    return prompt

def parse_ai_response(response_text: str) -> dict:
    """Parse JSON response from AI."""
    # Strip markdown formatting if present
    text = response_text.strip()
    if text.startswith('```json'):
        text = text[7:]
    elif text.startswith('```'):
        text = text[3:]
    
    if text.endswith('```'):
        text = text[:-3]
        
    text = text.strip()
    
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        # Fallback to regex extraction if JSON is malformed
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                raise ValueError(f"Failed to parse JSON from AI response: {text}") from e
        else:
            raise ValueError(f"Failed to parse JSON from AI response: {text}") from e

    required_fields = ['failure_category', 'summary', 'failing_step', 'root_cause', 'suggested_fix']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field in AI response: {field}")
            
    return data
