"""
Centralized configuration for CardNinja

Load configuration from environment variables or .env file.
Copy config.example.env to .env and fill in your values.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
ENV_FILE = Path(__file__).parent / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class Config:
    """Application configuration"""
    
    # ===================
    # LLM Configuration
    # ===================
    
    # Provider: gemini, groq, mistral, ollama, lmstudio, llamacpp
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    
    # Model name (depends on provider)
    # Gemini: gemini-2.0-flash-exp, gemini-1.5-flash, gemini-1.5-pro
    # Groq: llama-3.1-70b-versatile, mixtral-8x7b-32768
    # Mistral: mistral-small-latest, mistral-medium-latest
    # Ollama: llama3.2, mistral, etc.
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")
    
    # Base URL for local LLM providers
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    
    # ===================
    # API Keys (supports multiple comma-separated keys for rotation)
    # ===================
    
    # Google Gemini - Free: https://aistudio.google.com/apikey
    # Single key: GEMINI_API_KEY=your_key
    # Multiple keys: GEMINI_API_KEYS=key1,key2,key3
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_API_KEYS: str = os.getenv("GEMINI_API_KEYS", "")
    
    # Groq - Free: https://console.groq.com/keys
    # Single key: GROQ_API_KEY=your_key
    # Multiple keys: GROQ_API_KEYS=key1,key2,key3
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_API_KEYS: str = os.getenv("GROQ_API_KEYS", "")
    
    # Mistral AI - Free tier: https://console.mistral.ai/
    # Single key: MISTRAL_API_KEY=your_key
    # Multiple keys: MISTRAL_API_KEYS=key1,key2,key3
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    MISTRAL_API_KEYS: str = os.getenv("MISTRAL_API_KEYS", "")
    
    # ===================
    # Server Configuration
    # ===================
    
    # API Server
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    # PORT is set by Render, API_PORT is fallback for local dev
    API_PORT: int = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
    
    # CORS Origins (comma-separated) - include production URLs
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://127.0.0.1:3000,https://cardninja.vercel.app"
    ).split(",")
    
    # ===================
    # Admin Configuration
    # ===================
    
    # Password for admin panel (set in .env)
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    
    # ===================
    # Data Paths
    # ===================
    
    DATA_DIR: Path = Path(__file__).parent / "data"
    CARDS_FILE: Path = DATA_DIR / "cards.json"
    CARD_SOURCES_FILE: Path = DATA_DIR / "card_sources.json"
    
    # ===================
    # Scraper Configuration
    # ===================
    
    # Delay between scraping requests (seconds)
    # 2 minutes (120s) to avoid rate limits on free LLM APIs
    SCRAPE_DELAY: float = float(os.getenv("SCRAPE_DELAY", "120.0"))
    
    # Request timeout (seconds)
    SCRAPE_TIMEOUT: float = float(os.getenv("SCRAPE_TIMEOUT", "30.0"))
    
    # User agent for scraping
    SCRAPE_USER_AGENT: str = os.getenv(
        "SCRAPE_USER_AGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    )
    
    @classmethod
    def get_api_key(cls) -> str:
        """Get the first API key for the current provider (for backward compatibility)"""
        keys = cls.get_api_keys()
        return keys[0] if keys else ""
    
    @classmethod
    def get_api_keys(cls) -> list:
        """Get all API keys for the current provider as a list.
        
        Supports both single key (PROVIDER_API_KEY) and multiple keys (PROVIDER_API_KEYS).
        Multiple keys should be comma-separated.
        """
        keys = []
        
        if cls.LLM_PROVIDER == "gemini":
            # Check for multiple keys first, then fall back to single key
            if cls.GEMINI_API_KEYS:
                keys = [k.strip() for k in cls.GEMINI_API_KEYS.split(",") if k.strip()]
            elif cls.GEMINI_API_KEY:
                keys = [cls.GEMINI_API_KEY]
        elif cls.LLM_PROVIDER == "groq":
            if cls.GROQ_API_KEYS:
                keys = [k.strip() for k in cls.GROQ_API_KEYS.split(",") if k.strip()]
            elif cls.GROQ_API_KEY:
                keys = [cls.GROQ_API_KEY]
        elif cls.LLM_PROVIDER == "mistral":
            if cls.MISTRAL_API_KEYS:
                keys = [k.strip() for k in cls.MISTRAL_API_KEYS.split(",") if k.strip()]
            elif cls.MISTRAL_API_KEY:
                keys = [cls.MISTRAL_API_KEY]
        
        return keys
    
    @classmethod
    def is_cloud_provider(cls) -> bool:
        """Check if using a cloud LLM provider"""
        return cls.LLM_PROVIDER in ["gemini", "groq", "mistral"]
    
    @classmethod
    def validate(cls) -> list:
        """Validate configuration and return list of errors"""
        errors = []
        
        if cls.is_cloud_provider() and not cls.get_api_keys():
            errors.append(
                f"{cls.LLM_PROVIDER.upper()}_API_KEY or {cls.LLM_PROVIDER.upper()}_API_KEYS not set. "
                f"Get free keys and add them to backend/.env"
            )
        
        if not cls.DATA_DIR.exists():
            errors.append(f"Data directory not found: {cls.DATA_DIR}")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Print current configuration (hiding sensitive keys)"""
        print("=" * 50)
        print("CardNinja Configuration")
        print("=" * 50)
        print(f"LLM Provider:  {cls.LLM_PROVIDER}")
        print(f"LLM Model:     {cls.LLM_MODEL}")
        
        if cls.is_cloud_provider():
            keys = cls.get_api_keys()
            if keys:
                print(f"API Keys:      {len(keys)} key(s) configured")
                for i, key in enumerate(keys):
                    masked = f"{key[:6]}...{key[-4:]}" if len(key) > 10 else "****"
                    print(f"  [{i+1}] {masked}")
            else:
                print(f"API Keys:      NOT SET")
        else:
            print(f"LLM Base URL:  {cls.LLM_BASE_URL}")
        
        print(f"API Server:    {cls.API_HOST}:{cls.API_PORT}")
        print(f"Data Dir:      {cls.DATA_DIR}")
        print("=" * 50)


# Create a singleton instance
config = Config()
