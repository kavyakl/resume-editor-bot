from langchain.prompts import PromptTemplate
from typing import Dict

class ResumePrompts:
    @staticmethod
    def get_section_templates() -> Dict[str, PromptTemplate]:
        return {
            "summary": PromptTemplate(
                input_variables=["experience", "skills", "job_role", "industry"],
                template="""Create a compelling professional summary for a resume with the following details:
                
                Experience: {experience}
                Skills: {skills}
                Target Role: {job_role}
                Industry: {industry}
                
                Requirements:
                1. Start with a strong opening statement that captures attention
                2. Highlight 2-3 key achievements or unique value propositions
                3. Include relevant skills that match the target role
                4. Keep it concise (3-4 sentences)
                5. Use industry-specific terminology
                6. Focus on quantifiable achievements where possible
                
                Professional Summary:"""
            ),
            
            "experience": PromptTemplate(
                input_variables=["role", "company", "duration", "achievements", "job_description"],
                template="""Optimize the following work experience for a resume:
                
                Role: {role}
                Company: {company}
                Duration: {duration}
                Current Achievements: {achievements}
                Target Job Description: {job_description}
                
                Requirements:
                1. Create 3-4 bullet points using the STAR method (Situation, Task, Action, Result)
                2. Start each bullet with a strong action verb
                3. Include quantifiable metrics and achievements
                4. Align with the target job description's key requirements
                5. Use industry-specific keywords
                6. Focus on impact and results
                
                Optimized Experience Section:"""
            ),
            
            "skills": PromptTemplate(
                input_variables=["current_skills", "job_description", "industry"],
                template="""Analyze and optimize the skills section for a resume:
                
                Current Skills: {current_skills}
                Target Job Description: {job_description}
                Industry: {industry}
                
                Requirements:
                1. Categorize skills into Technical, Soft Skills, and Industry-specific
                2. Prioritize skills mentioned in the job description
                3. Add relevant industry certifications if applicable
                4. Include proficiency levels where appropriate
                5. Remove outdated or irrelevant skills
                6. Add missing critical skills from the job description
                
                Optimized Skills Section:"""
            ),
            
            "projects": PromptTemplate(
                input_variables=["project_details", "job_description", "role"],
                template="""Create an impactful projects section for a resume:
                
                Project Details: {project_details}
                Target Job Description: {job_description}
                Target Role: {role}
                
                Requirements:
                1. Structure each project with a clear title and duration
                2. Include 2-3 bullet points per project
                3. Highlight technical skills and tools used
                4. Emphasize problem-solving and innovation
                5. Link project outcomes to target role requirements
                6. Use metrics to quantify impact where possible
                
                Optimized Projects Section:"""
            ),
            
            "education": PromptTemplate(
                input_variables=["education_details", "job_description", "industry"],
                template="""Optimize the education section for a resume:
                
                Education Details: {education_details}
                Target Job Description: {job_description}
                Industry: {industry}
                
                Requirements:
                1. List degrees in reverse chronological order
                2. Include relevant coursework that matches job requirements
                3. Add academic achievements and honors
                4. Mention relevant certifications
                5. Include industry-specific training
                6. Highlight research or thesis work if applicable
                
                Optimized Education Section:"""
            )
        }
    
    @staticmethod
    def get_job_analysis_template() -> PromptTemplate:
        return PromptTemplate(
            input_variables=["job_description"],
            template="""Analyze the following job description and extract key information:
            
            Job Description: {job_description}
            
            Please provide:
            1. Required Skills (Technical and Soft Skills)
            2. Key Responsibilities
            3. Required Qualifications
            4. Preferred Qualifications
            5. Industry-specific Keywords
            6. Company Culture Indicators
            7. Growth Opportunities
            
            Format the response as a structured JSON with these categories."""
        )
    
    @staticmethod
    def get_bullet_point_optimizer() -> PromptTemplate:
        return PromptTemplate(
            input_variables=["bullet_point", "job_description", "section_type"],
            template="""Optimize the following resume bullet point for ATS compatibility and impact:
            
            Original Bullet Point: {bullet_point}
            Target Job Description: {job_description}
            Section Type: {section_type}
            
            Requirements:
            1. Start with a strong action verb
            2. Include quantifiable metrics
            3. Highlight specific skills from the job description
            4. Focus on achievements and impact
            5. Use industry-specific terminology
            6. Keep it concise and clear
            7. Ensure ATS compatibility
            
            Optimized Bullet Point:"""
        )

PROJECT_PARSER_PROMPT = """
Parse the following project description into a structured YAML format.

Project Title: {project_title}
Project Description:
{dump_text}

YAML Structure:
- title: (string)
- description: (string, a concise one-sentence summary)
- role: (string, e.g., "Lead Developer," "Data Scientist")
- technologies: (list of strings)
- methods: (string, brief description of methodologies used)
- results: (string, key outcomes and achievements)
- impact: (string, the overall impact of the project)
- duration: (string, e.g., "3 months," "2022-2023")
- team_size: (integer or string)
- challenges: (string, main obstacles overcome)

Guidelines:
1. Extract the most relevant information for each field.
2. Be concise and professional.
3. If a field is not mentioned, leave it blank or use a sensible default.
4. The 'technologies' list should only contain technical skills, tools, or frameworks.

Respond ONLY with the structured YAML content.

YAML Output:
"""

# Prompts for Resume Generation
SUMMARY_PROMPT_TEMPLATE = """
Based on the following projects and skills, write a compelling professional summary for a resume targeting a job that requires: {job_description}.

Relevant Projects:
{projects}

Candidate's Core Skills:
{candidate_skills}

Instructions:
- Start with a strong opening statement.
- Weave in 2-3 key achievements from the projects.
- Keep it concise and impactful (3-4 sentences).
- Align directly with the target job requirements.
"""

EXPERIENCE_PROMPT_TEMPLATE = """
Generate 4-5 professional, achievement-oriented bullet points for a "Research Experience & Highlights" section of a resume. The candidate is a PhD Researcher targeting a job that requires: {job_description}.

Use the following projects as the primary source of experience:
{projects}

Instructions:
- Start each bullet point with a strong action verb (e.g., "Engineered," "Architected," "Accelerated").
- Quantify results wherever possible (e.g., "reduced model size by 80%," "achieved 3-5x speedup").
- Focus on the impact and outcomes of the work.
- Directly address skills and requirements mentioned in the job description.
- Do not invent new information; base the highlights strictly on the provided project details.
"""

SKILLS_PROMPT_TEMPLATE = """
Based on the following projects and the candidate's existing skills, create an optimized "Technical Skills" section for a resume. The target job requires: {job_description}.

Candidate's Projects:
{projects}

Candidate's Known Skills:
{candidate_skills}

Instructions:
1.  Create skill categories (e.g., "Programming Languages," "ML/AI Frameworks," "GenAI & Model Optimization").
2.  Prioritize skills that are clearly demonstrated in the projects and mentioned in the job description.
3.  Integrate skills from the projects into the appropriate categories.
4.  Format the output cleanly for a resume.
"""

SUMMARY_PROMPT = PromptTemplate(template=SUMMARY_PROMPT_TEMPLATE, input_variables=["job_description", "projects", "candidate_skills"])
EXPERIENCE_PROMPT = PromptTemplate(template=EXPERIENCE_PROMPT_TEMPLATE, input_variables=["job_description", "projects"])
SKILLS_PROMPT = PromptTemplate(template=SKILLS_PROMPT_TEMPLATE, input_variables=["job_description", "projects", "candidate_skills"])

# =================================================================================================
# RESUME WRITER PROMPTS (FINAL INDUSTRY-FOCUSED VERSION)
# =================================================================================================

RESEARCH_EXPERIENCE_PROMPT = PromptTemplate(
    input_variables=["projects", "job_description"],
    template="""
As an expert resume writer, generate an impactful "Research Experience" section for a PhD candidate targeting an "{job_description}" role.
Synthesize the following projects into 4-5 achievement-oriented bullet points.

**Candidate Projects:**
{projects}

**Instructions:**
1.  For each bullet point, start with a bolded project title followed by a colon. Use markdown for bolding (e.g., **Project Title**).
2.  After the colon, write a concise, powerful description of the project's impact.
3.  Begin the description with a strong action verb (e.g., Built, Designed, Achieved, Created, Developed).
4.  Integrate quantifiable metrics and specific technologies from the projects (e.g., 19.23 FPS, 80% compression, PYNQ Z1, PyTorch, ONNX).
5.  Do not invent information. Base the output strictly on the provided project details.

**Example of Final Output Format:**
- **Distributed Object Detection on IoT Nodes**: Built a scalable framework for real-time object detection using PYNQ Z1 AP-SoCs; achieved 19.23 FPS across 3 nodes, enabling robust edge deployment.
- **LitBot — GenAI Literature Assistant**: Created an OpenAI-based literature analysis tool with FAISS search and semantic summarization, adopted by 10+ researchers.

Generate the "Research Experience" bullet points now.
"""
)

APPLIED_HIGHLIGHTS_PROMPT = PromptTemplate(
    input_variables=["projects", "job_description"],
    template="""
As an expert resume writer, generate an "Applied Highlights" section for a PhD candidate targeting an "{job_description}" role.
This section should showcase key, tangible projects.

The candidate's projects are:
{projects}

Instructions:
1.  Select the 3-4 most impactful projects relevant to the job description.
2.  For each project, create a single bullet point in the format: "Project Title: Brief, impactful description."
3.  The description should highlight the core technology, method, and result.
4.  Incorporate keywords like: GenAI, LLM, RAG, full-stack, model optimization, deployment, performance profiling.

Example of a strong bullet point:
"LLM-Enhanced Literature Analysis: Created a full-stack summarization pipeline using RAG with FAISS and OpenAI GPT, improving retrieval relevance and automating survey generation."

Generate the "Applied Highlights" bullet points now.
"""
)

TAILORED_SKILLS_PROMPT = PromptTemplate(
    input_variables=["job_description", "master_skills"],
    template="""
As an expert technical recruiter, your task is to create a tailored "Technical Skills" section for a resume.
The target role is: "{job_description}"
The candidate's master list of all skills is:
{master_skills}

Instructions:
1.  Analyze the job description to identify the most critical skills and technologies required.
2.  From the master skills list, select only the most relevant skills.
3.  Organize these selected skills into the following categories:
    - Programming Languages
    - AI/ML Frameworks
    - GenAI & NLP
    - Model Optimization
    - Embedded & Edge Deployment
    - Hardware & EDA Tools
    - Cloud & Infrastructure
    - DevOps & Workflow
4.  If a category has no relevant skills for the job, omit the category entirely.
5.  Format the output strictly as "Category Name: Skill 1, Skill 2, Skill 3". Do not add extra text or explanations.

Example Output:
AI/ML Frameworks: PyTorch, TensorFlow, ONNX
GenAI & NLP: RAG, FAISS, OpenAI GPT
"""
) 