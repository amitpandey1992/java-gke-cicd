import httpx
from typing import Optional
from .base_fetcher import BaseFetcher, BuildInfo
import logging

logger = logging.getLogger(__name__)

class JenkinsFetcher(BaseFetcher):
    def __init__(self, jenkins_url: str, username: str, api_token: str):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.auth = (username, api_token)

    async def fetch_log(self, build_url: Optional[str] = None, job_name: Optional[str] = None, build_number: Optional[str] = None) -> BuildInfo:
        """Fetch build log from Jenkins."""
        if not build_url and not (job_name and build_number):
            raise ValueError("Must provide either build_url or both job_name and build_number")

        if not build_url:
            build_url = f"{self.jenkins_url}/job/{job_name}/{build_number}"

        console_url = f"{build_url.rstrip('/')}/consoleText"

        async with httpx.AsyncClient(auth=self.auth) as client:
            try:
                response = await client.get(console_url)
                response.raise_for_status()
                raw_log = response.text
                
                # We extract job_name and build_id from URL if not provided
                extracted_job = job_name or "unknown_job"
                extracted_id = build_number or "unknown_id"
                
                return BuildInfo(
                    provider="jenkins",
                    job_name=extracted_job,
                    build_id=extracted_id,
                    build_url=build_url,
                    status="completed", # Jenkins consoleText doesn't give status directly
                    raw_log=raw_log
                )
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching log from Jenkins: {e}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Network error fetching log from Jenkins: {e}")
                raise

    async def validate_connection(self) -> bool:
        """Test connectivity to Jenkins."""
        async with httpx.AsyncClient(auth=self.auth) as client:
            try:
                response = await client.get(f"{self.jenkins_url}/api/json")
                response.raise_for_status()
                return True
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.error(f"Failed to connect to Jenkins: {e}")
                return False
