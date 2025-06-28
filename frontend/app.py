import streamlit as st
import requests
import time
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="RAGruit", 
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
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    }}
    
    .stButton>button:disabled {{
        background-color: #cccccc !important;
        cursor: not-allowed;
    }}
    
    .ranking-table {{
        margin-bottom: 20px;
        font-size: 16px;
    }}
    
    .top-candidate {{
        font-weight: bold;
        color: #2e7d32;
    }}
    </style>
    """, unsafe_allow_html=True)

load_css()

# Initialize session state
if "results" not in st.session_state:
    st.session_state.results = None
if "ranking_results" not in st.session_state:
    st.session_state.ranking_results = None
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "ranking_submitted" not in st.session_state:
    st.session_state.ranking_submitted = False

# Header
st.title("🚀 RAGruit")
st.subheader("Dynamic RAG System for Resume with Trust Scoring and Ranking")

# How it works section
with st.expander("ℹ️ How This Works", expanded=True):
    st.markdown("""
    **Multi-Agent Workflow:**
    1. 📄 **PDF Extraction** - Parse resume and job description
    2. ⚙️ **Skill Detection** - Identify technical skills
    3. 🎯 **JD Matching** - Compare against job requirements
    4. 📊 **Similarity Scoring** - Semantic match evaluation
    5. ✅ **Trust Score** - Overall match quality (0-100)
    
    **HR Features:**
    - Single candidate detailed analysis
    - Multi-candidate ranking system
    - Candidate name detection
    """)

# Main columns
col1, col2 = st.columns([1, 1.5], gap="large")

with col1:
    # Tab interface for single vs multiple resumes
    tab1, tab2 = st.tabs(["Single Candidate", "Rank Candidates"])
    
    with tab1:
        st.header("Single Candidate Screening")
        with st.form("single_form", clear_on_submit=False):
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
            
            submitted = st.form_submit_button("Analyze Resume", use_container_width=True)
            
            if submitted:
                # Validate inputs
                if not resume_file:
                    st.error("Please upload a resume PDF")
                    st.stop()
                    
                if not job_description_text.strip():
                    st.error("Please enter a job description")
                    st.stop()
                    
                st.session_state.form_submitted = True
            else:
                st.session_state.form_submitted = False
    
    with tab2:
        st.header("Rank Candidates")
        with st.form("ranking_form", clear_on_submit=False):
            resume_files = st.file_uploader(
                "Upload Resumes (PDF)", 
                type="pdf",
                accept_multiple_files=True,
                key="resumes_uploader",
                help="Upload multiple candidate resumes"
            )
            ranking_jd_text = st.text_area(
                "Paste Job Description",
                height=300,
                key="ranking_jd_text",
                placeholder="Paste the job description here...",
                help="Copy and paste the full job description text"
            )
            
            ranking_submitted = st.form_submit_button("Rank Candidates", use_container_width=True)
            
            if ranking_submitted:
                # Validate inputs
                if not resume_files:
                    st.error("Please upload at least one resume")
                    st.stop()
                    
                if not ranking_jd_text.strip():
                    st.error("Please enter a job description")
                    st.stop()
                    
                st.session_state.ranking_submitted = True
            else:
                st.session_state.ranking_submitted = False

# Single candidate processing
if st.session_state.form_submitted:
    with st.spinner("Processing candidate..."):
        start_time = time.time()
        try:
            # Prepare request data
            files = {"resume": ("resume.pdf", resume_file.getvalue(), "application/pdf")}
            data = {"job_description": job_description_text}
            
            # Call backend API
            response = requests.post(
                "http://localhost:8000/screen-resume",
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                results = response.json()
                processing_time = time.time() - start_time
                st.session_state.results = results
                st.session_state.ranking_results = None  # Clear previous ranking results
                st.success(f"Analysis completed in {processing_time:.2f} seconds!")
            else:
                st.error(f"Backend error: {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to backend server. Make sure it's running on port 8000")
        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again with smaller files")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            
    st.session_state.form_submitted = False

# Candidate ranking processing
if st.session_state.ranking_submitted:
    with st.spinner(f"Processing {len(resume_files)} candidates. This may take a while..."):
        start_time = time.time()
        try:
            # Prepare request data
            files = []
            for i, resume in enumerate(resume_files):
                files.append(("resumes", (f"resume_{i}.pdf", resume.getvalue(), "application/pdf")))
            
            # Call ranking API
            response = requests.post(
                "http://localhost:8000/rank-resumes",
                files=files,
                data={"job_description": ranking_jd_text},
                timeout=len(resume_files) * 30  # 30 seconds per resume
            )
            
            if response.status_code == 200:
                ranking_results = response.json()
                processing_time = time.time() - start_time
                st.session_state.ranking_results = ranking_results
                st.session_state.results = None  # Clear previous single result
                st.success(f"Ranked {len(ranking_results)} candidates in {processing_time:.2f} seconds!")
            else:
                st.error(f"Ranking error: {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to backend server. Make sure it's running on port 8000")
        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again with fewer resumes")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            
    st.session_state.ranking_submitted = False

# Results display
with col2:
    # Single candidate results
    if st.session_state.get("results"):
        results = st.session_state.results
        
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
    
    # Ranking results
    elif st.session_state.get("ranking_results"):
        ranking_results = st.session_state.ranking_results
        
        st.header("Candidate Ranking Results")
        
        # Create dataframe for display
        data = []
        for i, candidate in enumerate(ranking_results):
            data.append({
                "Candidate": candidate.get("name", f"Candidate {i+1}"),
                "Trust Score": candidate["trust_score"],
                "Similarity Score": candidate["similarity_score"] * 100
            })
        
        df = pd.DataFrame(data)
        
        # Display ranking table
        st.markdown("### Candidate Ranking")
        st.dataframe(
            df.style.format({
                "Trust Score": "{:.1f}%",
                "Similarity Score": "{:.1f}%"
            }),
            use_container_width=True,
            height=min(400, 45 * len(df) + 45),
            hide_index=True
        )
        
        # Download button for ranking results
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Ranking as CSV",
            data=csv,
            file_name='candidate_ranking.csv',
            mime='text/csv',
        )

# Sidebar
st.sidebar.title("About")
st.sidebar.markdown("""
**RAGruit**  
Dynamic RAG system for automated resume screening  
using Google Gemini and LangGraph.
""")

st.sidebar.divider()
st.sidebar.header("Tech Stack")
st.sidebar.image("https://registry.npmmirror.com/@lobehub/icons-static-png/latest/files/light/gemini-brand-color.png", width=80)
st.sidebar.caption("Google Gemini Pro")
st.sidebar.image("https://python.langchain.com/img/favicon.ico", width=30)
st.sidebar.caption("LangGraph")
st.sidebar.image("https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png", width=80)
st.sidebar.caption("FastAPI")
st.sidebar.image("https://streamlit.io/images/brand/streamlit-mark-color.svg", width=30)
st.sidebar.caption("Streamlit")

st.sidebar.divider()
st.sidebar.header("Instructions")
st.sidebar.markdown("""
1. **Single Candidate**:
   - Upload one resume PDF
   - Paste job description
   - Click "Analyze Resume"

2. **Rank Candidates**:
   - Upload multiple resume PDFs
   - Paste job description
   - Click "Rank Candidates"
""")

if st.sidebar.button("Clear All Results"):
    st.session_state.results = None
    st.session_state.ranking_results = None
    st.session_state.form_submitted = False
    st.session_state.ranking_submitted = False
    st.rerun()