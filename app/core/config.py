import yaml
from pathlib import Path
from typing import List, Dict, Any

from pydantic_settings import BaseSettings
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration Models ---
class ApiSettings(BaseModel):
    host: str
    port: int
    debug: bool
    cors_origins: List[str]

class OpenAISettings(BaseModel):
    model: str
    max_tokens: int
    temperature: float

class VectorDBSettings(BaseModel):
    embedding_model: str
    chunk_size: int
    chunk_overlap: int

class PathSettings(BaseModel):
    data_dir: str
    projects_dir: str
    exports_dir: str
    resumes_dir: str
    embeddings_dir: str

class ResumeSettings(BaseModel):
    max_projects: int
    max_skills: int
    section_order: List[str]

class ProjectAnalysisSettings(BaseModel):
    relevance_threshold: float
    max_recommendations: int
    skill_extraction_enabled: bool

class Settings(BaseSettings):
    api: ApiSettings
    openai: OpenAISettings
    vector_db: VectorDBSettings
    paths: PathSettings
    resume: ResumeSettings
    project_analysis: ProjectAnalysisSettings
    
    # Load directly from environment for secrets
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Create directories
        for path in vars(self.paths).values():
            os.makedirs(path, exist_ok=True)

def load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

# --- Load Settings ---
config_path = Path("config/settings.yaml")
yaml_config = load_yaml_config(config_path)

settings = Settings(**yaml_config) 