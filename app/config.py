"""Configuration settings for the application."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    # AI Provider
    ai_provider: str = "ollama"  # ollama or vertex
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "cicd_analyzer"
    postgres_user: str = "analyzer"
    postgres_password: str = "changeme_in_production"
    
    # ChromaDB
    chromadb_path: str = "./chroma_data"
    
    # CI Platforms
    jenkins_url: str = "http://localhost:8080"
    jenkins_user: str = "admin"
    jenkins_token: str = ""
    github_token: str = ""
    teamcity_url: str = "http://localhost:8111"
    teamcity_token: str = ""
    
    # Notifications
    slack_webhook_url: str = ""
    
    # Vertex AI (org)
    vertex_project_id: str = ""
    vertex_location: str = "us-central1"
    
    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def postgres_dsn(self) -> str:
        """Returns the PostgreSQL connection string."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

@lru_cache
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()
