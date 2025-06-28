from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from app.services.pdf_service import extract_text_from_pdf
from app.agents.resume_agent import create_resume_agent
from app.core.state import AgentState
from app.models.schemas import ScreeningResult
import uvicorn
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Resume Screener API")
agent = create_resume_agent()

@app.post("/screen-resume", response_model=ScreeningResult)
async def screen_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        # Process resume PDF
        resume_bytes = await resume.read()
        resume_text = extract_text_from_pdf(resume_bytes)
        
        # Initialize agent state
        state = AgentState(
            resume_text=resume_text,
            job_description=job_description
        )
        
        # Execute agent workflow
        result = agent.invoke(state)
        
        # Convert to Pydantic model for proper serialization
        result_model = AgentState(**result)
        
        return {
            "trust_score": result_model.trust_score,
            "similarity_score": round(result_model.similarity_score, 4),
            "extracted_skills": result_model.extracted_skills,
            "required_skills": result_model.required_skills,
            "missing_skills": result_model.missing_skills,
            "feedback": result_model.feedback_report
        }
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Processing error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)