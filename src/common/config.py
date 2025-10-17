"""
Configuration management with environment variables and flags.
Supports GPU/CPU toggles, API key rotation, and all system flags.
"""

import os
from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config(BaseSettings):
    """Main configuration class with all system flags and settings."""
    
    # Paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = Field(default="data")
    reports_dir: Path = Field(default="reports")
    
    # Vector Database
    vector_db: str = Field(default="qdrant", env="VECTOR_DB")
    qdrant_url: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    qdrant_collection_name: str = Field(default="multilingual_docs", env="QDRANT_COLLECTION_NAME")
    
    # Embeddings
    embedding_model: str = Field(default="models/text-embedding-004", env="EMBEDDING_MODEL")
    gemini_api_keys: str = Field(default="", env="GEMINI_API_KEYS")
    
    # LLMs
    llm_primary: str = Field(default="ollama:deepseek-r1:1.5b", env="LLM_PRIMARY")
    llm_fallback: str = Field(default="gemini-1.5-flash-latest", env="LLM_FALLBACK")
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    
    # Retrieval
    enable_bm25: bool = Field(default=True, env="ENABLE_BM25")
    fusion_method: str = Field(default="weighted", env="FUSION_METHOD")
    dense_weight: float = Field(default=0.6, env="DENSE_WEIGHT")
    keyword_weight: float = Field(default=0.4, env="KEYWORD_WEIGHT")
    
    # Reranking
    enable_rerank: bool = Field(default=True, env="ENABLE_RERANK")
    rerank_backend: str = Field(default="gemini", env="RERANK_BACKEND")
    rerank_top_k: int = Field(default=30, env="RERANK_TOP_K")
    
    # Query Decomposition
    enable_decomposition: bool = Field(default=True, env="ENABLE_DECOMPOSITION")
    
    # Metadata Filters
    enable_metadata_filter: bool = Field(default=True, env="ENABLE_METADATA_FILTER")
    
    # Evaluation
    enable_eval: bool = Field(default=True, env="ENABLE_EVAL")
    eval_model: str = Field(default="gemini-1.5-flash-latest", env="EVAL_MODEL")
    
    # OCR
    ocr_engine: str = Field(default="tesseract", env="OCR_ENGINE")
    ocr_langs: str = Field(default="eng,chi_sim,hin,ben,urd", env="OCR_LANGS")
    tesseract_cmd: Optional[str] = Field(default=None, env="TESSERACT_CMD")
    enable_llm_cleanup: bool = Field(default=False, env="ENABLE_LLM_CLEANUP")
    
    # System
    enable_gpu: bool = Field(default=False, env="ENABLE_GPU")
    use_docker_gpu: bool = Field(default=False, env="USE_DOCKER_GPU")
    gpu_platform: str = Field(default="windows", env="GPU_PLATFORM")
    
    # Rate Limiting
    key_rotation_strategy: str = Field(default="round_robin_backoff", env="KEY_ROTATION_STRATEGY")
    rate_limit_rpm: int = Field(default=90, env="RATE_LIMIT_RPM")
    
    # Chunking
    chunk_size: int = Field(default=500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=65, env="CHUNK_OVERLAP")
    
    @validator("gemini_api_keys", pre=True, always=True)
    def parse_gemini_keys(cls, v):
        """Parse comma-separated Gemini API keys."""
        if isinstance(v, str):
            # Return the string as-is, will be parsed later
            return v
        return v or ""
    
    def get_gemini_keys(self) -> List[str]:
        """Get parsed list of Gemini API keys."""
        if not self.gemini_api_keys:
            return []
        return [k.strip() for k in self.gemini_api_keys.split(",") if k.strip()]
    
    @validator("data_dir", "reports_dir", pre=True, always=True)
    def resolve_paths(cls, v, values):
        """Resolve paths relative to project root."""
        if isinstance(v, str):
            v = Path(v)
        if not v.is_absolute():
            root = values.get("project_root", Path.cwd())
            v = root / v
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("tesseract_cmd", pre=True, always=True)
    def set_tesseract_cmd(cls, v):
        """Set Tesseract command based on platform."""
        if v:
            return v
        # Auto-detect based on platform
        if os.name == "nt":  # Windows
            return r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        else:  # Linux/Mac
            return "tesseract"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_incoming_dir(self, lang: str) -> Path:
        """Get incoming directory for a language."""
        path = self.data_dir / "incoming" / lang
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_processing_dir(self) -> Path:
        """Get processing directory."""
        path = self.data_dir / "processing"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_ocr_raw_dir(self) -> Path:
        """Get OCR raw directory."""
        path = self.data_dir / "ocr_raw"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_ocr_clean_dir(self) -> Path:
        """Get OCR clean directory."""
        path = self.data_dir / "ocr_clean"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_chunks_dir(self) -> Path:
        """Get chunks directory."""
        path = self.data_dir / "chunks"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_embeddings_dir(self) -> Path:
        """Get embeddings directory."""
        path = self.data_dir / "embeddings"
        path.mkdir(parents=True, exist_ok=True)
        return path


# Global config instance
config = Config()

