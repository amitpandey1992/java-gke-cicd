import httpx
import zipfile
import io
from typing import Optional
from .base_fetcher import BaseFetcher, BuildInfo
import logging

logger = logging.getLogger(__name__)

class GitHubFetcher(BaseFetcher):
    def __init__(self, github_token: str):
        self.headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self.base_url = "https://api.github.com"

    async def fetch_log(self, repo: Optional[str] = None, run_id: Optional[str] = None) -> BuildInfo:
        """Fetch build log from GitHub Actions."""
        if not repo or not run_id:
            raise ValueError("Must provide both repo and run_id")

        info_url = f"{self.base_url}/repos/{repo}/actions/runs/{run_id}"
        logs_url = f"{self.base_url}/repos/{repo}/actions/runs/{run_id}/logs"

        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            try:
                # Fetch run info
                info_response = await client.get(info_url)
                info_response.raise_for_status()
                run_data = info_response.json()
                
                job_name = run_data.get("name", "unknown_workflow")
                status = run_data.get("conclusion", "unknown")
                build_url = run_data.get("html_url", "")

                # Fetch logs zip
                logs_response = await client.get(logs_url)
                logs_response.raise_for_status()
                
                # Extract and concatenate log files
                raw_log = ""
                with zipfile.ZipFile(io.BytesIO(logs_response.content)) as z:
                    for filename in z.namelist():
                        if not filename.endswith('/'): # Ignore directories
                            with z.open(filename) as f:
                                raw_log += f"\\n--- {filename} ---\\n"
                                raw_log += f.read().decode('utf-8', errors='replace')
                
                return BuildInfo(
                    provider="github",
                    job_name=job_name,
                    build_id=str(run_id),
                    build_url=build_url,
                    status=status,
                    raw_log=raw_log
                )
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching log from GitHub: {e}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Network error fetching log from GitHub: {e}")
                raise

    async def validate_connection(self) -> bool:
        """Test connectivity to GitHub."""
        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                response = await client.get(f"{self.base_url}/user")
                response.raise_for_status()
                return True
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.error(f"Failed to connect to GitHub: {e}")
                return False
