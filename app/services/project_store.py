from typing import Dict, Any, List, Optional
import yaml
import os
from app.core.config import settings
from app.services.project_parser import ProjectParserService
import json
from datetime import datetime

class ProjectStoreService:
    def __init__(self):
        self.projects_dir = settings.paths.projects_dir
        os.makedirs(self.projects_dir, exist_ok=True)
        self.project_parser = ProjectParserService()
        self.projects_cache = None
        self.last_cache_update = None
        self.projects = self._load_all_projects()
        
    def get_all_projects(self) -> list[dict]:
        """Return all loaded projects from the cache."""
        return self.projects

    def _load_all_projects(self) -> list[dict]:
        """Load all project YAML files from the projects directory."""
        projects = []
        for filename in os.listdir(self.projects_dir):
            if filename.endswith(".yaml"):
                file_path = os.path.join(self.projects_dir, filename)
                with open(file_path, 'r') as f:
                    try:
                        project_data = yaml.safe_load(f)
                        if project_data:
                            # Validate and clean the project data
                            validated_project = self._validate_project(project_data)
                            if validated_project:
                                projects.append(validated_project)
                    except Exception as e:
                        print(f"Error loading project {filename}: {str(e)}")
                        continue
        return projects
    
    def _validate_project(self, project_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate and clean project data.
        
        Args:
            project_data: Raw project data from YAML
            
        Returns:
            Validated project data or None if invalid
        """
        try:
            # Required fields
            required_fields = ['title']
            
            # Check required fields
            for field in required_fields:
                if field not in project_data or not project_data[field]:
                    print(f"Project missing required field: {field}")
                    return None
            
            # Ensure title is a string
            project_data['title'] = str(project_data['title'])
            
            # Set default values for optional fields
            defaults = {
                'description': '',
                'role': '',
                'technologies': [],
                'methods': '',
                'results': '',
                'impact': '',
                'duration': '',
                'team_size': '',
                'challenges': '',
                'created_at': datetime.now().isoformat()
            }
            
            for field, default_value in defaults.items():
                if field not in project_data:
                    project_data[field] = default_value
            
            # Ensure technologies is a list
            if isinstance(project_data['technologies'], str):
                # Split by common delimiters
                tech_str = project_data['technologies']
                technologies = [tech.strip() for tech in tech_str.replace(',', ';').split(';') if tech.strip()]
                project_data['technologies'] = technologies
            
            return project_data
            
        except Exception as e:
            print(f"Error validating project: {str(e)}")
            return None
    
    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid by comparing file modification times."""
        try:
            if not os.path.exists(self.projects_dir):
                return False
            
            cache_time = self.last_cache_update.timestamp()
            
            for filename in os.listdir(self.projects_dir):
                if filename.endswith(('.yaml', '.yml')):
                    filepath = os.path.join(self.projects_dir, filename)
                    file_mtime = os.path.getmtime(filepath)
                    if file_mtime > cache_time:
                        return False
            
            return True
            
        except Exception:
            return False
    
    def get_project_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific project by title.
        
        Args:
            title: Project title to search for
            
        Returns:
            Project dictionary or None if not found
        """
        try:
            projects = self._load_all_projects()
            for project in projects:
                if project.get('title', '').lower() == title.lower():
                    return project
            return None
            
        except Exception as e:
            raise ValueError(f"Error finding project: {str(e)}")
    
    def search_projects(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search projects by title, description, or technologies.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching projects
        """
        try:
            projects = self._load_all_projects()
            query_lower = query.lower()
            
            # Simple text-based search
            matching_projects = []
            
            for project in projects:
                score = 0
                
                # Check title
                if query_lower in project.get('title', '').lower():
                    score += 3
                
                # Check description
                if query_lower in project.get('description', '').lower():
                    score += 2
                
                # Check technologies
                technologies = project.get('technologies', [])
                for tech in technologies:
                    if query_lower in tech.lower():
                        score += 1
                
                # Check methods
                if query_lower in project.get('methods', '').lower():
                    score += 1
                
                if score > 0:
                    matching_projects.append((project, score))
            
            # Sort by score and return top results
            matching_projects.sort(key=lambda x: x[1], reverse=True)
            return [project for project, score in matching_projects[:limit]]
            
        except Exception as e:
            raise ValueError(f"Error searching projects: {str(e)}")
    
    def get_projects_by_technology(self, technology: str) -> List[Dict[str, Any]]:
        """
        Get all projects that use a specific technology.
        
        Args:
            technology: Technology to search for
            
        Returns:
            List of projects using the technology
        """
        try:
            projects = self._load_all_projects()
            technology_lower = technology.lower()
            
            matching_projects = []
            
            for project in projects:
                technologies = project.get('technologies', [])
                for tech in technologies:
                    if technology_lower in tech.lower():
                        matching_projects.append(project)
                        break
            
            return matching_projects
            
        except Exception as e:
            raise ValueError(f"Error filtering by technology: {str(e)}")
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored projects.
        
        Returns:
            Dictionary with project statistics
        """
        try:
            projects = self._load_all_projects()
            
            if not projects:
                return {
                    'total_projects': 0,
                    'technologies': {},
                    'roles': {},
                    'avg_team_size': 0
                }
            
            # Count technologies
            technology_counts = {}
            role_counts = {}
            team_sizes = []
            
            for project in projects:
                # Count technologies
                technologies = project.get('technologies', [])
                for tech in technologies:
                    technology_counts[tech] = technology_counts.get(tech, 0) + 1
                
                # Count roles
                role = project.get('role', '')
                if role:
                    role_counts[role] = role_counts.get(role, 0) + 1
                
                # Collect team sizes
                team_size = project.get('team_size', '')
                if isinstance(team_size, int):
                    team_sizes.append(team_size)
                elif isinstance(team_size, str) and team_size.isdigit():
                    team_sizes.append(int(team_size))
            
            # Sort by frequency
            technology_counts = dict(sorted(technology_counts.items(), 
                                          key=lambda x: x[1], reverse=True))
            role_counts = dict(sorted(role_counts.items(), 
                                    key=lambda x: x[1], reverse=True))
            
            return {
                'total_projects': len(projects),
                'technologies': technology_counts,
                'roles': role_counts,
                'avg_team_size': sum(team_sizes) / len(team_sizes) if team_sizes else 0,
                'most_common_technologies': list(technology_counts.keys())[:5],
                'most_common_roles': list(role_counts.keys())[:5]
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating statistics: {str(e)}")
    
    def get_all_projects_as_text(self) -> str:
        """Return all loaded projects as a single formatted text string."""
        projects = self.get_all_projects()
        return json.dumps(projects, indent=2)

    def get_master_skills_as_text(self) -> str:
        """Load master skills from skills.yaml and format as a string."""
        skills_file_path = os.path.join(settings.paths.data_dir, "skills.yaml")
        if not os.path.exists(skills_file_path):
            return ""
        
        with open(skills_file_path, 'r') as f:
            skills_data = yaml.safe_load(f)
        
        skills_text = ""
        for category, skills in skills_data.items():
            skills_text += f"{category}:\n"
            skills_text += ", ".join(skills) + "\n\n"
            
        return skills_text.strip()

    def get_all_skills(self) -> list[str]:
        """Return a list of all unique skills from all projects."""
        projects = self.get_all_projects()
        all_skills = set()
        for project in projects:
            skills = project.get("technologies", [])
            if isinstance(skills, list):
                all_skills.update(skill.strip() for skill in skills)
        return sorted(list(all_skills))

    def export_projects_to_json(self, filepath: str = None) -> str:
        """
        Export all projects to a JSON file.
        
        Args:
            filepath: Optional file path to save to
            
        Returns:
            Path to the saved JSON file
        """
        try:
            projects = self._load_all_projects()
            
            if not filepath:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = os.path.join(settings.paths.data_dir, f"projects_export_{timestamp}.json")
            
            with open(filepath, 'w') as f:
                json.dump(projects, f, indent=4)
            
            return filepath
            
        except Exception as e:
            raise ValueError(f"Error exporting projects: {str(e)}")
    
    def save_project(self, project_data: dict):
        """Save a project to a YAML file."""
        title = project_data.get("title", "Untitled Project")
        filename = f"{title.lower().replace(' ', '_')}.yaml"
        file_path = os.path.join(self.projects_dir, filename)
        
        with open(file_path, 'w') as f:
            yaml.dump(project_data, f, default_flow_style=False, sort_keys=False) 