from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from app.core.config import settings
import os
import json
import faiss
from langchain.chains import ConversationalRetrievalChain

class RAGService:
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.llm = ChatOpenAI(
            model=settings.openai.model,
            temperature=settings.openai.temperature,
            api_key=self.openai_api_key
        )
        self.embedding_model = OpenAIEmbeddings(
            model=settings.vector_db.embedding_model,
            api_key=self.openai_api_key
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.vector_db.chunk_size,
            chunk_overlap=settings.vector_db.chunk_overlap
        )
        self.vector_store_path = settings.paths.embeddings_dir
        self.vector_store = self._load_vector_store()

    def _load_vector_store(self):
        """Loads the vector store from disk if it exists, otherwise returns None."""
        index_path = os.path.join(self.vector_store_path, "index.faiss")
        if os.path.exists(index_path):
            try:
                return FAISS.load_local(
                    self.vector_store_path,
                    self.embedding_model,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Error loading vector store: {e}. A new one will be created upon upload.")
                return None
        return None

    async def create_vector_store(self, resume_data):
        """Create a vector store from resume data."""
        try:
            # Convert resume sections to documents
            documents = []
            for section_name, content in resume_data["sections"].items():
                if isinstance(content, list):
                    # Handle structured sections (experience, education, etc.)
                    for item in content:
                        if isinstance(item, dict):
                            doc_text = f"{section_name.title()}: {json.dumps(item, indent=2)}"
                        else:
                            doc_text = f"{section_name.title()}: {item}"
                        documents.append(Document(page_content=doc_text, metadata={"section": section_name}))
                else:
                    # Handle simple text sections
                    documents.append(Document(page_content=f"{section_name.title()}: {content}", metadata={"section": section_name}))
            
            if not documents:
                raise ValueError("No content found in resume sections")
            
            # Split documents into chunks
            texts = self.text_splitter.split_documents(documents)
            
            # Create and save vector store
            self.vector_store = FAISS.from_documents(texts, self.embedding_model)
            os.makedirs(self.vector_store_path, exist_ok=True)
            self.vector_store.save_local(self.vector_store_path)
            return True
            
        except Exception as e:
            raise ValueError(f"Error creating vector store: {str(e)}")

    async def query_vector_store(self, query: str, num_results: int = 5) -> list[str]:
        """Query the vector store for relevant documents."""
        if not self.vector_store:
            # Reload in case it was created in another process
            self.vector_store = self._load_vector_store()
            if not self.vector_store:
                raise ValueError("No resume has been processed. Please upload a resume first.")

        try:
            results = self.vector_store.similarity_search(query, k=num_results)
            return [doc.page_content for doc in results]
            
        except Exception as e:
            raise ValueError(f"Error querying vector store: {str(e)}")

    async def optimize_section(self, section_name: str, content: str, job_description: str):
        """Optimize a resume section based on job description."""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert resume writer. Your task is to optimize the given resume section to better match the job description while maintaining truthfulness and professionalism."),
                ("user", "Section: {section_name}\nCurrent Content: {content}\nJob Description: {job_description}\nPlease provide an optimized version of this section.")
            ])

            chain = prompt | self.llm
            response = await chain.ainvoke({
                "section_name": section_name,
                "content": content,
                "job_description": job_description
            })

            return response.content
            
        except Exception as e:
            raise ValueError(f"Error optimizing section: {str(e)}") 