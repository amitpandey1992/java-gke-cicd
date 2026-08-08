def truncate_log(sanitized_log: str, max_chars: int = 15000) -> str:
    """Truncate log to fit within character limits, prioritizing error sections."""
    if len(sanitized_log) <= max_chars:
        return sanitized_log

    lines = sanitized_log.split('\n')
    original_lines = len(lines)
    
    error_keywords = ['ERROR', 'FATAL', 'Exception', 'Traceback', 'FAILED']
    error_indices = []

    for i, line in enumerate(lines):
        if any(keyword in line for keyword in error_keywords):
            error_indices.append(i)

    included_indices = set()
    
    # Always include first 20 lines (build config info)
    for i in range(min(20, original_lines)):
        included_indices.add(i)

    if error_indices:
        first_error = error_indices[0]
        last_error = error_indices[-1]
        
        # Include 50 lines before first error and 50 lines after last error
        start_idx = max(0, first_error - 50)
        end_idx = min(original_lines, last_error + 51)
        
        for i in range(start_idx, end_idx):
            included_indices.add(i)
    else:
        # If no error keywords found, take last 200 lines
        start_idx = max(0, original_lines - 200)
        for i in range(start_idx, original_lines):
            included_indices.add(i)

    sorted_indices = sorted(list(included_indices))
    
    truncated_lines = []
    prev_idx = -1
    
    for idx in sorted_indices:
        if prev_idx != -1 and idx > prev_idx + 1:
            truncated_lines.append('[... truncated ...]')
        truncated_lines.append(lines[idx])
        prev_idx = idx

    result = '\n'.join(truncated_lines)
    
    # If still over max_chars, truncate from middle
    if len(result) > max_chars:
        half_limit = (max_chars - 50) // 2
        result = result[:half_limit] + '\n\n[... truncated ...]\n\n' + result[-half_limit:]

    header = f'=== LOG TRUNCATED FROM {original_lines} TO {len(result.splitlines())} LINES ===\n'
    return header + result
