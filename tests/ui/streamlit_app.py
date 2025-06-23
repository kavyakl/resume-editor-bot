import streamlit as st
import requests
import docx
import io
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import json

st.set_page_config(page_title="Resume Editor", page_icon="📝", layout="wide")

st.title("AI-Powered Resume Editor")
st.markdown("Use your existing resume to get AI-powered suggestions for improvement.")

# Text area for job description
job_description = st.text_area("Paste the job description here", height=200)

if job_description:
    if st.button("Analyze Resume"):
        try:
            # Use existing resume
            response = requests.post("http://localhost:8000/api/use-existing-resume")
            
            if response.status_code == 200:
                parsed_resume = response.json()["parsed_data"]
                
                # Analyze the job description
                job_analysis = requests.post(
                    "http://localhost:8000/api/analyze-job",
                    json={"job_description": job_description}
                ).json()
                
                # Calculate skill match
                skill_match = requests.post(
                    "http://localhost:8000/api/calculate-skill-match",
                    json={
                        "resume_data": {
                            "sections": {
                                "skills": parsed_resume["sections"].get("skills", "")
                            }
                        },
                        "job_description": job_description
                    }
                ).json()
                
                # Display results
                st.subheader("Job Analysis")
                st.write(job_analysis)
                
                st.subheader("Skill Match Analysis")
                st.write(skill_match)
                
                # Get suggestions for each section
                st.subheader("Section Improvements")
                for section_name, content in parsed_resume["sections"].items():
                    with st.expander(f"Improve {section_name}"):
                        # Convert content to string if it's a list or dict
                        if isinstance(content, (list, dict)):
                            content_str = json.dumps(content, indent=2)
                        else:
                            content_str = str(content)
                            
                        try:
                            suggestions = requests.post(
                                "http://localhost:8000/api/suggest-improvements",
                                json={
                                    "section": {
                                        "section_name": section_name,
                                        "content": content_str
                                    },
                                    "job_description": job_description
                                }
                            ).json()
                            st.write(suggestions)
                        except Exception as e:
                            st.error(f"Error getting suggestions for {section_name}: {str(e)}")
                
                # Create improved resume
                improved_doc = docx.Document()
                improved_doc.add_heading("Improved Resume", 0)
                
                # Add improved content
                for section_name, content in parsed_resume["sections"].items():
                    improved_doc.add_heading(section_name.title(), level=1)
                    if isinstance(content, (list, dict)):
                        content_str = json.dumps(content, indent=2)
                    else:
                        content_str = str(content)
                    improved_doc.add_paragraph(content_str)
                
                # Save to bytes
                docx_bytes = io.BytesIO()
                improved_doc.save(docx_bytes)
                docx_bytes.seek(0)
                
                # Download button
                st.download_button(
                    label="Download Improved Resume",
                    data=docx_bytes,
                    file_name="improved_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            else:
                st.error(f"Error processing resume: {response.json().get('detail', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
else:
    st.info("Please provide a job description to get started.") 