import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Dict, Any, List, Optional
from app.services.rag_service import RAGService
from app.services.job_analysis_service import JobAnalysisService
from app.services.export_service import ExportService
from app.services.resume_parser_service import ResumeParserService
from app.services.project_parser import ProjectParserService
from app.services.project_store import ProjectStoreService
from app.services.relevance_ranker import RelevanceRanker
from app.services.resume_writer import ResumeWriterService
from app.services.cover_letter_writer import CoverLetterWriterService
from app.services.resume_scorer import ResumeScorerService
from app.core.job_parser import JobParserService
from pydantic import BaseModel
import os
import tempfile
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)
rag_service = RAGService()
job_analysis_service = JobAnalysisService()
export_service = ExportService()
resume_parser_service = ResumeParserService()
project_parser_service = ProjectParserService()
project_store_service = ProjectStoreService()
resume_writer_service = ResumeWriterService(project_store_service)
# relevance_ranker_service = RelevanceRanker()
cover_letter_writer_service = CoverLetterWriterService()
resume_scorer_service = ResumeScorerService()
job_parser_service = JobParserService()

# Global variable for lazy loading
relevance_ranker_service = None

def get_relevance_ranker():
    """Lazy initialization of relevance ranker service."""
    global relevance_ranker_service
    if relevance_ranker_service is None:
        try:
            relevance_ranker_service = RelevanceRanker()
        except Exception as e:
            logger.error(f"Error initializing relevance ranker: {e}")
            # Return a minimal implementation
            class MinimalRelevanceRanker:
                async def rank_projects_for_job(self, job_description: str, top_k: int = 5):
                    return []
                async def get_project_recommendations(self, job_description: str):
                    return {"ranked_projects": [], "job_analysis": {}, "project_statistics": {}}
                async def create_project_vector_store(self):
                    return False
            relevance_ranker_service = MinimalRelevanceRanker()
    return relevance_ranker_service

class ResumeSection(BaseModel):
    section_name: str
    content: str

class QueryRequest(BaseModel):
    query: str
    num_results: int = 3

class JobDescriptionRequest(BaseModel):
    job_description: str

class ResumeData(BaseModel):
    sections: Dict[str, str]

class ExportRequest(BaseModel):
    resume_data: ResumeData
    format: str  # "pdf", "docx", or "json"

# New project-based models
class ProjectDumpRequest(BaseModel):
    dump_text: str
    project_title: str = None

class GenerateResumeRequest(BaseModel):
    job_description: str
    candidate_skills: List[str] = None
    include_sections: List[str] = None

class OptimizeSectionRequest(BaseModel):
    current_section: str
    section_name: str
    job_description: str

class TailoredResumeRequest(BaseModel):
    job_description: str
    include_sections: list[str]
    candidate_skills: list[str] = [] # Making it optional, though not used in generation

class DeduplicatedResumeRequest(BaseModel):
    job_description: str
    include_sections: List[str]
    candidate_skills: List[str] = None
    max_projects_per_section: int = 4

class CoverLetterRequest(BaseModel):
    job_description: str
    candidate_name: str
    candidate_resume_sections: Dict[str, Any]
    company_name: str = None
    job_title: str = None
    tone: str = "professional"

class ResumeScoringRequest(BaseModel):
    job_description: str
    resume_data: Dict[str, Any]

@router.post("/optimize-section")
async def optimize_section(section: ResumeSection, job_description: str):
    try:
        optimized_content = await rag_service.optimize_section(
            section.section_name,
            section.content,
            job_description
        )
        return {"optimized_content": optimized_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def query_vector_store(request: QueryRequest):
    try:
        results = await rag_service.query(request.query, request.num_results)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="Only .docx files are supported"
        )
        
    try:
        # Read file content
        content = await file.read()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Parse resume
            parsed_resume = resume_parser_service.parse_docx(temp_file_path)
            
            # Create vector store
            await rag_service.create_vector_store(parsed_resume)
            
            return {
                "status": "success",
                "message": "Resume uploaded and processed successfully",
                "parsed_data": parsed_resume
            }
            
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing resume: {str(e)}"
            )
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )

@router.post("/analyze-job")
async def analyze_job(request: JobDescriptionRequest):
    try:
        analysis = await job_analysis_service.analyze_job_description(request.job_description)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-skill-match")
async def calculate_skill_match(resume_data: ResumeData, job_description: str):
    try:
        match_results = await job_analysis_service.calculate_skill_match(
            resume_data.sections.get("skills", ""),
            job_description
        )
        return match_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest-improvements")
async def suggest_improvements(section: ResumeSection, job_description: str):
    try:
        suggestions = await job_analysis_service.suggest_improvements(
            section.section_name,
            section.content,
            job_description
        )
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_resume(request: ExportRequest):
    try:
        if request.format == "pdf":
            file_path = export_service.export_to_pdf(request.resume_data.sections)
        elif request.format == "docx":
            file_path = export_service.export_to_docx(request.resume_data.sections)
        elif request.format == "json":
            file_path = export_service.export_to_json(request.resume_data.sections)
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
        return {"file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/use-existing-resume")
async def use_existing_resume():
    try:
        # Use the existing resume file if it exists
        resume_path = "Kalyanam_resume.docx"
        if os.path.exists(resume_path):
            # Parse existing resume
            parsed_resume = resume_parser_service.parse_docx(resume_path)
            
            # Create vector store
            await rag_service.create_vector_store(parsed_resume)
            
            return {
                "status": "success",
                "message": "Resume processed successfully",
                "parsed_data": parsed_resume
            }
        else:
            # Provide default resume structure when no file exists
            default_resume = {
                "name": "Lakshmi Kavya Kalyanam",
                "contact": {
                    "email": "kavyakalyanamk@gmail.com",
                    "phone": "+1-813-609-9796",
                    "location": "Tampa, FL",
                    "linkedin": "linkedin.com/in/lakshmikavya-kalyanam-a88633131"
                },
                "sections": {
                    "summary": "PhD in Computer Science with expertise in neural network optimization, GenAI pipelines, and embedded ML deployment. Seeking Applied Scientist roles focused on scalable ML systems, search ranking models, reinforcement learning, and real-world deployment on large-scale infrastructure.",
                    "skills": "Programming Languages: Python, C++, CUDA, Verilog\nMachine Learning: PyTorch, TensorFlow, ONNX, Scikit-learn\nDeep Learning: Neural Networks, Computer Vision, NLP\nOptimization: Model Pruning, Quantization, Edge Deployment\nTools & Platforms: Docker, AWS, Git, Linux\nHardware: FPGA, Embedded Systems, IoT Devices",
                    "experience": [
                        {
                            "title": "PhD Researcher",
                            "company": "University of South Florida",
                            "duration": "2019 - Present",
                            "description": [
                                "Researching neural network optimization and dynamic sparsity techniques",
                                "Developing embedded ML deployment solutions for edge devices",
                                "Publishing in top-tier conferences and filing patents"
                            ]
                        }
                    ],
                    "education": [
                        {
                            "degree": "Ph.D., Computer Science",
                            "institution": "University of South Florida",
                            "duration": "Expected 2025",
                            "details": ["Focus: Neural network compression, dynamic sparsity, embedded ML deployment"]
                        },
                        {
                            "degree": "M.S., Computer Science", 
                            "institution": "University of South Florida",
                            "duration": "2020",
                            "details": ["Thesis: Real-time object detection using BNNs on PYNQ-Z1"]
                        }
                    ],
                    "projects": [
                        {
                            "title": "LitBot – AI Literature Survey Assistant",
                            "description": ["Developed GPT + FAISS-powered assistant for academic paper search and summarization", "Accelerated literature review workflows by 80%"]
                        },
                        {
                            "title": "Resume Editor Bot – RAG-Powered Resume Generator", 
                            "description": ["Created job-tailored resume builder using RAG + OpenAI APIs", "Features project ranking, DOCX export, and LLM-based section rewriting"]
                        }
                    ]
                }
            }
            
            # Create vector store from default resume
            await rag_service.create_vector_store(default_resume)
            
            return {
                "status": "success", 
                "message": "Using default resume structure (no file found)",
                "parsed_data": default_resume
            }
            
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing resume: {str(e)}"
        )

# New project-based routes
@router.post("/project-dump")
async def parse_project_dump(request: ProjectDumpRequest):
    """Parse a natural language project dump into structured format."""
    try:
        result = await project_parser_service.parse_and_save_project(
            request.dump_text, 
            request.project_title
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects")
async def get_all_projects():
    """Get all stored projects."""
    try:
        projects = project_store_service.get_all_projects()
        return {"projects": projects, "count": len(projects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/statistics")
async def get_project_statistics():
    print("=== ENTERED /api/projects/statistics ENDPOINT ===")
    try:
        stats = project_store_service.get_project_statistics()
        return stats
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"ERROR in /api/projects/statistics: {e}")
        print(f"TRACEBACK: {tb}")
        return {"error": str(e), "traceback": tb}

@router.get("/projects/{project_title}")
async def get_project_by_title(project_title: str):
    """Get a specific project by title."""
    try:
        project = project_store_service.get_project_by_title(project_title)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/search/{query}")
async def search_projects(query: str, limit: int = 5):
    """Search projects by query."""
    try:
        projects = project_store_service.search_projects(query, limit)
        return {"projects": projects, "query": query, "count": len(projects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/technology/{technology}")
async def get_projects_by_technology(technology: str):
    """Get projects that use a specific technology."""
    try:
        projects = project_store_service.get_projects_by_technology(technology)
        return {"projects": projects, "technology": technology, "count": len(projects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parse-job")
async def parse_job_description(request: JobDescriptionRequest):
    """Parse job description into structured format."""
    try:
        job_data = await job_parser_service.parse_job_description(request.job_description)
        return job_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rank-projects")
async def rank_projects_for_job(request: JobDescriptionRequest, top_k: int = 5):
    """Rank projects by relevance to job description."""
    try:
        ranked_projects = await get_relevance_ranker().rank_projects_for_job(
            request.job_description, top_k
        )
        return {"ranked_projects": ranked_projects, "count": len(ranked_projects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/project-recommendations")
async def get_project_recommendations(job_description: JobDescriptionRequest):
    """Get comprehensive project recommendations for a job."""
    try:
        recommendations = await get_relevance_ranker().get_project_recommendations(job_description.job_description)
        # Ensure the response is JSON serializable
        if isinstance(recommendations, dict):
            return recommendations
        else:
            # Convert to dict if it's not already
            return {"ranked_projects": [], "job_analysis": {}, "project_statistics": {}}
    except Exception as e:
        logger.error(f"Error in project recommendations: {e}")
        return {"ranked_projects": [], "job_analysis": {}, "project_statistics": {}}

@router.post("/generate-resume-section")
async def generate_resume_section(section_name: str, section_type: str, request: JobDescriptionRequest):
    """Generate a specific resume section."""
    try:
        # Get ranked projects
        ranked_projects = await get_relevance_ranker().rank_projects_for_job(
            request.job_description, top_k=10
        )
        
        # Generate section
        section_content = await resume_writer_service.generate_resume_section(
            section_name, ranked_projects, request.job_description, section_type
        )
        
        return {
            "section_name": section_name,
            "section_type": section_type,
            "content": section_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-tailored-resume", response_model=dict)
async def generate_tailored_resume_route(request: TailoredResumeRequest):
    """
    Generate a complete, tailored resume with specific sections.
    """
    try:
        generated_data = resume_writer_service.generate_tailored_resume(
            job_description=request.job_description,
            include_sections=request.include_sections,
        )
        return generated_data
    except Exception as e:
        logger.error(f"Error generating tailored resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-deduplicated-resume", response_model=dict)
async def generate_deduplicated_resume_route(request: DeduplicatedResumeRequest):
    """
    Generate a complete, tailored resume with intelligent project deduplication.
    Ensures projects aren't repeated across different sections.
    """
    try:
        generated_data = await resume_writer_service.generate_tailored_resume_with_deduplication(
            job_description=request.job_description,
            include_sections=request.include_sections,
            candidate_skills=request.candidate_skills
        )
        return generated_data
    except Exception as e:
        logger.error(f"Error generating deduplicated resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-academic-cv", response_model=dict)
async def generate_academic_cv_route(request: DeduplicatedResumeRequest):
    """
    Generate an academic CV with comprehensive research and project sections.
    Includes all relevant projects without strict deduplication for academic purposes.
    """
    try:
        # For academic CV, we want to include more comprehensive sections
        academic_sections = ["summary", "research", "projects", "skills", "education"]
        
        generated_data = await resume_writer_service.generate_tailored_resume_with_deduplication(
            job_description=request.job_description,
            include_sections=academic_sections,
            candidate_skills=request.candidate_skills
        )
        
        # Add academic-specific metadata
        generated_data["cv_type"] = "academic"
        generated_data["comprehensive_mode"] = True
        
        return generated_data
    except Exception as e:
        logger.error(f"Error generating academic CV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-cover-letter", response_model=dict)
async def generate_cover_letter_route(request: CoverLetterRequest):
    """
    Generate a tailored cover letter based on resume data and job description.
    """
    try:
        # Extract company info if not provided
        company_name = request.company_name
        job_title = request.job_title
        
        if not company_name or not job_title:
            extracted_info = cover_letter_writer_service.extract_company_info(request.job_description)
            company_name = company_name or extracted_info["company_name"]
            job_title = job_title or extracted_info["job_title"]
        
        # Generate cover letter
        result = await cover_letter_writer_service.generate_cover_letter(
            job_description=request.job_description,
            candidate_name=request.candidate_name,
            candidate_resume_sections=request.candidate_resume_sections,
            company_name=company_name,
            job_title=job_title,
            tone=request.tone
        )
        
        return result
    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/score-resume", response_model=dict)
async def score_resume_route(request: ResumeScoringRequest):
    """
    Score a resume against a job description using ATS simulation and LLM feedback.
    """
    try:
        # Score the resume
        result = await resume_scorer_service.score_resume(
            job_description=request.job_description,
            resume_data=request.resume_data
        )
        
        return result
    except Exception as e:
        logger.error(f"Error scoring resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-resume-section")
async def optimize_resume_section(request: OptimizeSectionRequest):
    """Optimize an existing resume section for a job."""
    try:
        optimized_content = await resume_writer_service.optimize_existing_section(
            request.current_section,
            request.section_name,
            request.job_description
        )
        return {
            "section_name": request.section_name,
            "original_content": request.current_section,
            "optimized_content": optimized_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-cover-letter-intro")
async def generate_cover_letter_intro(request: JobDescriptionRequest, candidate_skills: List[str] = None):
    """Generate a cover letter introduction paragraph."""
    try:
        intro = await resume_writer_service.generate_cover_letter_intro(
            request.job_description, candidate_skills
        )
        return {"cover_letter_intro": intro}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-project-vector-store")
async def create_project_vector_store():
    """Create vector store from all projects."""
    try:
        success = await get_relevance_ranker().create_project_vector_store()
        return {"status": "success", "message": "Project vector store created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy"} 