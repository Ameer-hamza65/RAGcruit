from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.pdf_service import extract_text_from_pdf, is_valid_pdf
from app.agents.resume_agent import create_resume_agent
from app.core.state import AgentState
from app.models.schemas import ScreeningResult
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings
import uvicorn
import logging
import traceback
import uuid
import re
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Resume Screener API")
agent = create_resume_agent()

# Initialize LLM for name extraction
llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL,
    temperature=0.0,
    google_api_key=settings.GOOGLE_API_KEY
)

# Pydantic model for ranked candidates
class RankedCandidate(BaseModel):
    candidate_id: str
    name: str
    trust_score: float
    similarity_score: float
    missing_skills: List[str]
    extracted_skills: List[str]

@app.post("/screen-resume", response_model=ScreeningResult)
async def screen_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        # Validate PDF file
        if not is_valid_pdf(await resume.read()):
            raise HTTPException(400, "Invalid or empty PDF file")
        await resume.seek(0)  # Reset file pointer
        
        # Process resume PDF
        resume_bytes = await resume.read()
        resume_text = extract_text_from_pdf(resume_bytes)
        
        # Check if text extraction was successful
        if not resume_text.strip():
            raise HTTPException(400, "Could not extract text from PDF")
        
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

def extract_name_with_regex(text: str) -> str:
    """Try to extract name using regex patterns"""
    patterns = [
        r"^(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]*)+)",  # First Last at start
        r"\b(?:[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+)\b",  # First M. Last
        r"Name:\s*(.+)",
        r"Contact\s*Info\s*\n(.+)",
        r"Resume\s*of\s*(.+)",
        r"([A-Z][a-z]+ [A-Z][a-z]+)\s*\n\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Name followed by email
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            name = match.group(1).strip() if match.lastindex else match.group(0).strip()
            # Clean up the name
            name = re.sub(r"^(Resume|CV|Name|of|[:])", "", name, flags=re.IGNORECASE).strip()
            return name
    
    return ""

@app.post("/extract-name")
async def extract_name(resume: UploadFile = File(...)):
    try:
        # Validate PDF file
        if not is_valid_pdf(await resume.read()):
            return {"name": "Invalid PDF"}
        await resume.seek(0)  # Reset file pointer
        
        # Extract text from PDF
        resume_bytes = await resume.read()
        resume_text = extract_text_from_pdf(resume_bytes)
        
        # Check if text extraction was successful
        if not resume_text.strip():
            return {"name": "No Text Found"}
        
        # First try regex extraction
        candidate_name = extract_name_with_regex(resume_text)
        if candidate_name:
            return {"name": candidate_name}
        
        # If regex fails, use LLM with a better prompt
        prompt = ChatPromptTemplate.from_template(
            "Extract the candidate's full name from the resume text below. "
            "The name is usually at the top of the resume. "
            "Return ONLY the full name in JSON format: {{\"name\": \"John Doe\"}}. "
            "If you cannot find a name, return {{\"name\": \"Unknown Candidate\"}}.\n\n"
            "Resume Text:\n{text}"
        )
        
        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({"text": resume_text[:10000]})  # Use first 10k characters
        
        try:
            # Try to parse JSON response
            name_data = json.loads(response)
            return name_data
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract name from text
            name_match = re.search(r'[\'"]?name[\'"]?\s*:\s*[\'"](.+?)[\'"]', response)
            if name_match:
                return {"name": name_match.group(1).strip()}
            
            # Return the first proper name structure found in the response
            name_match = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+)', response)
            if name_match:
                return {"name": name_match.group(0)}
            
            return {"name": "Unknown Candidate"}
        
    except Exception as e:
        logger.error(f"Name extraction error: {str(e)}")
        return {"name": "Unknown Candidate"}

@app.post("/rank-resumes", response_model=List[RankedCandidate])
async def rank_resumes(
    job_description: str = Form(...),
    resumes: List[UploadFile] = File(...)
):
    try:
        if not resumes:
            raise HTTPException(400, "No resumes uploaded")
            
        results = []
        names = []
        valid_resumes = []
        
        # Validate all resumes first
        for resume in resumes:
            try:
                # Check if PDF is valid
                if not is_valid_pdf(await resume.read()):
                    logger.warning(f"Invalid PDF: {resume.filename}")
                    continue
                await resume.seek(0)  # Reset file pointer
                valid_resumes.append(resume)
            except Exception as e:
                logger.error(f"Error validating resume {resume.filename}: {str(e)}")
        
        if not valid_resumes:
            raise HTTPException(400, "No valid PDF files uploaded")
        
        # First pass: Extract names
        for resume in valid_resumes:
            name_response = await extract_name(resume)
            names.append(name_response["name"])
            await resume.seek(0)  # Reset file pointer after name extraction
        
        # Second pass: Process resumes
        for i, resume in enumerate(valid_resumes):
            try:
                # Process resume
                resume_bytes = await resume.read()
                resume_text = extract_text_from_pdf(resume_bytes)
                
                # Check if text extraction was successful
                if not resume_text.strip():
                    logger.warning(f"Empty text from: {resume.filename}")
                    continue
                
                # Create unique ID for candidate
                candidate_id = str(uuid.uuid4())
                
                # Run screening
                state = AgentState(
                    resume_text=resume_text,
                    job_description=job_description
                )
                result = agent.invoke(state)
                result_model = AgentState(**result)
                
                results.append({
                    "candidate_id": candidate_id,
                    "name": names[i],
                    "trust_score": result_model.trust_score,
                    "similarity_score": round(result_model.similarity_score, 4),
                    "missing_skills": result_model.missing_skills,
                    "extracted_skills": result_model.extracted_skills
                })
            except Exception as e:
                logger.error(f"Error processing resume {resume.filename}: {str(e)}")
                results.append({
                    "candidate_id": str(uuid.uuid4()),
                    "name": names[i],
                    "trust_score": 0.0,
                    "similarity_score": 0.0,
                    "missing_skills": ["Processing Error"],
                    "extracted_skills": ["Processing Error"]
                })
        
        # Sort by trust_score descending
        results.sort(key=lambda x: x["trust_score"], reverse=True)
        return results
        
    except Exception as e:
        logger.error(f"Ranking error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Ranking error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)