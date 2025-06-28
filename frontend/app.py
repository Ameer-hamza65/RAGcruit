import streamlit as st
import requests
import time

# Initialize session state at the very top
if "results" not in st.session_state:
    st.session_state.results = None
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

# Page configuration
st.set_page_config(
    page_title="RAGcruit",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
def load_css():
    st.markdown(f"""
    <style>
    :root {{
        --red: #ff4b4b;
        --orange: #f0ad4e;
        --green: #5cb85c;
    }}
    
    .progress-container {{
        width: 100%;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin: 20px 0;
        overflow: hidden;
        height: 30px;
    }}
    
    .progress-bar {{
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
        position: relative;
    }}
    
    .progress-text {{
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        color: white;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }}
    
    [data-testid="metric-container"] {{
        text-align: center;
        background: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    .stButton>button {{
        background-color: #4CAF50 !important;
        color: white !important;
    }}
    </style>
    """, unsafe_allow_html=True)

load_css()

# Header
st.title("🚀 RAGcruit")
st.subheader("Dynamic RAG System for Resume with Trust Scoring")

# How it works section
with st.expander("ℹ️ How This Works", expanded=True):
    st.markdown("""
    **Multi-Agent Workflow:**
    1. 📄 **PDF Extraction** - Parse resume and job description
    2. ⚙️ **Skill Detection** - Identify technical skills
    3. 🎯 **JD Matching** - Compare against job requirements
    4. 📊 **Similarity Scoring** - Semantic match evaluation
    5. 💡 **Feedback Generation** - Improvement suggestions
    6. ✅ **Trust Score** - Overall match quality (0-100)
    """)

# Main columns
col1, col2 = st.columns([1, 1.5], gap="large")

with col1:
    st.header("Upload Documents")
    
    with st.form("upload_form", clear_on_submit=False):
        resume_file = st.file_uploader(
            "Upload Resume (PDF)", 
            type="pdf",
            key="resume_uploader"
        )
        job_description_text = st.text_area(
            "Paste Job Description",
            height=300,
            key="jd_text_area",
            placeholder="Paste the job description here...",
            help="Copy and paste the full job description text"
        )
        
        # Debug info
        st.write(f"Resume file uploaded: {resume_file is not None}")
        st.write(f"JD text provided: {bool(job_description_text and job_description_text.strip())}")
        
        # Submit button with manual validation
        submitted = st.form_submit_button("Analyze Resume", use_container_width=True)
        
        if submitted:
            # Validate inputs
            if not resume_file:
                st.error("Please upload a resume PDF")
                st.stop()
                
            if not job_description_text or not job_description_text.strip():
                st.error("Please enter a job description")
                st.stop()
                
            st.session_state.form_submitted = True
        else:
            st.session_state.form_submitted = False

# If form was submitted, process the request
if st.session_state.form_submitted:
    with st.spinner("Processing with AI agents..."):
        start_time = time.time()
        try:
            # Prepare request data
            files = {"resume": ("resume.pdf", resume_file.getvalue(), "application/pdf")}
            data = {"job_description": job_description_text}
            
            # Call backend API
            response = requests.post(
                "http://localhost:8000/screen-resume",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                results = response.json()
                processing_time = time.time() - start_time
                st.session_state.results = results
                st.success(f"Analysis completed in {processing_time:.2f} seconds!")
            else:
                st.error(f"Backend error: {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to backend server. Make sure it's running on port 8000.")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            
    st.session_state.form_submitted = False

# Results display (moved outside the form)
with col2:
    if st.session_state.get("results"):
        results = st.session_state.results
        
        # Results header
        st.header("Screening Results")
        
        # Trust Score display
        trust_score = results["trust_score"]
        st.subheader(f"Trust Score: {trust_score}/100")
        
        # Score visualization
        progress_color = "red" if trust_score < 50 else "orange" if trust_score < 75 else "green"
        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {trust_score}%; background-color: var(--{progress_color});">
                <span class="progress-text">{trust_score}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Metrics
        col21, col22 = st.columns(2)
        with col21:
            st.metric(
                label="Similarity Score", 
                value=f"{results['similarity_score']*100:.2f}%",
                help="Semantic match between resume and job description"
            )
        with col22:
            st.metric(
                label="Missing Skills", 
                value=len(results["missing_skills"]),
                help="Required skills not found in resume"
            )
        
        # Skills analysis
        with st.expander("🔍 Skills Analysis", expanded=True):
            tab1, tab2, tab3 = st.tabs(["Extracted", "Required", "Missing"])
            
            with tab1:
                if results["extracted_skills"]:
                    st.write(results["extracted_skills"])
                else:
                    st.info("No skills extracted")
                    
            with tab2:
                if results["required_skills"]:
                    st.write(results["required_skills"])
                else:
                    st.info("No skills extracted from JD")
                    
            with tab3:
                if results["missing_skills"]:
                    st.write(results["missing_skills"])
                else:
                    st.success("All required skills are present!")
        
        # Feedback report
        st.subheader("Improvement Suggestions")
        st.markdown(results["feedback"], unsafe_allow_html=True)

# Sidebar
st.sidebar.title("About")
st.sidebar.markdown("""
**RAGcruit**  
Dynamic RAG system for automated resume screening  
using Google Gemini and LangGraph.
""")

st.sidebar.divider()
st.sidebar.header("Tech Stack")
st.sidebar.image("https://freepnglogo.com/images/all_img/1728457808_Google_Gemini_logo_PNG.png", width=80)
st.sidebar.caption("gemini-2.0-flash")
st.sidebar.image("https://python.langchain.com/img/favicon.ico", width=30)
st.sidebar.caption("LangGraph")
st.sidebar.image("https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png", width=80)
st.sidebar.caption("FastAPI")
st.sidebar.image("https://streamlit.io/images/brand/streamlit-mark-color.svg", width=30)
st.sidebar.caption("Streamlit")

if st.sidebar.button("Clear Results"):
    st.session_state.results = None
    st.session_state.form_submitted = False
    st.rerun()