from typing import Dict, List, Any
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from langchain.prompts import PromptTemplate
from app.core.prompts import ResumePrompts

class JobAnalysisService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai.model,
            temperature=settings.openai.temperature,
            api_key=settings.OPENAI_API_KEY
        )

    async def analyze_job_description(self, job_description: str) -> dict:
        """Analyze a job description and extract key information."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert job analyst. Extract key information from the job description and structure it in a clear format."),
            ("user", "Job Description: {job_description}\nPlease analyze and provide:\n1. Required Skills\n2. Responsibilities\n3. Qualifications\n4. Experience Level\n5. Industry\n6. Key Keywords")
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({"job_description": job_description})
        
        # Parse the response into structured format
        try:
            return json.loads(response.content)
        except:
            # If JSON parsing fails, return as text
            return {"analysis": response.content}

    async def calculate_skill_match(self, resume_skills: str, job_description: str) -> dict:
        """Calculate how well the resume skills match the job requirements."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at matching skills to job requirements. Analyze the match between resume skills and job requirements."),
            ("user", "Resume Skills: {resume_skills}\nJob Description: {job_description}\nPlease provide:\n1. Match percentage\n2. Matching skills\n3. Missing skills\n4. Additional skills")
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({
            "resume_skills": resume_skills,
            "job_description": job_description
        })

        try:
            return json.loads(response.content)
        except:
            return {"analysis": response.content}

    async def suggest_improvements(self, section_name: str, content: str, job_description: str) -> dict:
        """Suggest improvements to a resume section based on job description."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert resume writer. Suggest specific improvements to make the resume section more relevant to the job description."),
            ("user", "Section: {section_name}\nCurrent Content: {content}\nJob Description: {job_description}\nPlease provide:\n1. Key improvements\n2. Specific examples\n3. Action items")
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({
            "section_name": section_name,
            "content": content,
            "job_description": job_description
        })

        try:
            return json.loads(response.content)
        except:
            return {"suggestions": response.content}

    def extract_keywords(self, job_description: str) -> List[str]:
        """Extract key skills and requirements from the job description."""
        try:
            analysis = self.analyze_job_description(job_description)
            
            # Handle different response formats
            keywords = set()
            
            if isinstance(analysis, dict):
                # Extract from structured response
                if "required_skills" in analysis and isinstance(analysis["required_skills"], list):
                    keywords.update(analysis["required_skills"])
                if "industry_keywords" in analysis and isinstance(analysis["industry_keywords"], list):
                    keywords.update(analysis["industry_keywords"])
                if "required_qualifications" in analysis and isinstance(analysis["required_qualifications"], list):
                    keywords.update(analysis["required_qualifications"])
            else:
                # If analysis is not a dict, extract keywords from text
                import re
                # Simple keyword extraction from text
                common_skills = ["python", "pytorch", "tensorflow", "cuda", "gpu", "machine learning", 
                               "deep learning", "computer vision", "neural networks", "optimization",
                               "edge computing", "iot", "research", "docker", "onnx"]
                
                job_lower = job_description.lower()
                for skill in common_skills:
                    if skill in job_lower:
                        keywords.add(skill)
            
            return list(keywords)
        except Exception as e:
            # Fallback: extract basic keywords
            import re
            common_skills = ["python", "pytorch", "tensorflow", "cuda", "gpu", "machine learning", 
                           "deep learning", "computer vision", "neural networks", "optimization",
                           "edge computing", "iot", "research", "docker", "onnx"]
            
            keywords = set()
            job_lower = job_description.lower()
            for skill in common_skills:
                if skill in job_lower:
                    keywords.add(skill)
            
            return list(keywords)
    
    def suggest_improvements(self, resume_section: str, job_description: str) -> Dict[str, Any]:
        """Suggest improvements to a resume section based on job description."""
        analysis = self.analyze_job_description(job_description)
        
        prompt = f"""Analyze the following resume section and suggest improvements based on the job requirements:
        
        Resume Section:
        {resume_section}
        
        Job Requirements:
        {json.dumps(analysis, indent=2)}
        
        Please provide:
        1. Specific improvements to align with job requirements
        2. Missing keywords to include
        3. Suggested restructuring
        4. ATS optimization tips
        
        Format the response as a structured JSON."""
        
        response = self.llm.predict(prompt)
        suggestions = json.loads(response)
        
        return suggestions 