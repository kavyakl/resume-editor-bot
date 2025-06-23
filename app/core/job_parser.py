from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings
import json
from typing import Dict, Any, List
import re
from langchain.prompts import PromptTemplate

class JobParserService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
            
        self.llm = ChatOpenAI(
            model=settings.openai.model,
            temperature=settings.openai.temperature,
            api_key=settings.OPENAI_API_KEY
        )

    async def parse_job_description(self, job_description: str) -> Dict[str, Any]:
        """
        Parse job description to extract structured information.
        
        Args:
            job_description: Raw job description text
            
        Returns:
            Structured job information dictionary
        """
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at parsing job descriptions. Extract the following information:

                - job_title: The job title/position
                - company: Company name (if mentioned)
                - required_skills: List of required technical skills
                - preferred_skills: List of preferred/nice-to-have skills
                - tools_technologies: Specific tools, frameworks, or technologies mentioned
                - responsibilities: Key responsibilities and duties
                - qualifications: Required qualifications (education, experience)
                - industry_focus: Industry or domain focus (e.g., "AI/ML", "Web Development", "Research")
                - experience_level: Entry, Mid, Senior, Lead, etc.
                - location: Job location (if mentioned)
                - salary_range: Salary information (if mentioned)
                - keywords: Important keywords for matching
                
                Return ONLY a valid JSON object with these fields. Use null for missing information."""),
                ("user", "Job Description: {job_description}")
            ])
            
            chain = prompt | self.llm
            
            response = await chain.ainvoke({
                "job_description": job_description
            })
            
            # Parse the JSON response
            try:
                job_data = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from the response
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    job_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse structured data from response")
            
            # Clean and validate the data
            job_data = self._clean_job_data(job_data)
            
            return job_data
            
        except Exception as e:
            raise ValueError(f"Error parsing job description: {str(e)}")

    def _clean_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and validate job data.
        
        Args:
            job_data: Raw job data from GPT
            
        Returns:
            Cleaned job data
        """
        try:
            # Ensure required fields exist
            required_fields = ['job_title', 'required_skills', 'preferred_skills', 'tools_technologies']
            
            for field in required_fields:
                if field not in job_data:
                    job_data[field] = []
                elif isinstance(job_data[field], str):
                    # Convert string to list if needed
                    job_data[field] = [skill.strip() for skill in job_data[field].split(',') if skill.strip()]
            
            # Ensure lists are actually lists
            list_fields = ['required_skills', 'preferred_skills', 'tools_technologies', 'keywords']
            for field in list_fields:
                if not isinstance(job_data.get(field), list):
                    job_data[field] = []
            
            # Clean up skills lists
            for field in ['required_skills', 'preferred_skills']:
                if job_data[field]:
                    # Remove duplicates and clean up
                    cleaned_skills = []
                    for skill in job_data[field]:
                        if isinstance(skill, str):
                            skill = skill.strip()
                            if skill and skill not in cleaned_skills:
                                cleaned_skills.append(skill)
                    job_data[field] = cleaned_skills
            
            # Generate keywords if not provided
            if not job_data.get('keywords'):
                keywords = []
                keywords.extend(job_data.get('required_skills', []))
                keywords.extend(job_data.get('preferred_skills', []))
                keywords.extend(job_data.get('tools_technologies', []))
                if job_data.get('industry_focus'):
                    keywords.append(job_data['industry_focus'])
                job_data['keywords'] = list(set(keywords))
            
            return job_data
            
        except Exception as e:
            raise ValueError(f"Error cleaning job data: {str(e)}")

    async def extract_skills_from_jd(self, job_description: str) -> List[str]:
        """
        Extract just the skills from a job description.
        
        Args:
            job_description: Raw job description
            
        Returns:
            List of skills
        """
        try:
            job_data = await self.parse_job_description(job_description)
            all_skills = []
            all_skills.extend(job_data.get('required_skills', []))
            all_skills.extend(job_data.get('preferred_skills', []))
            all_skills.extend(job_data.get('tools_technologies', []))
            
            # Remove duplicates
            return list(set(all_skills))
            
        except Exception as e:
            raise ValueError(f"Error extracting skills: {str(e)}")

    async def get_job_keywords(self, job_description: str) -> List[str]:
        """
        Extract keywords for matching from job description.
        
        Args:
            job_description: Raw job description
            
        Returns:
            List of keywords
        """
        try:
            job_data = await self.parse_job_description(job_description)
            return job_data.get('keywords', [])
            
        except Exception as e:
            raise ValueError(f"Error extracting keywords: {str(e)}")

    async def analyze_job_focus(self, job_description: str) -> Dict[str, Any]:
        """
        Analyze the focus and requirements of a job.
        
        Args:
            job_description: Raw job description
            
        Returns:
            Analysis of job focus
        """
        try:
            job_data = await self.parse_job_description(job_description)
            
            # Analyze the focus
            analysis = {
                'job_title': job_data.get('job_title', ''),
                'industry_focus': job_data.get('industry_focus', ''),
                'experience_level': job_data.get('experience_level', ''),
                'required_skills_count': len(job_data.get('required_skills', [])),
                'preferred_skills_count': len(job_data.get('preferred_skills', [])),
                'tools_count': len(job_data.get('tools_technologies', [])),
                'total_skills': len(job_data.get('required_skills', []) + job_data.get('preferred_skills', [])),
                'is_technical': self._is_technical_role(job_data),
                'is_research': self._is_research_role(job_data),
                'is_leadership': self._is_leadership_role(job_data)
            }
            
            return analysis
            
        except Exception as e:
            raise ValueError(f"Error analyzing job focus: {str(e)}")

    def _is_technical_role(self, job_data: Dict[str, Any]) -> bool:
        """Check if this is a technical role."""
        technical_keywords = [
            'engineer', 'developer', 'programmer', 'scientist', 'analyst',
            'architect', 'specialist', 'technician', 'developer', 'coder'
        ]
        
        job_title = job_data.get('job_title', '')
        if isinstance(job_title, list):
            job_title = ' '.join(job_title)
        job_title = job_title.lower()
        return any(keyword in job_title for keyword in technical_keywords)

    def _is_research_role(self, job_data: Dict[str, Any]) -> bool:
        """Check if this is a research role."""
        research_keywords = [
            'research', 'scientist', 'phd', 'academic', 'postdoc',
            'investigator', 'fellow', 'scholar'
        ]
        
        job_title = job_data.get('job_title', '')
        if isinstance(job_title, list):
            job_title = ' '.join(job_title)
        job_title = job_title.lower()
        return any(keyword in job_title for keyword in research_keywords)

    def _is_leadership_role(self, job_data: Dict[str, Any]) -> bool:
        """Check if this is a leadership role."""
        leadership_keywords = [
            'lead', 'senior', 'principal', 'manager', 'director',
            'head', 'chief', 'vp', 'cto', 'architect'
        ]
        
        job_title = job_data.get('job_title', '')
        if isinstance(job_title, list):
            job_title = ' '.join(job_title)
        job_title = job_title.lower()
        return any(keyword in job_title for keyword in leadership_keywords)

    async def compare_job_requirements(self, job_description: str, candidate_skills: List[str]) -> Dict[str, Any]:
        """
        Compare job requirements with candidate skills.
        
        Args:
            job_description: Job description
            candidate_skills: List of candidate skills
            
        Returns:
            Comparison analysis
        """
        try:
            job_data = await self.parse_job_description(job_description)
            
            required_skills = job_data.get('required_skills', [])
            preferred_skills = job_data.get('preferred_skills', [])
            
            # Convert to lowercase for comparison
            candidate_skills_lower = [skill.lower() for skill in candidate_skills]
            required_skills_lower = [skill.lower() for skill in required_skills]
            preferred_skills_lower = [skill.lower() for skill in preferred_skills]
            
            # Find matches
            required_matches = [skill for skill in required_skills if skill.lower() in candidate_skills_lower]
            preferred_matches = [skill for skill in preferred_skills if skill.lower() in candidate_skills_lower]
            
            # Calculate scores
            required_match_rate = len(required_matches) / len(required_skills) if required_skills else 0
            preferred_match_rate = len(preferred_matches) / len(preferred_skills) if preferred_skills else 0
            
            # Find missing skills
            missing_required = [skill for skill in required_skills if skill.lower() not in candidate_skills_lower]
            missing_preferred = [skill for skill in preferred_skills if skill.lower() not in candidate_skills_lower]
            
            return {
                'required_skills_match_rate': required_match_rate,
                'preferred_skills_match_rate': preferred_match_rate,
                'overall_match_rate': (required_match_rate + preferred_match_rate) / 2,
                'required_matches': required_matches,
                'preferred_matches': preferred_matches,
                'missing_required_skills': missing_required,
                'missing_preferred_skills': missing_preferred,
                'total_required_skills': len(required_skills),
                'total_preferred_skills': len(preferred_skills),
                'matched_required_count': len(required_matches),
                'matched_preferred_count': len(preferred_matches)
            }
            
        except Exception as e:
            raise ValueError(f"Error comparing requirements: {str(e)}") 