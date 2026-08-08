import httpx
from typing import Optional
from .base_fetcher import BaseFetcher, BuildInfo
import logging

logger = logging.getLogger(__name__)

class TeamCityFetcher(BaseFetcher):
    def __init__(self, teamcity_url: str, auth_token: str):
        self.teamcity_url = teamcity_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json"
        }

    async def fetch_log(self, build_id: Optional[str] = None) -> BuildInfo:
        """Fetch build log from TeamCity."""
        if not build_id:
            raise ValueError("Must provide build_id")

        log_url = f"{self.teamcity_url}/app/rest/builds/id:{build_id}/log"
        info_url = f"{self.teamcity_url}/app/rest/builds/id:{build_id}"

        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                # Fetch build info
                info_response = await client.get(info_url)
                info_response.raise_for_status()
                build_data = info_response.json()
                
                job_name = build_data.get("buildTypeId", "unknown_job")
                status = build_data.get("status", "unknown")
                build_url = build_data.get("webUrl", "")

                # Fetch log text
                # Note: TeamCity log endpoint returns plain text
                log_headers = self.headers.copy()
                log_headers["Accept"] = "text/plain"
                log_response = await client.get(log_url, headers=log_headers)
                log_response.raise_for_status()
                raw_log = log_response.text
                
                return BuildInfo(
                    provider="teamcity",
                    job_name=job_name,
                    build_id=build_id,
                    build_url=build_url,
                    status=status,
                    raw_log=raw_log
                )
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching log from TeamCity: {e}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Network error fetching log from TeamCity: {e}")
                raise

    async def validate_connection(self) -> bool:
        """Test connectivity to TeamCity."""
        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                response = await client.get(f"{self.teamcity_url}/app/rest/server")
                response.raise_for_status()
                return True
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.error(f"Failed to connect to TeamCity: {e}")
                return False
