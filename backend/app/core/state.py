from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import operator
from functools import reduce

class AgentState(BaseModel):
    resume_text: str = ""
    job_description: str = ""
    extracted_skills: List[str] = []
    required_skills: List[str] = []
    missing_skills: List[str] = []
    similarity_score: float = 0.0
    feedback_report: str = ""
    trust_score: float = 0.0
    resume_embedding: Optional[List[float]] = None
    jd_embedding: Optional[List[float]] = None

    def __add__(self, other: Dict[str, Any]) -> "AgentState":
        state_dict = self.dict()
        for key, value in other.items():
            if key in state_dict:
                state_dict[key] = value
        return AgentState(**state_dict)