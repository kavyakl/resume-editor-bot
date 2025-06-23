from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings
import yaml
import os
from typing import Dict, Any, List
import json
from datetime import datetime
from langchain.prompts import PromptTemplate
from app.core.prompts import PROJECT_PARSER_PROMPT

class ProjectParserService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
            
        self.llm = ChatOpenAI(
            model=settings.openai.model,
            temperature=settings.openai.temperature,
            api_key=settings.OPENAI_API_KEY
        )
        
        self.projects_dir = settings.paths.projects_dir
        os.makedirs(self.projects_dir, exist_ok=True)

    async def parse_project_dump(self, dump_text: str, project_title: str = None) -> Dict[str, Any]:
        """
        Parse natural language project dump into structured format.
        
        Args:
            dump_text: Raw project description
            project_title: Optional title for the project
            
        Returns:
            Structured project dictionary
        """
        try:
            # Create prompt for structured parsing
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at parsing project descriptions into structured data. 
                Extract the following information from the project description:
                
                - title: Project title (if not provided, generate a concise one)
                - description: Brief project overview (2-3 sentences)
                - role: Your role in the project
                - technologies: List of technologies, tools, frameworks used
                - methods: Technical methods, algorithms, or approaches used
                - results: Quantifiable results, metrics, or outcomes
                - impact: Business or research impact
                - duration: Project duration (e.g., "3 months", "2023-2024")
                - team_size: Number of people involved
                - challenges: Key challenges faced and how they were solved
                
                Return ONLY a valid JSON object with these fields. Use null for missing information."""),
                ("user", "Project Description: {dump_text}\nProject Title: {project_title}")
            ])
            
            chain = prompt | self.llm
            
            response = await chain.ainvoke({
                "dump_text": dump_text,
                "project_title": project_title or "Untitled Project"
            })
            
            # Parse the JSON response
            try:
                project_data = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    project_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse structured data from response")
            
            # Add metadata
            project_data["created_at"] = datetime.now().isoformat()
            project_data["source_text"] = dump_text
            
            # Generate filename
            if not project_title:
                project_title = project_data.get("title", "untitled_project")
            
            filename = self._sanitize_filename(project_title)
            project_data["filename"] = filename
            
            return project_data
            
        except Exception as e:
            raise ValueError(f"Error parsing project dump: {str(e)}")

    def save_project(self, project_data: Dict[str, Any]) -> str:
        """
        Save structured project data to YAML file.
        
        Args:
            project_data: Structured project dictionary
            
        Returns:
            Path to saved file
        """
        try:
            filename = project_data.get("filename", "untitled_project")
            filepath = os.path.join(self.projects_dir, f"{filename}.yaml")
            
            # Convert to YAML and save
            with open(filepath, 'w') as f:
                yaml.dump(project_data, f, default_flow_style=False, sort_keys=False)
            
            return filepath
            
        except Exception as e:
            raise ValueError(f"Error saving project: {str(e)}")

    async def parse_and_save_project(self, dump_text: str, project_title: str) -> dict:
        """Parse a project dump and save it to a YAML file."""
        parsed_data = await self.parse_project_dump(dump_text, project_title)
        # Save to file
        filename = f"{project_title.lower().replace(' ', '_')}.yaml"
        filepath = os.path.join(self.projects_dir, filename)
        with open(filepath, 'w') as f:
            yaml.dump(parsed_data, f, default_flow_style=False, sort_keys=False)
        
        return parsed_data

    def _sanitize_filename(self, filename: str) -> str:
        """Convert project title to safe filename."""
        import re
        # Remove special characters and replace spaces with underscores
        safe_name = re.sub(r'[^\w\s-]', '', filename)
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        return safe_name.lower()

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """
        Load all project YAML files from the projects directory.
        
        Returns:
            List of project dictionaries
        """
        projects = []
        
        try:
            for filename in os.listdir(self.projects_dir):
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    filepath = os.path.join(self.projects_dir, filename)
                    with open(filepath, 'r') as f:
                        project_data = yaml.safe_load(f)
                        projects.append(project_data)
            
            return projects
            
        except Exception as e:
            raise ValueError(f"Error loading projects: {str(e)}")

    def get_project_by_title(self, title: str) -> Dict[str, Any]:
        """
        Load a specific project by title.
        
        Args:
            title: Project title to search for
            
        Returns:
            Project dictionary or None if not found
        """
        try:
            projects = self.get_all_projects()
            for project in projects:
                if project.get("title", "").lower() == title.lower():
                    return project
            return None
            
        except Exception as e:
            raise ValueError(f"Error finding project: {str(e)}") 