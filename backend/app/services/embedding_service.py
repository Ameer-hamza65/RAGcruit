from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY
        )
    
    def embed_query(self, text: str) -> list:
        return self.embeddings.embed_query(text)

embedding_service = EmbeddingService()