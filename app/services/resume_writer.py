from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings
from app.services.relevance_ranker import RelevanceRanker
from app.core.job_parser import JobParserService
from typing import Dict, Any, List, Optional
import json
from app.core.prompts import (
    SUMMARY_PROMPT,
    EXPERIENCE_PROMPT,
    SKILLS_PROMPT,
    RESEARCH_EXPERIENCE_PROMPT,
    PROJECTS_PROMPT,
    APPLIED_HIGHLIGHTS_PROMPT,
    TAILORED_SKILLS_PROMPT
)
from langchain.prompts import PromptTemplate
from app.services.project_store import ProjectStoreService
from langchain.chains import LLMChain

class ResumeWriterService:
    def __init__(self, project_store: ProjectStoreService):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
            
        self.llm = ChatOpenAI(
            model=settings.openai.model,
            temperature=settings.openai.temperature,
            api_key=settings.OPENAI_API_KEY
        )
        self.relevance_ranker = RelevanceRanker()
        self.job_parser = JobParserService()
        self.project_store = project_store

    async def generate_resume_section(self, section_type: str, job_description: str, projects: List[Dict[str, Any]], 
                                    candidate_skills: List[str] = None) -> str:
        """
        Generate a tailored resume section based on projects and job description.
        
        Args:
            section_type: Type of section ("experience", "projects", "skills", "summary")
            job_description: Job description
            projects: List of ranked projects
            candidate_skills: Optional list of candidate skills
            
        Returns:
            Generated resume section text
        """
        try:
            if section_type == "experience":
                return await self._generate_experience_section(job_description, projects)
            elif section_type == "projects":
                return await self._generate_projects_section(job_description, projects)
            elif section_type == "skills":
                return await self._generate_skills_section(projects, job_description)
            elif section_type == "summary":
                return await self._generate_summary_section(projects, job_description)
            else:
                raise ValueError(f"Unsupported section type: {section_type}")
                
        except Exception as e:
            raise ValueError(f"Error generating resume section: {str(e)}")

    async def _generate_experience_section(self, job_description: str, projects: List[Dict[str, Any]]) -> str:
        """Generate experience section with project-based bullet points."""
        try:
            # Parse job description
            job_data = await self.job_parser.parse_job_description(job_description)
            
            # Create project descriptions for the prompt
            project_descriptions = []
            for i, project in enumerate(projects[:5]):  # Top 5 projects
                desc = f"Project {i+1}: {project.get('title', '')}\n"
                desc += f"Role: {project.get('role', '')}\n"
                desc += f"Technologies: {', '.join(project.get('technologies', []))}\n"
                desc += f"Results: {project.get('results', '')}\n"
                desc += f"Impact: {project.get('impact', '')}\n"
                project_descriptions.append(desc)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert resume writer. Create a compelling experience section that:
                1. Highlights the most relevant projects for the job
                2. Uses strong action verbs and quantifiable results
                3. Emphasizes skills and technologies mentioned in the job description
                4. Follows professional resume formatting
                5. Each bullet point should be concise but impactful
                
                Format the output as a clean, professional experience section with proper bullet points."""),
                ("user", """Job Title: {job_title}
                Required Skills: {required_skills}
                Job Description: {job_description}
                
                Projects to highlight:
                {project_descriptions}
                
                Create a professional experience section that showcases these projects in the most relevant way for this job.""")
            ])
            
            chain = prompt | self.llm
            
            response = await chain.ainvoke({
                "job_title": job_data.get("job_title", ""),
                "required_skills": ", ".join(job_data.get("required_skills", [])),
                "job_description": job_description,
                "project_descriptions": "\n\n".join(project_descriptions)
            })
            
            return response.content
            
        except Exception as e:
            raise ValueError(f"Error generating experience section: {str(e)}")

    async def _generate_projects_section(self, job_description: str, projects: List[Dict[str, Any]]) -> str:
        """Generate projects section with detailed project descriptions."""
        try:
            # Parse job description
            job_data = await self.job_parser.parse_job_description(job_description)
            
            # Create detailed project descriptions
            project_details = []
            for i, project in enumerate(projects[:6]):  # Top 6 projects
                detail = f"Project {i+1}: {project.get('title', '')}\n"
                detail += f"Description: {project.get('description', '')}\n"
                detail += f"Role: {project.get('role', '')}\n"
                detail += f"Technologies: {', '.join(project.get('technologies', []))}\n"
                detail += f"Methods: {project.get('methods', '')}\n"
                detail += f"Results: {project.get('results', '')}\n"
                detail += f"Impact: {project.get('impact', '')}\n"
                detail += f"Duration: {project.get('duration', '')}\n"
                project_details.append(detail)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert resume writer. Create a compelling projects section that:
                1. Showcases the most relevant projects for the job
                2. Provides detailed but concise project descriptions
                3. Emphasizes technical skills and methodologies
                4. Highlights quantifiable results and impact
                5. Uses professional formatting with clear project titles and bullet points
                
                Format each project with a clear title and 3-4 bullet points highlighting key aspects."""),
                ("user", """Job Title: {job_title}
                Industry Focus: {industry_focus}
                Required Skills: {required_skills}
                
                Project Details:
                {project_details}
                
                Create a professional projects section that best showcases these projects for this role.""")
            ])
            
            chain = prompt | self.llm
            
            response = await chain.ainvoke({
                "job_title": job_data.get("job_title", ""),
                "industry_focus": job_data.get("industry_focus", ""),
                "required_skills": ", ".join(job_data.get("required_skills", [])),
                "project_details": "\n\n".join(project_details)
            })
            
            return response.content
            
        except Exception as e:
            raise ValueError(f"Error generating projects section: {str(e)}")

    async def _generate_skills_section(self, projects: List[Dict[str, Any]], 
                                     job_description: str) -> str:
        """Generate skills section based on project technologies and job requirements."""
        try:
            # Parse job description
            job_data = await self.job_parser.parse_job_description(job_description)
            
            # Extract skills from projects
            project_skills = set()
            for project in projects:
                technologies = project.get("technologies", [])
                project_skills.update(technologies)
            
            # Get job requirements
            required_skills = job_data.get("required_skills", [])
            preferred_skills = job_data.get("preferred_skills", [])
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert resume writer. Create a skills section that:
                1. Prioritizes skills that match the job requirements
                2. Groups skills logically (e.g., Programming Languages, Frameworks, Tools)
                3. Includes both required and preferred skills from the job
                4. Adds relevant skills from the candidate's projects
                5. Uses professional formatting with clear categories
                
                Format as a clean skills section with categorized skill groups."""),
                ("user", """Job Title: {job_title}
                Required Skills: {required_skills}
                Preferred Skills: {preferred_skills}
                Project Skills: {project_skills}
                
                Create a professional skills section that best matches the job requirements.""")
            ])
            
            chain = prompt | self.llm
            
            response = await chain.ainvoke({
                "job_title": job_data.get("job_title", ""),
                "required_skills": ", ".join(required_skills),
                "preferred_skills": ", ".join(preferred_skills),
                "project_skills": ", ".join(list(project_skills))
            })
            
            return response.content
            
        except Exception as e:
            raise ValueError(f"Error generating skills section: {str(e)}")

    async def _generate_summary_section(self, projects: List[Dict[str, Any]], 
                                      job_description: str) -> str:
        """Generate a professional summary based on projects and job requirements."""
        return "PhD in Computer Science with expertise in neural network optimization, GenAI pipelines, and embedded ML deployment. Seeking Applied Scientist roles focused on scalable ML systems, search ranking models, reinforcement learning, and real-world deployment on large-scale infrastructure."

    def generate_tailored_resume(self, job_description: str, include_sections: list[str]) -> dict:
        """
        Generates a complete tailored resume with specified sections.
        """
        projects_text = self.project_store.get_all_projects_as_text()
        master_skills_text = self.project_store.get_master_skills_as_text()

        generated_sections = {}
        for section in include_sections:
            generated_sections[section] = self._generate_section_content(
                section_type=section,
                job_description=job_description,
                projects=projects_text,
                master_skills=master_skills_text
            )
        
        return {"sections": generated_sections}

    def _generate_section_content(self, section_type: str, job_description: str, projects: str, master_skills: str) -> str:
        """
        Uses the appropriate prompt and LLMChain to generate section content.
        """
        if section_type == "summary":
            return "PhD in Computer Science with expertise in neural network optimization, GenAI pipelines, and embedded ML deployment. Seeking Applied Scientist roles focused on scalable ML systems, search ranking models, reinforcement learning, and real-world deployment on large-scale infrastructure."

        prompts = {
            "research_experience": RESEARCH_EXPERIENCE_PROMPT,
            "skills": TAILORED_SKILLS_PROMPT,
            "projects": PROJECTS_PROMPT,
        }
        
        prompt = prompts.get(section_type)
        if not prompt:
            raise ValueError(f"Invalid section type: {section_type}")

        input_data = { "job_description": job_description }
        if "projects" in prompt.input_variables:
            input_data["projects"] = projects
        if "master_skills" in prompt.input_variables:
            input_data["master_skills"] = master_skills

        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.invoke(input_data)
        
        return response.get("text", "").strip()

    async def optimize_existing_section(self, current_section: str, section_name: str,
                                      job_description: str) -> str:
        """
        Optimize an existing resume section for a job.
        
        Args:
            current_section: Current section content
            section_name: Name of the section
            job_description: Job description
            
        Returns:
            Optimized section content
        """
        try:
            # Parse job description
            job_data = await self.job_parser.parse_job_description(job_description)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert resume writer. Optimize the given resume section to:
                1. Better align with the job requirements
                2. Emphasize relevant skills and experiences
                3. Use stronger action verbs and quantifiable results
                4. Maintain professional formatting
                5. Keep the same structure but improve content relevance
                
                Return the optimized section while preserving the original format and structure."""),
                ("user", """Job Title: {job_title}
                Required Skills: {required_skills}
                Job Description: {job_description}
                
                Current {section_name} Section:
                {current_section}
                
                Optimize this section to better match the job requirements.""")
            ])
            
            chain = prompt | self.llm
            
            response = await chain.ainvoke({
                "job_title": job_data.get("job_title", ""),
                "required_skills": ", ".join(job_data.get("required_skills", [])),
                "job_description": job_description,
                "section_name": section_name,
                "current_section": current_section
            })
            
            return response.content
            
        except Exception as e:
            raise ValueError(f"Error optimizing section: {str(e)}")

    async def generate_cover_letter_intro(self, job_description: str, 
                                        candidate_skills: List[str] = None) -> str:
        """
        Generate a cover letter introduction paragraph.
        
        Args:
            job_description: Job description
            candidate_skills: Optional list of candidate skills
            
        Returns:
            Cover letter introduction
        """
        try:
            # Get project recommendations
            recommendations = await self.relevance_ranker.get_project_recommendations(
                job_description, candidate_skills
            )
            ranked_projects = recommendations["ranked_projects"]
            job_analysis = recommendations["job_analysis"]
            
            # Get top project highlights
            top_project = ranked_projects[0] if ranked_projects else None
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert cover letter writer. Create a compelling introduction paragraph that:
                1. Shows enthusiasm for the specific role and company
                2. Briefly mentions relevant experience and achievements
                3. Connects the candidate's background to the job requirements
                4. Uses professional but engaging language
                5. Is concise (2-3 sentences) but impactful
                
                Create an introduction that immediately captures attention and shows fit for the role."""),
                ("user", """Job Title: {job_title}
                Company: {company}
                Industry Focus: {industry_focus}
                Top Project: {top_project}
                Key Skills: {key_skills}
                
                Create a compelling cover letter introduction for this role.""")
            ])
            
            chain = prompt | self.llm
            
            response = await chain.ainvoke({
                "job_title": job_analysis.get("job_title", ""),
                "company": "the company",  # Could be extracted from job description
                "industry_focus": job_analysis.get("industry_focus", ""),
                "top_project": top_project.get("title", "") if top_project else "",
                "key_skills": ", ".join(candidate_skills[:5]) if candidate_skills else ""
            })
            
            return response.content
            
        except Exception as e:
            raise ValueError(f"Error generating cover letter intro: {str(e)}") 