from pydantic import BaseModel

class ScreeningResult(BaseModel):
    trust_score: float
    similarity_score: float
    extracted_skills: list[str]
    required_skills: list[str]
    missing_skills: list[str]
    feedback: str