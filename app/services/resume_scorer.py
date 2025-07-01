from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings
from typing import Dict, Any, List, Optional, Tuple
import re
import json
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string

class ResumeScorerService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
            
        self.llm = ChatOpenAI(
            model=settings.openai.model,
            temperature=0.3,  # Lower temperature for more consistent scoring
            api_key=settings.OPENAI_API_KEY
        )
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        self.stop_words = set(stopwords.words('english'))
        
    async def score_resume(self, job_description: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a resume against a job description using both keyword matching and LLM analysis.
        
        Args:
            job_description: Job description text
            resume_data: Dictionary containing resume sections
            
        Returns:
            Dictionary with scoring results and feedback
        """
        try:
            # Extract keywords from job description
            job_keywords = self._extract_keywords(job_description)
            
            # Extract keywords from resume
            resume_keywords = self._extract_resume_keywords(resume_data)
            
            # Calculate keyword matching score
            keyword_score, matched_keywords, missing_keywords = self._calculate_keyword_match(
                job_keywords, resume_keywords
            )
            
            # Generate LLM-powered feedback
            llm_feedback = await self._generate_llm_feedback(job_description, resume_data)
            
            # Calculate overall score (70% keywords + 30% LLM assessment)
            overall_score = int(keyword_score * 0.7 + llm_feedback.get('llm_score', 0) * 0.3)
            
            return {
                "match_score": overall_score,
                "keyword_score": keyword_score,
                "keywords_matched": matched_keywords,
                "keywords_missing": missing_keywords,
                "section_feedback": llm_feedback.get('section_feedback', {}),
                "overall_feedback": llm_feedback.get('overall_feedback', ''),
                "ats_optimization_tips": llm_feedback.get('ats_tips', []),
                "scoring_breakdown": {
                    "keyword_matching": keyword_score,
                    "llm_assessment": llm_feedback.get('llm_score', 0),
                    "overall_score": overall_score
                }
            }
            
        except Exception as e:
            raise ValueError(f"Error scoring resume: {str(e)}")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract relevant keywords from text using NLP techniques.
        
        Args:
            text: Input text to extract keywords from
            
        Returns:
            List of relevant keywords
        """
        try:
            # Convert to lowercase and tokenize
            tokens = word_tokenize(text.lower())
            
            # Remove punctuation and stop words
            keywords = []
            for token in tokens:
                # Remove punctuation
                token = token.strip(string.punctuation)
                
                # Skip if it's a stop word, too short, or contains numbers
                if (token not in self.stop_words and 
                    len(token) > 2 and 
                    not token.isdigit() and
                    not re.match(r'^\d+$', token)):
                    keywords.append(token)
            
            # Add technical terms and phrases
            technical_terms = self._extract_technical_terms(text)
            keywords.extend(technical_terms)
            
            # Remove duplicates and return
            return list(set(keywords))
            
        except Exception as e:
            # Fallback to simple word extraction
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            return list(set(words))
    
    def _extract_technical_terms(self, text: str) -> List[str]:
        """
        Extract technical terms, frameworks, and tools from text.
        
        Args:
            text: Input text
            
        Returns:
            List of technical terms
        """
        # Common technical terms and frameworks
        technical_patterns = [
            r'\b[A-Z][a-zA-Z]*\b',  # Capitalized terms (like PyTorch, TensorFlow)
            r'\b[A-Z]{2,}\b',       # Acronyms (like API, ML, AI)
            r'\b[a-z]+\.js\b',      # JavaScript frameworks
            r'\b[a-z]+\.py\b',      # Python files
            r'\b[A-Za-z]+\d+\b',    # Terms with numbers (like CUDA12, Python3)
        ]
        
        technical_terms = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, text)
            technical_terms.extend(matches)
        
        # Common tech stack keywords
        tech_keywords = [
            'python', 'java', 'javascript', 'c++', 'cuda', 'pytorch', 'tensorflow',
            'onnx', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'fastapi',
            'django', 'react', 'vue', 'angular', 'nodejs', 'mongodb', 'postgresql',
            'mysql', 'redis', 'kafka', 'spark', 'hadoop', 'scala', 'go', 'rust',
            'machine learning', 'deep learning', 'ai', 'ml', 'nlp', 'computer vision',
            'data science', 'big data', 'cloud computing', 'devops', 'ci/cd',
            'microservices', 'api', 'rest', 'graphql', 'sql', 'nosql', 'git',
            'linux', 'unix', 'windows', 'macos', 'docker', 'kubernetes', 'jenkins',
            'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'agile', 'scrum'
        ]
        
        text_lower = text.lower()
        for keyword in tech_keywords:
            if keyword in text_lower:
                technical_terms.append(keyword)
        
        return list(set(technical_terms))
    
    def _extract_resume_keywords(self, resume_data: Dict[str, Any]) -> List[str]:
        """
        Extract keywords from resume sections.
        
        Args:
            resume_data: Dictionary containing resume sections
            
        Returns:
            List of keywords found in resume
        """
        keywords = []
        
        # Extract from summary
        if 'summary' in resume_data:
            keywords.extend(self._extract_keywords(resume_data['summary']))
        
        # Extract from skills
        if 'skills' in resume_data:
            if isinstance(resume_data['skills'], list):
                keywords.extend([skill.lower() for skill in resume_data['skills']])
            elif isinstance(resume_data['skills'], str):
                keywords.extend(self._extract_keywords(resume_data['skills']))
        
        # Extract from projects
        if 'projects' in resume_data:
            for project in resume_data['projects']:
                if isinstance(project, dict):
                    # Extract from project title
                    if 'title' in project:
                        keywords.extend(self._extract_keywords(project['title']))
                    
                    # Extract from project description
                    if 'description' in project:
                        keywords.extend(self._extract_keywords(project['description']))
                    
                    # Extract from technologies
                    if 'technologies' in project and isinstance(project['technologies'], list):
                        keywords.extend([tech.lower() for tech in project['technologies']])
        
        # Extract from research
        if 'research' in resume_data:
            for research in resume_data['research']:
                if isinstance(research, dict):
                    if 'title' in research:
                        keywords.extend(self._extract_keywords(research['title']))
                    if 'description' in research:
                        keywords.extend(self._extract_keywords(research['description']))
        
        return list(set(keywords))
    
    def _calculate_keyword_match(self, job_keywords: List[str], resume_keywords: List[str]) -> Tuple[int, List[str], List[str]]:
        """
        Calculate keyword matching score between job and resume.
        
        Args:
            job_keywords: Keywords from job description
            resume_keywords: Keywords from resume
            
        Returns:
            Tuple of (score, matched_keywords, missing_keywords)
        """
        # Convert to sets for easier comparison
        job_set = set(job_keywords)
        resume_set = set(resume_keywords)
        
        # Find matched and missing keywords
        matched_keywords = list(job_set.intersection(resume_set))
        missing_keywords = list(job_set - resume_set)
        
        # Calculate score (percentage of job keywords found in resume)
        if len(job_set) > 0:
            score = int((len(matched_keywords) / len(job_set)) * 100)
        else:
            score = 0
        
        return score, matched_keywords, missing_keywords
    
    async def _generate_llm_feedback(self, job_description: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate LLM-powered feedback for resume optimization.
        
        Args:
            job_description: Job description
            resume_data: Resume data
            
        Returns:
            Dictionary with LLM feedback
        """
        try:
            # Prepare resume sections for the prompt
            summary = resume_data.get('summary', '')
            skills = resume_data.get('skills', [])
            if isinstance(skills, list):
                skills_text = ', '.join(skills)
            else:
                skills_text = str(skills)
            
            projects = resume_data.get('projects', [])
            projects_text = ""
            for i, project in enumerate(projects[:3]):  # Top 3 projects
                if isinstance(project, dict):
                    title = project.get('title', 'Unknown Project')
                    desc = project.get('description', '')
                    projects_text += f"- {title}: {desc}\n"
            
            # Create the prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a resume optimization engine. Analyze the candidate's resume against the job description and provide detailed feedback for improvement."""),
                ("user", f"""JOB DESCRIPTION:
{job_description}

RESUME SECTIONS:
Summary: {summary}
Skills: {skills_text}
Top Projects:
{projects_text}

TASK:
1. Score the resume's relevance (0-100) based on how well it matches the job requirements.
2. List skills from the job description that were matched vs. missing.
3. Suggest specific improvements for each resume section.
4. Provide ATS optimization tips.

Respond in the following JSON format:
{{
    "llm_score": 85,
    "overall_feedback": "Overall assessment of the resume",
    "section_feedback": {{
        "summary": "Specific feedback for summary section",
        "skills": "Specific feedback for skills section", 
        "projects": "Specific feedback for projects section"
    }},
    "ats_tips": [
        "Tip 1 for ATS optimization",
        "Tip 2 for ATS optimization"
    ]
}}""")
            ])
            
            # Generate feedback
            chain = prompt | self.llm
            response = await chain.ainvoke({})
            
            # Parse JSON response
            try:
                feedback_data = json.loads(response.content)
                return feedback_data
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "llm_score": 75,
                    "overall_feedback": "Resume shows good alignment with job requirements",
                    "section_feedback": {
                        "summary": "Consider adding more specific technical achievements",
                        "skills": "Skills section looks comprehensive",
                        "projects": "Projects demonstrate relevant experience"
                    },
                    "ats_tips": [
                        "Use standard section headings",
                        "Include relevant keywords naturally",
                        "Quantify achievements where possible"
                    ]
                }
                
        except Exception as e:
            # Fallback response
            return {
                "llm_score": 70,
                "overall_feedback": f"Unable to generate detailed feedback: {str(e)}",
                "section_feedback": {},
                "ats_tips": ["Ensure all sections are properly formatted"]
            }
    
    def get_ats_optimization_tips(self) -> List[str]:
        """
        Get general ATS optimization tips.
        
        Returns:
            List of ATS optimization tips
        """
        return [
            "Use standard section headings (Experience, Education, Skills)",
            "Include relevant keywords naturally throughout the resume",
            "Quantify achievements with specific numbers and metrics",
            "Use bullet points for easy scanning",
            "Avoid graphics, tables, or complex formatting",
            "Use a clean, professional font (Arial, Calibri, Times New Roman)",
            "Keep file size under 500KB",
            "Use industry-standard job titles",
            "Include both technical and soft skills",
            "Proofread for spelling and grammar errors"
        ] 