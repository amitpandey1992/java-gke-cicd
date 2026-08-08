from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class BuildInfo:
    provider: str
    job_name: str
    build_id: str
    build_url: str
    status: str
    raw_log: str
    timestamp: Optional[str] = None

class BaseFetcher(ABC):
    @abstractmethod
    async def fetch_log(self, **kwargs) -> BuildInfo:
        """Fetch build log from CI platform."""
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Test connectivity to CI platform."""
        pass
