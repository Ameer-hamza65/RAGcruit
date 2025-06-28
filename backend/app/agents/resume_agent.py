from langgraph.graph import StateGraph, END
from app.core.state import AgentState
from app.agents.skill_extractor import extract_skills
from app.agents.trust_score import calculate_similarity, calculate_trust_score
from app.services.embedding_service import embedding_service
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings

llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL,
    temperature=0.7,
    google_api_key=settings.GOOGLE_API_KEY
)

def create_resume_agent():
    # Define nodes with proper state updates
    def extract_text_node(state: AgentState):
        # No change needed - just passing through
        return state

    def extract_skills_node(state: AgentState):
        state.extracted_skills = extract_skills(state.resume_text, "resume")
        return {"extracted_skills": state.extracted_skills}

    def process_jd_node(state: AgentState):
        state.required_skills = extract_skills(state.job_description, "jd")
        return {"required_skills": state.required_skills}

    def calculate_similarity_node(state: AgentState):
        state.resume_embedding = embedding_service.embed_query(state.resume_text)
        state.jd_embedding = embedding_service.embed_query(state.job_description)
        state.similarity_score = calculate_similarity(
            state.resume_embedding, 
            state.jd_embedding
        )
        return {"similarity_score": state.similarity_score}

    def find_missing_skills_node(state: AgentState):
        state.missing_skills = list(set(state.required_skills) - set(state.extracted_skills))
        return {"missing_skills": state.missing_skills}

    def generate_feedback_node(state: AgentState):
        prompt = ChatPromptTemplate.from_template(
            "As a professional career coach, analyze this resume against the job description. "
            "Provide specific improvement suggestions. Focus on missing skills: {missing_skills}. "
            "Match similarity score: {score}/10\n\n"
            "Resume Summary: {resume}\n\nJob Description: {jd}"
        )
        
        chain = prompt | llm | StrOutputParser()
        state.feedback_report = chain.invoke({
            "missing_skills": ", ".join(state.missing_skills),
            "score": round(state.similarity_score * 10, 2),
            "resume": state.resume_text[:2000],
            "jd": state.job_description[:2000]
        })
        return {"feedback_report": state.feedback_report}

    def calculate_trust_score_node(state: AgentState):
        state.trust_score = calculate_trust_score(state)
        return {"trust_score": state.trust_score}

    # Build workflow with proper state merging
    workflow = StateGraph(AgentState)

    workflow.add_node("extract_text", extract_text_node)
    workflow.add_node("extract_skills", extract_skills_node)
    workflow.add_node("process_jd", process_jd_node)
    workflow.add_node("calculate_similarity", calculate_similarity_node)
    workflow.add_node("find_missing_skills", find_missing_skills_node)
    workflow.add_node("generate_feedback", generate_feedback_node)
    workflow.add_node("calculate_trust_score", calculate_trust_score_node)

    workflow.set_entry_point("extract_text")
    workflow.add_edge("extract_text", "extract_skills")
    workflow.add_edge("extract_skills", "process_jd")
    workflow.add_edge("process_jd", "calculate_similarity")
    workflow.add_edge("calculate_similarity", "find_missing_skills")
    workflow.add_edge("find_missing_skills", "generate_feedback")
    workflow.add_edge("generate_feedback", "calculate_trust_score")
    workflow.add_edge("calculate_trust_score", END)

    # Add conditional edges if needed
    return workflow.compile()