"""Demo AI caller that returns realistic mock analysis results.

Use this when Ollama/Vertex AI is not available (e.g., low-RAM VM).
Set AI_PROVIDER=demo in .env to activate.
"""

import json
import logging
import random
import asyncio

logger = logging.getLogger(__name__)

# Realistic mock analysis templates
DEMO_ANALYSES = [
    {
        "failure_category": "DEPENDENCY_CONFLICT",
        "summary": "npm package version conflict between react 18.2 and react-dom 17.0",
        "failing_step": "npm install @ line 34",
        "root_cause": "react-dom 17.0.2 is incompatible with react 18.2.0. The project upgraded react but not react-dom.",
        "suggested_fix": "Update react-dom to match react version: npm install react-dom@18.2.0"
    },
    {
        "failure_category": "TEST_FAILURE",
        "summary": "Unit test assertion failed in UserService.test_login",
        "failing_step": "pytest tests/test_user_service.py::test_login @ line 87",
        "root_cause": "Expected HTTP 200 but got 401. The test fixture is using expired mock JWT tokens.",
        "suggested_fix": "Regenerate test JWT tokens in conftest.py or mock the token validation layer"
    },
    {
        "failure_category": "COMPILATION_ERROR",
        "summary": "Java compilation failed due to missing import in OrderController.java",
        "failing_step": "mvn compile @ OrderController.java:15",
        "root_cause": "Class 'OrderValidationService' was moved to package 'com.app.services.validation' but the import still references 'com.app.services'.",
        "suggested_fix": "Update import to: import com.app.services.validation.OrderValidationService;"
    },
    {
        "failure_category": "INFRASTRUCTURE_ERROR",
        "summary": "Docker build failed - base image pull timeout",
        "failing_step": "docker build -t app:latest . @ Dockerfile:1",
        "root_cause": "Docker Hub rate limit exceeded. The CI runner has pulled too many images in the last 6 hours without authentication.",
        "suggested_fix": "Add Docker Hub credentials to CI environment or use a private registry mirror"
    },
    {
        "failure_category": "CONFIGURATION_ERROR",
        "summary": "Database migration failed - missing environment variable DB_HOST",
        "failing_step": "alembic upgrade head @ env.py:23",
        "root_cause": "The DB_HOST environment variable is not set in the CI pipeline. It was added in the latest PR but not configured in the CI secrets.",
        "suggested_fix": "Add DB_HOST to CI/CD secrets: Settings > Secrets > New secret > DB_HOST=staging-db.internal"
    },
    {
        "failure_category": "NETWORK_ERROR",
        "summary": "API integration test failed - connection refused to external service",
        "failing_step": "pytest tests/integration/test_payment_api.py @ line 42",
        "root_cause": "The payment gateway sandbox URL has changed from api.sandbox.pay.com to sandbox-api.pay.com. Tests are hitting the old endpoint.",
        "suggested_fix": "Update PAYMENT_API_URL in test config to https://sandbox-api.pay.com/v2"
    },
    {
        "failure_category": "RESOURCE_EXHAUSTION",
        "summary": "Build killed by OOM - Node.js heap out of memory",
        "failing_step": "next build @ generating static pages",
        "root_cause": "Next.js static page generation is consuming more than 4GB heap. The project has 2000+ pages and the CI runner only has 4GB RAM.",
        "suggested_fix": "Set NODE_OPTIONS='--max-old-space-size=8192' in CI env, or enable incremental static regeneration (ISR) to reduce build-time pages"
    },
    {
        "failure_category": "PERMISSION_ERROR",
        "summary": "Terraform apply failed - insufficient IAM permissions",
        "failing_step": "terraform apply -auto-approve @ main.tf:45",
        "root_cause": "The CI service account is missing 'compute.instances.create' permission. The new infrastructure module adds VM instances but the SA only has network permissions.",
        "suggested_fix": "Grant 'Compute Instance Admin' role to the CI service account, or ask your cloud admin to update the SA permissions"
    },
]


class DemoCaller:
    """Demo AI caller that returns realistic mock results without calling any AI."""

    def __init__(self):
        logger.info("Demo AI mode activated - returning mock analysis results")

    async def analyze(self, prompt: str) -> str:
        """Return a realistic mock analysis based on log content."""
        # Simulate AI thinking time (1-3 seconds)
        await asyncio.sleep(random.uniform(1.0, 3.0))

        # Try to pick a relevant analysis based on keywords in the prompt
        analysis = self._pick_relevant_analysis(prompt)

        logger.info(f"Demo AI returning mock analysis: {analysis['failure_category']}")
        return json.dumps(analysis)

    def _pick_relevant_analysis(self, prompt: str) -> dict:
        """Pick the most relevant mock analysis based on log keywords."""
        prompt_lower = prompt.lower()

        keyword_mapping = {
            "npm": 0, "node_modules": 0, "package.json": 0, "dependency": 0,
            "test": 1, "pytest": 1, "jest": 1, "assertion": 1, "assert": 1,
            "compile": 2, "javac": 2, "mvn": 2, "gradle": 2, "build failed": 2,
            "docker": 3, "image": 3, "pull": 3, "registry": 3,
            "env": 4, "variable": 4, "config": 4, "migration": 4, "alembic": 4,
            "connection": 5, "timeout": 5, "refused": 5, "network": 5, "api": 5,
            "memory": 6, "oom": 6, "heap": 6, "killed": 6,
            "permission": 7, "denied": 7, "terraform": 7, "iam": 7, "forbidden": 7,
        }

        scores = [0] * len(DEMO_ANALYSES)
        for keyword, idx in keyword_mapping.items():
            if keyword in prompt_lower:
                scores[idx] += 1

        best_idx = scores.index(max(scores)) if max(scores) > 0 else random.randint(0, len(DEMO_ANALYSES) - 1)
        return DEMO_ANALYSES[best_idx]
