import os
import json
from sklearn.metrics.pairwise import cosine_similarity
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS

from app.core.config import settings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.services.job_analysis_service import JobAnalysisService
from app.services.project_store import ProjectStoreService

class RelevanceRanker:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai.model,
            temperature=settings.openai.temperature,
            api_key=settings.OPENAI_API_KEY
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.vector_db.embedding_model,
            api_key=settings.OPENAI_API_KEY
        )
        self.vector_store_path = os.path.join(settings.paths.embeddings_dir, "projects_relevance")
        self.vector_store = self._load_vector_store()
        self.job_parser = JobAnalysisService()
        self.project_store = ProjectStoreService()

    def _load_vector_store(self):
        if os.path.exists(self.vector_store_path):
            try:
                return FAISS.load_local(
                    self.vector_store_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Could not load project relevance vector store: {e}")
                return None
        return None

    def create_project_vector_store(self, projects: list[dict]):
        documents = [Document(page_content=json.dumps(p, indent=2)) for p in projects]
        if not documents:
            return
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        os.makedirs(self.vector_store_path, exist_ok=True)
        self.vector_store.save_local(self.vector_store_path)

    async def rank_projects(self, job_description: str, projects: list[dict]) -> list[dict]:
        if not projects:
            return []

        job_embedding = self.embeddings.embed_query(job_description)
        project_embeddings = self.embeddings.embed_documents([json.dumps(p) for p in projects])
        
        similarities = cosine_similarity([job_embedding], project_embeddings)[0]
        
        for i, project in enumerate(projects):
            project['relevance_score'] = similarities[i]
            
        ranked_projects = sorted(projects, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        relevance_threshold = settings.project_analysis.relevance_threshold
        qualified_projects = [p for p in ranked_projects if p.get('relevance_score', 0) >= relevance_threshold]
        
        return qualified_projects

    async def get_project_recommendations(self, job_description: str) -> dict:
        projects = self.project_store.get_all_projects()
        ranked_projects = await self.rank_projects(job_description, projects)
        top_projects = ranked_projects[:settings.project_analysis.max_recommendations]

        job_analysis = await self.job_parser.analyze_job_description(job_description)
        project_stats = self.project_store.get_project_statistics()

        return {
            "ranked_projects": top_projects,
            "job_analysis": job_analysis,
            "project_statistics": project_stats
        } 