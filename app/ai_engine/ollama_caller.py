import httpx
import logging
import time

logger = logging.getLogger(__name__)

class OllamaCaller:
    def __init__(self, host: str, model: str):
        self.host = host.rstrip('/')
        self.model = model

    async def analyze(self, prompt: str) -> str:
        """Call Ollama API for text generation."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        logger.info(f"Sending request to Ollama ({self.model})...")
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                elapsed = time.time() - start_time
                logger.info(f"Ollama response received in {elapsed:.2f}s")
                
                return data.get('response', '')
            except httpx.TimeoutException as e:
                logger.error(f"Ollama request timed out after 120s: {e}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Failed to connect to Ollama: {e}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama returned HTTP error: {e}")
                raise
