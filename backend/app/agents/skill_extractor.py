from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings

llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL,
    temperature=0.7,
    google_api_key=settings.GOOGLE_API_KEY
)

def extract_skills(text: str, context: str = "resume") -> list:
    """Extract skills from text using Gemini Pro."""
    prompt_type = {
        "resume": "Extract technical skills from this resume text. Return ONLY comma-separated values:",
        "jd": "Extract required technical skills from this job description. Return ONLY comma-separated values:"
    }
    
    prompt = ChatPromptTemplate.from_template(
        f"{prompt_type[context]}\n\n{{text}}"
    )
    chain = prompt | llm | StrOutputParser()
    skills = chain.invoke({"text": text})
    return [s.strip() for s in skills.split(",") if s.strip()]