# screening/ui/app.py

import streamlit as st
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import screen_candidates
from config import RESUME_DIR
from services.json_loader import get_resume_count


def main():
    st.set_page_config(
        page_title="Resume Screening System",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Resume Screening System")
    st.markdown("---")
    
    # Sidebar info
    with st.sidebar:
        st.header("System Info")
        resume_count = get_resume_count(RESUME_DIR)
        st.metric("Parsed Resumes", resume_count)
        st.info(f"Resume directory: `{RESUME_DIR}`")
        
        st.markdown("---")
        st.subheader("Scoring Weights")
        st.write("🔧 Technical: 40%")
        st.write("💼 Career: 35%")
        st.write("🤝 Fit: 25%")
    
    # Main content
    st.subheader("Job Description")
    st.write("Paste the job description below to screen candidates:")
    
    jd_text = st.text_area(
        label="Job Description",
        height=300,
        placeholder="""Example:
We are looking for a Python Developer with 2+ years of experience.

Required Skills:
- Python programming
- Web development (Django/Flask)
- Git version control
- Database knowledge (SQL)

Nice to have:
- JavaScript/React
- Docker/AWS
- Machine Learning basics

The ideal candidate should have strong problem-solving skills and team collaboration experience.""",
        label_visibility="collapsed"
    )
    
    # Check if resumes are available
    if resume_count == 0:
        st.error(f"⚠️ No resume JSONs found in `{RESUME_DIR}`. Please parse resumes first.")
        st.stop()
    
    # Screening button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        screen_button = st.button("🚀 Screen Candidates", use_container_width=True)
    
    if screen_button:
        if not jd_text.strip():
            st.error("⚠️ Please provide a job description")
        else:
            # Run screening
            with st.spinner("🔍 Analyzing candidates... This may take a moment."):
                try:
                    results, screening_time = asyncio.run(screen_candidates(jd_text))
                    
                    # Display results
                    st.markdown("---")
                    st.success(f"✅ Screening completed in {screening_time:.1f} seconds")
                    
                    st.subheader("📊 Screening Results")
                    
                    # Results table
                    for rank, candidate in enumerate(results, 1):
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"### {rank}. {candidate['name']}")
                                st.write(f"📧 {candidate['email']}")
                                st.write(f"📱 {candidate['phone']}")
                            
                            with col2:
                                score = candidate['total_score']
                                st.metric("Score", f"{score:.1f}/100")
                            
                            # Expandable details
                            with st.expander("View Details"):
                                breakdown = candidate['breakdown']
                                
                                col_a, col_b, col_c = st.columns(3)
                                
                                with col_a:
                                    st.markdown("**🔧 Technical**")
                                    tech_score = breakdown['technical']['score']
                                    st.progress(tech_score / 100)
                                    st.write(f"Score: {tech_score:.1f}")
                                    st.caption(breakdown['technical'].get('reasoning', 'N/A'))
                                
                                with col_b:
                                    st.markdown("**💼 Career**")
                                    career_score = breakdown['career']['score']
                                    st.progress(career_score / 100)
                                    st.write(f"Score: {career_score:.1f}")
                                    st.caption(breakdown['career'].get('reasoning', 'N/A'))
                                
                                with col_c:
                                    st.markdown("**🤝 Fit**")
                                    fit_score = breakdown['fit']['score']
                                    st.progress(fit_score / 100)
                                    st.write(f"Score: {fit_score:.1f}")
                                    st.caption(breakdown['fit'].get('reasoning', 'N/A'))
                            
                            st.markdown("---")
                
                except Exception as e:
                    st.error(f"❌ Error during screening: {str(e)}")
                    st.exception(e)


if __name__ == "__main__":
    main()