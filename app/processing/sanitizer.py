import re
import logging

logger = logging.getLogger(__name__)

def sanitize_log(raw_log: str) -> str:
    """Sanitize build log by removing sensitive information and formatting."""
    redactions = 0
    sanitized = raw_log

    # Define regex patterns for sensitive information
    patterns = {
        'AWS_ACCESS_KEY': r'AKIA[0-9A-Z]{16}',
        'AWS_SECRET_KEY': r'[A-Za-z0-9/+=]{40}',
        'API_KEY': r'(?i)(api[_-]?key|token|secret|password|passwd|pwd)\s*[:=]\s*[\'"]?[A-Za-z0-9_\-\.]{8,}[\'"]?',
        'BEARER_TOKEN': r'Bearer [A-Za-z0-9\-\._~\+/]+=*',
        'PRIVATE_KEY': r'-----BEGIN [A-Z ]+ PRIVATE KEY-----.*?-----END [A-Z ]+ PRIVATE KEY-----',
        'GITHUB_TOKEN': r'ghp_[A-Za-z0-9]{36}',
        'NPM_TOKEN': r'//registry\.npmjs\.org/:_authToken=[\w-]+'
    }

    # Apply redactions
    for key, pattern in patterns.items():
        # Using DOTALL for multi-line private keys
        flags = re.DOTALL if key == 'PRIVATE_KEY' else 0
        matches = len(re.findall(pattern, sanitized, flags))
        if matches > 0:
            sanitized = re.sub(pattern, f'[REDACTED_{key}]', sanitized, flags=flags)
            redactions += matches

    # Remove ANSI escape codes
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    sanitized = ansi_escape.sub('', sanitized)

    # Remove progress bars (lines with %, ████, etc.)
    progress_bar = re.compile(r'.*(%|████|====|----).*')
    filtered_lines = []
    for line in sanitized.split('\n'):
        if not progress_bar.match(line):
            filtered_lines.append(line)
            
    sanitized = '\n'.join(filtered_lines)

    if redactions > 0:
        logger.info(f"Sanitized {redactions} sensitive items from log")

    return sanitized
