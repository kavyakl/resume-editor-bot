from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings
from app.services.relevance_ranker import RelevanceRanker
from app.core.job_parser import JobParserService
from typing import Dict, Any, List, Optional, Set
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

    def select_relevant_projects(self, projects: List[Dict[str, Any]], job_tags: List[str], 
                               target_section: str, used_project_slugs: Set[str], 
                               max_count: int = 5) -> List[Dict[str, Any]]:
        """
        Select relevant projects for a specific section with deduplication.
        
        Args:
            projects: List of all available projects
            job_tags: Tags extracted from job description
            target_section: Target section ("research", "project", "experience")
            used_project_slugs: Set of project slugs already used in other sections
            max_count: Maximum number of projects to return
            
        Returns:
            List of selected projects for the section
        """
        try:
            print(f"[DEBUG] select_relevant_projects called for section: {target_section}")
            print(f"[DEBUG] job_tags: {job_tags}")
            print(f"[DEBUG] total projects available: {len(projects)}")
            print(f"[DEBUG] used_project_slugs: {used_project_slugs}")
            
            # Filter projects by relevance tags and section compatibility
            filtered_projects = []
            for project in projects:
                # Skip if already used in another section
                if project.get('slug') in used_project_slugs:
                    print(f"[DEBUG] Skipping {project.get('title')} - already used")
                    continue
                
                # Check if project is compatible with target section
                project_sections = project.get('sections', [])
                if target_section not in project_sections:
                    print(f"[DEBUG] Skipping {project.get('title')} - not compatible with section {target_section} (has: {project_sections})")
                    continue
                
                # Check relevance tags overlap
                project_tags = project.get('relevance_tags', [])
                if not set(project_tags).intersection(set(job_tags)):
                    print(f"[DEBUG] Skipping {project.get('title')} - no tag overlap (project tags: {project_tags}, job tags: {job_tags})")
                    continue
                
                print(f"[DEBUG] Including {project.get('title')} - matches criteria")
                filtered_projects.append(project)
            
            print(f"[DEBUG] filtered_projects count: {len(filtered_projects)}")
            
            # Sort by featured status first, then by relevance
            featured_projects = [p for p in filtered_projects if p.get('featured', False)]
            other_projects = [p for p in filtered_projects if not p.get('featured', False)]
            
            # Combine featured and other projects, prioritizing featured ones
            ranked_projects = featured_projects + other_projects
            
            # Return top projects up to max_count
            selected_projects = ranked_projects[:max_count]
            
            print(f"[DEBUG] selected_projects count: {len(selected_projects)}")
            for project in selected_projects:
                print(f"[DEBUG] Selected: {project.get('title')}")
            
            # Update used project slugs
            for project in selected_projects:
                used_project_slugs.add(project.get('slug'))
            
            return selected_projects
            
        except Exception as e:
            raise ValueError(f"Error selecting relevant projects: {str(e)}")

    async def generate_tailored_resume_with_deduplication(self, job_description: str, 
                                                        include_sections: List[str],
                                                        candidate_skills: List[str] = None,
                                                        max_projects_per_section: int = 4) -> Dict[str, Any]:
        """
        Generate a tailored resume with intelligent project deduplication.
        
        Args:
            job_description: Job description text
            include_sections: List of sections to include
            candidate_skills: Optional list of candidate skills
            
        Returns:
            Dictionary containing generated resume sections
        """
        print("[DEBUG] Starting resume generation (deduplication)...")
        try:
            # Parse job description once and cache the result
            job_data = await self.job_parser.parse_job_description(job_description)
            print("[DEBUG] job_data returned:", job_data)
            if job_data is None:
                print("[ERROR] job_data is None! Check job description parsing.")
                job_data = {}
            job_tags = []
            
            # Extract tags from required and preferred skills
            for skill in job_data.get("required_skills", []):
                job_tags.extend(self._extract_tags_from_skill(skill))
            for skill in job_data.get("preferred_skills", []):
                job_tags.extend(self._extract_tags_from_skill(skill))
            
            # Add industry-specific tags
            industry_focus = (job_data.get("industry_focus") or "").lower()
            if "ml" in industry_focus or "machine learning" in industry_focus:
                job_tags.extend(["ml", "ai", "deep-learning"])
            if "edge" in industry_focus or "embedded" in industry_focus:
                job_tags.extend(["edge-ai", "embedded", "iot"])
            if "computer vision" in industry_focus:
                job_tags.extend(["computer-vision", "image-processing"])
            if "nlp" in industry_focus or "natural language" in industry_focus:
                job_tags.extend(["nlp", "text-processing"])
            
            # Remove duplicates and normalize
            job_tags = list(set([tag.lower() for tag in job_tags]))
            
            # Get all projects
            all_projects = self.project_store.get_all_projects()
            
            # Track used project slugs to avoid duplication
            used_project_slugs = set()
            
            # Generate sections with deduplication - use cached job_data
            resume_sections = {}
            
            for section in include_sections:
                if section == "summary":
                    # Summary doesn't need specific projects
                    resume_sections["summary"] = await self._generate_summary_section_optimized(all_projects, job_description, job_data)
                elif section == "research":
                    # Select research projects
                    research_projects = self.select_relevant_projects(
                        all_projects, job_tags, "research", used_project_slugs, max_count=max_projects_per_section
                    )
                    resume_sections["research"] = await self._generate_research_section_optimized(job_description, research_projects, job_data)
                elif section == "projects":
                    # Select project section projects (allow some overlap with research for comprehensive coverage)
                    project_projects = self.select_relevant_projects(
                        all_projects, job_tags, "project", set(), max_count=max_projects_per_section * 2  # Allow more projects
                    )
                    resume_sections["projects"] = await self._generate_projects_section_optimized(job_description, project_projects, job_data)
                elif section == "experience":
                    # Experience can use any projects not yet used
                    experience_projects = self.select_relevant_projects(
                        all_projects, job_tags, "project", used_project_slugs, max_count=max_projects_per_section
                    )
                    resume_sections["experience"] = await self._generate_experience_section_optimized(job_description, experience_projects, job_data)
                elif section == "skills":
                    # Skills section doesn't need specific projects
                    print(f"[DEBUG] Generating skills section with {len(all_projects)} projects")
                    skills_section = await self._generate_skills_section_optimized(all_projects, job_description, job_data)
                    print(f"[DEBUG] Skills section generated: {skills_section[:200]}...")  # Show first 200 chars
                    resume_sections["skills"] = skills_section
            
            print("[DEBUG] Resume generation succeeded!")
            return {
                "sections": resume_sections,
                "job_analysis": job_data,
                "selected_projects_count": len(used_project_slugs),
                "deduplication_applied": True
            }
            
        except Exception as e:
            import traceback
            print("[ERROR] Resume generation failed:", str(e))
            print(traceback.format_exc())
            raise

    def _extract_tags_from_skill(self, skill: str) -> List[str]:
        """Extract relevant tags from a skill string."""
        skill_lower = skill.lower()
        tags = []
        
        # Map common skills to tags
        skill_to_tags = {
            "python": ["python", "programming"],
            "pytorch": ["pytorch", "ml", "deep-learning"],
            "tensorflow": ["tensorflow", "ml", "deep-learning"],
            "onnx": ["onnx", "ml", "optimization"],
            "cuda": ["cuda", "gpu", "parallel-computing"],
            "docker": ["docker", "containerization"],
            "fastapi": ["fastapi", "web-app", "api"],
            "streamlit": ["streamlit", "web-app", "ui"],
            "openai": ["openai", "genai", "llm"],
            "langchain": ["langchain", "genai", "rag"],
            "faiss": ["faiss", "vector-search", "rag"],
            "edge": ["edge-ai", "embedded"],
            "iot": ["iot", "embedded"],
            "computer vision": ["computer-vision", "image-processing"],
            "nlp": ["nlp", "text-processing"],
            "pruning": ["pruning", "optimization"],
            "quantization": ["quantization", "optimization"],
            "distributed": ["distributed-systems"],
            "real-time": ["real-time"],
            "research": ["research", "academic"]
        }
        
        for skill_key, tag_list in skill_to_tags.items():
            if skill_key in skill_lower:
                tags.extend(tag_list)
        
        return tags

    async def _generate_research_section_optimized(self, job_description: str, projects: List[Dict[str, Any]], job_data: Dict[str, Any]) -> str:
        """Generate research experience section with academic focus (optimized version)."""
        try:
            print(f"[DEBUG] _generate_research_section_optimized called with {len(projects)} projects")
            print(f"[DEBUG] projects: {[p.get('title', 'No title') for p in projects]}")
            
            # Start with basic research experience header (no duplicate)
            research_section = "Research Experience\nPhD Researcher, University of South Florida — Tampa, FL\n2019 – Present\n\n"
            
            # Create research project descriptions
            research_descriptions = []
            for i, project in enumerate(projects[:4]):  # Top 4 research projects
                desc = f"Research {i+1}: {project.get('title', '')}\n"
                desc += f"Role: {project.get('role', '')}\n"
                desc += f"Technologies: {', '.join(project.get('technologies', []))}\n"
                desc += f"Methods: {project.get('methods', '')}\n"
                desc += f"Results: {project.get('results', '')}\n"
                desc += f"Impact: {project.get('impact', '')}\n"
                desc += f"Duration: {project.get('duration', '')}\n"
                research_descriptions.append(desc)
            
            print(f"[DEBUG] research_descriptions count: {len(research_descriptions)}")
            
            if not research_descriptions:
                print("[DEBUG] No research descriptions - returning basic header")
                return research_section + "Conducted research in neural network optimization and edge AI deployment."
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert academic resume writer. Create a concise, impactful research experience section that:
                1. Highlights key technical contributions and innovations
                2. Emphasizes quantifiable results and measurable impact
                3. Uses strong action verbs and technical precision
                4. Focuses on research outcomes and field contributions
                5. Follows professional resume formatting (not academic CV)
                6. Creates tight, scannable bullet points for each research project
                7. Removes redundancy and wordiness
                8. Uses active, resume-style language (not paper abstract style)
                9. Uses consistent past tense for completed work
                10. Provides specific metrics and percentages
                
                Format as concise research project descriptions with clear project titles and impactful bullet points.
                DO NOT include the basic header (Research Experience, PhD Researcher, etc.) as that will be added separately.
                
                For each research project, create 2-3 tight bullet points that highlight:
                - Action + Method + Result (in ~2 lines)
                - Quantifiable impact and technical achievements
                - Publications, patents, or awards if applicable
                
                Avoid verbose descriptions, abstract-style language, or phrases like "The research outcome offers..."
                Use active language: "Compressed CNNs by 80%" not "Successfully achieved up to 80% model compression"
                Use tight phrasing: "achieving 80% CNN model compression" not "resulting in up to 80% model compression of CNNs"
                Include specific metrics: inference speedup, accuracy improvements, deployment efficiency
                Hiring managers skim - make each bullet count."""),
                ("user", """Job Title: {job_title}
                Industry Focus: {industry_focus}
                Required Skills: {required_skills}
                
                Research Projects:
                {research_descriptions}
                
                Create concise, impactful research project descriptions that showcase these projects for this role. 
                Focus on action + method + result in tight, scannable bullet points.
                Use active, resume-style language throughout.
                
                For each project, emphasize:
                - Specific technical achievements and innovations
                - Quantifiable results (percentages, speedups, efficiency gains)
                - Real-world impact and applications
                - Technical depth and complexity handled
                
                Use consistent past tense and avoid redundant phrases.""")
            ])
            
            chain = prompt | self.llm
            
            response = await chain.ainvoke({
                "job_title": job_data.get("job_title", ""),
                "industry_focus": job_data.get("industry_focus", ""),
                "required_skills": ", ".join(job_data.get("required_skills", [])),
                "research_descriptions": "\n\n".join(research_descriptions)
            })
            
            print(f"[DEBUG] Research section generated successfully")
            return research_section + response.content
            
        except Exception as e:
            print(f"[ERROR] Error in _generate_research_section_optimized: {str(e)}")
            raise ValueError(f"Error generating research section: {str(e)}")

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

    async def _generate_experience_section_optimized(self, job_description: str, projects: List[Dict[str, Any]], job_data: Dict[str, Any]) -> str:
        """Generate experience section with project-based bullet points (optimized version)."""
        try:
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

    async def _generate_projects_section_optimized(self, job_description: str, projects: List[Dict[str, Any]], job_data: Dict[str, Any]) -> str:
        """Generate projects section with detailed project descriptions (optimized version)."""
        try:
            # Create detailed project descriptions
            project_details = []
            for i, project in enumerate(projects[:8]):  # Top 8 projects for more comprehensive coverage
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
                ("system", """You are an expert resume writer. Create a sharp, impactful projects section that:
                1. Showcases the most relevant projects for the job
                2. Provides concise, action-driven project descriptions
                3. Emphasizes technical skills and quantifiable results
                4. Uses product launch-style phrasing (e.g., "Developed X that achieved Y")
                5. Uses professional formatting with clear project titles and bullet points
                6. Avoids repetition with research experience section
                7. Cross-references research projects briefly if they appear in both sections
                
                Format each project with a clear title and 2-3 impactful bullet points.
                Focus on: Action + Technology + Result + Impact
                Use phrases like "Developed", "Built", "Created" followed by specific outcomes.
                
                If a project was already described in Research Experience, use cross-reference format:
                "Project Name - See Research Experience
                Brief description focusing on different aspects or additional outcomes"
                
                Avoid duplicating detailed descriptions from the Research section."""),
                ("user", """Job Title: {job_title}
                Industry Focus: {industry_focus}
                Required Skills: {required_skills}
                
                Project Details:
                {project_details}
                
                Create a sharp, impactful projects section that best showcases these projects for this role.
                Focus on action + technology + result in concise bullet points.
                Avoid repetition with Research Experience section.""")
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

    async def _generate_skills_section_optimized(self, projects: List[Dict[str, Any]], 
                                     job_description: str, job_data: Dict[str, Any]) -> str:
        """Generate skills section based on project technologies and job requirements (optimized version)."""
        try:
            print(f"[DEBUG] _generate_skills_section_optimized called with {len(projects)} projects")
            
            # Extract skills from projects
            project_skills = set()
            for project in projects:
                technologies = project.get("technologies", [])
                project_skills.update(technologies)
            
            print(f"[DEBUG] Extracted {len(project_skills)} unique skills from projects: {list(project_skills)[:10]}...")
            
            # Get job requirements
            required_skills = job_data.get("required_skills", [])
            preferred_skills = job_data.get("preferred_skills", [])
            
            # Get master skills from project store for comprehensive coverage
            master_skills_text = self.project_store.get_master_skills_as_text()
            
            # Create a comprehensive skills list from multiple sources
            all_skills = set()
            
            # Add project skills
            all_skills.update(project_skills)
            
            # Add required and preferred skills from job
            all_skills.update(required_skills)
            all_skills.update(preferred_skills)
            
            # Add skills from master skills database
            if master_skills_text:
                # Parse master skills text to extract individual skills
                lines = master_skills_text.split('\n')
                for line in lines:
                    if ':' in line:
                        skills_part = line.split(':', 1)[1].strip()
                        skills = [s.strip() for s in skills_part.split(',')]
                        all_skills.update(skills)
            
            # Remove empty strings and normalize
            all_skills = {skill.strip() for skill in all_skills if skill.strip()}
            
            print(f"[DEBUG] Total unique skills collected: {len(all_skills)}")
            
            # Create a fallback skills section if LLM fails
            fallback_skills = self._create_fallback_skills_section(all_skills, required_skills, preferred_skills)
            
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are an expert resume writer. Create a concise, job-tailored skills section that:
                    1. Prioritizes skills mentioned in the job requirements
                    2. Groups skills into 4-6 logical, recruiter-friendly categories
                    3. Uses clean formatting with consistent separators (e.g., "Languages:", "Frameworks:", "Tools:")
                    4. Focuses on the most relevant skills for the position
                    5. Includes expanded acronyms for ATS optimization (e.g., "Deep Neural Networks (DNNs)")
                    6. Eliminates redundancy and keeps each category concise
                    7. Avoids overlapping categories
                    8. Uses specific hardware descriptions (e.g., "NVIDIA GeForce GTX 1080 Ti (11 GB)")
                    
                    IMPORTANT: Format each category as:
                    **Languages:** Python, C++
                    **Frameworks:** PyTorch 2.1.2, ONNX, FastAPI, Pydantic
                    **Tools:** Git, CUDA 12.3, Edge Impulse, LangChain, python-docx, PyMuPDF, JSON
                    **AI/ML:** Binarized Neural Networks (BNNs), Convolutional Neural Networks (CNNs), OpenAI GPT Models, LLM Fine-tuning, RAG Pipelines, Model Compression, Dynamic Pruning
                    **Optimization Techniques:** Sparsity Optimization, Structured/Unstructured Pruning, Quantization, RigL-based Dynamic Sparsity
                    **Hardware & Protocols:** NVIDIA GeForce GTX 1080 Ti (11 GB), PYNQ Z1 AP-SoC, Arduino, Low-latency Protocols, IoT, Edge Devices
                    
                    Use consistent formatting with colons and commas. No bullet points.
                    Do NOT write descriptions or explanations. Just list the skills.
                    Do NOT use phrases like "Proficient in" or "Experience with" - just the skill names.
                    Group related skills together and avoid creating too many categories."""),
                    ("user", """Job Title: {job_title}
                    Required Skills: {required_skills}
                    Preferred Skills: {preferred_skills}
                    Available Skills: {available_skills}
                    
                    Create a professional, ATS-optimized skills section that best matches the job requirements. 
                    Use 4-6 categories maximum and avoid redundancy.
                    Format exactly as shown in the system prompt with **Category:** skill1, skill2 format.""")
                ])
                
                chain = prompt | self.llm
                
                response = await chain.ainvoke({
                    "job_title": job_data.get("job_title", ""),
                    "required_skills": ", ".join(required_skills),
                    "preferred_skills": ", ".join(preferred_skills),
                    "available_skills": ", ".join(list(all_skills)[:50])  # Limit to top 50
                })
                
                print(f"[DEBUG] Skills section LLM response: {response.content[:300]}...")
                
                # Validate the response
                if response.content and len(response.content.strip()) > 50:
                    return response.content
                else:
                    print("[WARNING] LLM response too short, using fallback")
                    return fallback_skills
                    
            except Exception as llm_error:
                print(f"[ERROR] LLM failed for skills generation: {str(llm_error)}")
                return fallback_skills
            
        except Exception as e:
            print(f"[ERROR] Skills generation failed: {str(e)}")
            # Return a basic fallback
            return """**Programming Languages:** Python, C++
**AI/ML Frameworks:** PyTorch, TensorFlow, ONNX, scikit-learn
**Tools & Platforms:** Git, Docker, CUDA, Linux, Jupyter
**AI/ML Techniques:** Deep Learning, Model Compression, Quantization, Pruning
**Hardware & Embedded:** PYNQ-Z1, Arduino, Edge Devices, IoT"""

    def _create_fallback_skills_section(self, all_skills: set, required_skills: list, preferred_skills: list) -> str:
        """Create a fallback skills section when LLM fails."""
        try:
            # Categorize skills manually
            languages = {"python", "c++", "java", "javascript", "matlab"}
            frameworks = {"pytorch", "tensorflow", "onnx", "fastapi", "scikit-learn", "numpy", "pandas"}
            tools = {"git", "docker", "cuda", "linux", "jupyter", "pytest", "ci/cd"}
            ai_ml = {"deep learning", "machine learning", "neural networks", "llm", "rag", "pruning", "quantization", "optimization"}
            hardware = {"pynq", "arduino", "fpga", "edge devices", "iot", "embedded"}
            
            # Categorize available skills
            categorized = {
                "Languages": [],
                "Frameworks": [],
                "Tools": [],
                "AI/ML": [],
                "Hardware": []
            }
            
            for skill in all_skills:
                skill_lower = skill.lower()
                if skill_lower in languages:
                    categorized["Languages"].append(skill)
                elif skill_lower in frameworks:
                    categorized["Frameworks"].append(skill)
                elif skill_lower in tools:
                    categorized["Tools"].append(skill)
                elif skill_lower in ai_ml:
                    categorized["AI/ML"].append(skill)
                elif skill_lower in hardware:
                    categorized["Hardware"].append(skill)
                else:
                    # Default to Tools if not categorized
                    categorized["Tools"].append(skill)
            
            # Build the formatted string
            sections = []
            for category, skills in categorized.items():
                if skills:
                    # Prioritize required and preferred skills
                    prioritized_skills = []
                    for skill in skills:
                        if skill.lower() in [s.lower() for s in required_skills + preferred_skills]:
                            prioritized_skills.insert(0, skill)
                        else:
                            prioritized_skills.append(skill)
                    
                    # Take top 8 skills per category
                    top_skills = prioritized_skills[:8]
                    sections.append(f"**{category}:** {', '.join(top_skills)}")
            
            return "\n".join(sections)
            
        except Exception as e:
            print(f"[ERROR] Fallback skills creation failed: {str(e)}")
            return """**Programming Languages:** Python, C++
**AI/ML Frameworks:** PyTorch, TensorFlow, ONNX
**Tools:** Git, Docker, CUDA, Linux
**AI/ML:** Deep Learning, Model Compression, Quantization"""

    async def _generate_summary_section_optimized(self, projects: List[Dict[str, Any]], 
                                      job_description: str, job_data: Dict[str, Any]) -> str:
        """Generate summary section (optimized version)."""
        try:
            # Extract key skills from projects
            key_skills = set()
            for project in projects[:5]:  # Use top 5 projects
                technologies = project.get("technologies", [])
                key_skills.update(technologies[:3])  # Top 3 technologies per project
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert resume writer. Create a tight, impactful professional summary that:
                1. Gets to the point in 2-3 lines maximum
                2. Highlights key achievements and expertise
                3. Matches the job requirements and industry focus
                4. Uses strong action verbs and quantifiable results
                5. Removes buzzwords and fluff
                6. Focuses on "who you are" + "what you've done" in 3 seconds
                7. Avoids brand names unless directly relevant to the job
                8. Makes the candidate generalizable across different roles
                
                IMPORTANT: 
                - Format as a concise professional summary paragraph
                - Do NOT use quotation marks around the summary
                - Do NOT start with phrases like "Strategic" or "Proven track record"
                - Be specific and impactful
                - Focus on skills and capabilities rather than specific hardware or brand mentions
                - Keep it to 2-3 sentences maximum"""),
                ("user", """Job Title: {job_title}
                Industry Focus: {industry_focus}
                Required Skills: {required_skills}
                Key Project Skills: {key_skills}
                
                Create a tight, job-tailored summary that positions the candidate well for this role.
                Focus on data-centric AI, research engineering, or GenAI infrastructure as appropriate.
                Return ONLY the summary text without any quotes or formatting markers.""")
            ])
            
            chain = prompt | self.llm
            
            response = await chain.ainvoke({
                "job_title": job_data.get("job_title", ""),
                "industry_focus": job_data.get("industry_focus", ""),
                "required_skills": ", ".join(job_data.get("required_skills", [])),
                "key_skills": ", ".join(list(key_skills)[:10])  # Top 10 skills
            })
            
            # Clean up the response to remove quotes and extra formatting
            summary = response.content.strip()
            
            # Remove surrounding quotes if present
            if summary.startswith('"') and summary.endswith('"'):
                summary = summary[1:-1].strip()
            elif summary.startswith('"') and summary.endswith('"'):
                summary = summary[1:-1].strip()
            
            # Remove any markdown formatting
            summary = summary.replace('**', '').replace('*', '')
            
            # Ensure it's not empty
            if not summary or len(summary) < 20:
                # Fallback summary
                summary = "PhD in Computer Science with expertise in neural network optimization, GenAI pipelines, and embedded ML deployment. Demonstrated success in developing scalable ML systems with 80% model compression and 3-5x inference speedup. Seeking roles focused on applied ML research and real-world deployment."
            
            return summary
            
        except Exception as e:
            print(f"[ERROR] Summary generation failed: {str(e)}")
            # Return a fallback summary
            return "PhD in Computer Science with expertise in neural network optimization, GenAI pipelines, and embedded ML deployment. Demonstrated success in developing scalable ML systems with 80% model compression and 3-5x inference speedup. Seeking roles focused on applied ML research and real-world deployment."

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