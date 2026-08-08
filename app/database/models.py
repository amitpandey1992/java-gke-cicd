"""SQL table definitions."""

CREATE_FAILURES_TABLE = """
CREATE TABLE IF NOT EXISTS failures (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(64) UNIQUE NOT NULL,
    provider VARCHAR(20) NOT NULL,
    job_name VARCHAR(255),
    build_url TEXT,
    failure_category VARCHAR(50),
    summary TEXT,
    root_cause TEXT,
    suggested_fix TEXT,
    actual_fix TEXT,
    confidence FLOAT DEFAULT 0.0,
    from_memory BOOLEAN DEFAULT FALSE,
    feedback_helpful BOOLEAN,
    resolution_time_seconds INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);
"""

CREATE_FEEDBACK_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS feedback_log (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(64) REFERENCES failures(analysis_id),
    helpful BOOLEAN NOT NULL,
    actual_fix TEXT,
    engineer_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
"""
