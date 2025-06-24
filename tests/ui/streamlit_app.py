import streamlit as st
import requests
import sys
import os
import json
from datetime import datetime

# Add the scripts directory to the path so we can import from create_concise_resume.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

# Import the build_resume function from create_concise_resume.py
from create_concise_resume import build_resume

st.set_page_config(page_title="Resume Editor", page_icon="📝", layout="wide")

st.title("AI-Powered Resume Editor")
st.markdown("Generate tailored resumes using AI-powered project matching and analysis.")

# Create tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["📝 Resume Generator", "🎯 Project Matching", "➕ Project Management"])

with tab1:
    st.subheader("Resume Generator")
    st.markdown("Generate a tailored resume based on job description and your projects.")
    
    # Job description input
    job_description = st.text_area("Paste the job description here", height=200)
    
    # Section selection
    st.subheader("Select Resume Sections")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        include_summary = st.checkbox("Summary", value=True)
        include_skills = st.checkbox("Skills", value=True)
    
    with col2:
        include_research = st.checkbox("Research Experience", value=True)
        include_projects = st.checkbox("Projects", value=True)
    
    with col3:
        # Note: "experience" is not supported, using "research_experience" instead
        st.info("💡 Experience is included in Research Experience")
    
    if job_description:
        if st.button("🚀 Generate Tailored Resume", type="primary"):
            try:
                # Build sections list based on checkboxes
                include_sections = []
                if include_summary:
                    include_sections.append("summary")
                if include_skills:
                    include_sections.append("skills")
                if include_research:
                    include_sections.append("research_experience")
                if include_projects:
                    include_sections.append("projects")
                
                if not include_sections:
                    st.warning("Please select at least one section to generate.")
                    st.stop()
                
                # Generate tailored resume using the same approach as create_concise_resume.py
                response = requests.post(
                    "http://localhost:8000/api/generate-tailored-resume",
                    json={
                        "job_description": job_description,
                        "include_sections": include_sections
                    }
                )
                
                if response.status_code == 200:
                    generated_data = response.json()
                    
                    st.success("✅ Tailored resume generated successfully!")
                    
                    # Display generated sections
                    st.subheader("📄 Generated Resume Sections")
                    
                    for section_name, content in generated_data.get("sections", {}).items():
                        with st.expander(f"📝 {section_name.title()}"):
                            st.write(content)
                    
                    # Use the build_resume function from create_concise_resume.py
                    try:
                        output_file = build_resume(generated_data)
                        
                        # Read the generated file for download
                        with open(output_file, 'rb') as f:
                            doc_bytes = f.read()
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Professional Resume (DOCX)",
                            data=doc_bytes,
                            file_name=f"tailored_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                        
                        st.success(f"✅ Professional resume saved to: {output_file}")
                        
                    except Exception as e:
                        st.error(f"❌ Error creating formatted resume: {str(e)}")
                    
                    # Show project recommendations
                    st.subheader("🎯 Relevant Projects for This Job")
                    try:
                        project_response = requests.post(
                            "http://localhost:8000/api/project-recommendations",
                            json={"job_description": job_description}
                        )
                        
                        if project_response.status_code == 200:
                            recommendations = project_response.json()
                            
                            if "ranked_projects" in recommendations:
                                for i, project in enumerate(recommendations["ranked_projects"][:3], 1):
                                    with st.expander(f"#{i} {project.get('title', 'Untitled Project')} - Score: {project.get('relevance_score', 0):.2f}"):
                                        st.write(f"**Role:** {project.get('role', 'N/A')}")
                                        st.write(f"**Technologies:** {', '.join(project.get('technologies', []))}")
                                        st.write(f"**Impact:** {project.get('impact', 'N/A')}")
                                        st.write(f"**Results:** {project.get('results', 'N/A')}")
                        else:
                            st.info("Project recommendations not available.")
                            
                    except Exception as e:
                        st.info("Project recommendations not available.")
                        
                else:
                    st.error(f"❌ Error generating resume: {response.text}")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    else:
        st.info("Please provide a job description to get started.")

with tab2:
    st.subheader("Project Matching & Analysis")
    
    # Job description input
    job_desc = st.text_area("Paste the job description here", height=150, key="project_matching")
    
    if job_desc:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Find Matching Projects", type="primary"):
                try:
                    # Get project recommendations
                    response = requests.post(
                        "http://localhost:8000/api/project-recommendations",
                        json={"job_description": job_desc}
                    )
                    
                    if response.status_code == 200:
                        recommendations = response.json()
                        
                        st.success("✅ Found relevant projects!")
                        
                        # Display ranked projects
                        st.subheader("📊 Relevant Projects (Ranked)")
                        
                        if "ranked_projects" in recommendations:
                            for i, project in enumerate(recommendations["ranked_projects"][:5], 1):
                                with st.expander(f"#{i} {project.get('title', 'Untitled Project')} - Score: {project.get('relevance_score', 0):.2f}"):
                                    st.write(f"**Role:** {project.get('role', 'N/A')}")
                                    st.write(f"**Technologies:** {', '.join(project.get('technologies', []))}")
                                    st.write(f"**Impact:** {project.get('impact', 'N/A')}")
                                    st.write(f"**Results:** {project.get('results', 'N/A')}")
                        
                        # Store recommendations in session state for resume generation
                        st.session_state.recommendations = recommendations
                        
                    else:
                        st.error("❌ Error finding matching projects")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        with col2:
            if st.button("✍️ Generate Tailored Resume", type="secondary"):
                if hasattr(st.session_state, 'recommendations'):
                    try:
                        # Generate tailored resume
                        response = requests.post(
                            "http://localhost:8000/api/generate-tailored-resume",
                            json={
                                "job_description": job_desc,
                                "include_sections": ["summary", "research_experience", "skills"]
                            }
                        )
                        
                        if response.status_code == 200:
                            resume_data = response.json()
                            
                            st.success("✅ Tailored resume generated!")
                            
                            # Use build_resume function for professional formatting
                            try:
                                output_file = build_resume(resume_data)
                                
                                # Read the generated file for download
                                with open(output_file, 'rb') as f:
                                    doc_bytes = f.read()
                                
                                # Download button
                                st.download_button(
                                    label="📥 Download Professional Resume (DOCX)",
                                    data=doc_bytes,
                                    file_name=f"tailored_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
                                
                                st.success(f"✅ Professional resume saved to: {output_file}")
                                
                            except Exception as e:
                                st.error(f"❌ Error creating formatted resume: {str(e)}")
                        else:
                            st.error("❌ Error generating resume")
                            
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ Please find matching projects first!")

with tab3:
    st.subheader("Project Management")
    st.markdown("Add and manage your projects for better resume generation.")
    
    # Quick project addition
    st.subheader("➕ Add New Project")
    
    project_title = st.text_input("Project Title")
    project_dump = st.text_area("Project Description (paste your project details here)", height=150, 
                               placeholder="Describe your project including: technologies used, your role, results achieved, impact, duration, team size, challenges overcome, etc.")
    
    if project_title and project_dump:
        if st.button("💾 Save Project", type="primary"):
            try:
                response = requests.post(
                    "http://localhost:8000/api/project-dump",
                    json={
                        "dump_text": project_dump,
                        "project_title": project_title
                    }
                )
                
                if response.status_code == 200:
                    st.success(f"✅ Project '{project_title}' saved successfully!")
                    st.info("The project has been parsed and stored. It will now be available for resume generation and project matching.")
                    # Clear inputs
                    st.rerun()
                else:
                    st.error(f"❌ Error saving project: {response.text}")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # View existing projects
    st.subheader("📋 Your Projects")
    
    try:
        projects_response = requests.get("http://localhost:8000/api/projects")
        
        if projects_response.status_code == 200:
            projects_data = projects_response.json()
            projects = projects_data.get("projects", [])
            
            if projects:
                st.write(f"**Total Projects:** {len(projects)}")
                
                for i, project in enumerate(projects, 1):
                    with st.expander(f"#{i} {project.get('title', 'Untitled Project')}"):
                        st.write(f"**Role:** {project.get('role', 'N/A')}")
                        st.write(f"**Technologies:** {', '.join(project.get('technologies', []))}")
                        st.write(f"**Duration:** {project.get('duration', 'N/A')}")
                        st.write(f"**Team Size:** {project.get('team_size', 'N/A')}")
                        st.write(f"**Impact:** {project.get('impact', 'N/A')}")
                        st.write(f"**Results:** {project.get('results', 'N/A')}")
                        st.write(f"**Challenges:** {project.get('challenges', 'N/A')}")
            else:
                st.info("No projects found. Add your first project above!")
        else:
            st.error("❌ Error loading projects")
            
    except Exception as e:
        st.info("Project loading not available.")
    
    # Project statistics
    st.subheader("📊 Project Analytics")
    
    try:
        stats_response = requests.get("http://localhost:8000/api/projects/statistics")
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Projects", stats.get("total_projects", 0))
            
            with col2:
                st.metric("Technologies Used", stats.get("unique_technologies", 0))
            
            with col3:
                st.metric("Average Duration", f"{stats.get('avg_duration', 'N/A')}")
            
            # Technology breakdown
            if "technology_breakdown" in stats:
                st.subheader("🔧 Technology Usage")
                tech_data = stats["technology_breakdown"]
                
                for tech, count in tech_data.items():
                    st.write(f"**{tech}:** {count} projects")
        else:
            st.info("Project statistics not available.")
            
    except Exception as e:
        st.info("Project statistics not available.") 