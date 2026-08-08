from .ollama_caller import OllamaCaller
from .vertex_caller import VertexCaller
from .demo_caller import DemoCaller

def get_ai_caller(settings):
    """Factory to return the configured AI caller.
    
    Supported providers:
        - 'ollama': Local Ollama AI (needs 8GB+ RAM)
        - 'vertex': Google Vertex AI (needs GCP credentials)
        - 'demo': Mock AI for testing/demo (no requirements)
    """
    provider = settings.ai_provider.lower()
    if provider == 'ollama':
        return OllamaCaller(host=settings.ollama_host, model=settings.ollama_model)
    elif provider == 'vertex':
        return VertexCaller(project_id=settings.vertex_project_id, location=settings.vertex_location)
    elif provider == 'demo':
        return DemoCaller()
    else:
        raise ValueError(f"Unknown AI provider configured: {settings.ai_provider}. Use 'ollama', 'vertex', or 'demo'.")
