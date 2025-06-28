import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    EMBEDDING_MODEL: str = "models/embedding-001"
    LLM_MODEL: str = "gemini-2.0-flash"

settings = Settings()