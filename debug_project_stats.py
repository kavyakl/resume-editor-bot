#!/usr/bin/env python3
"""
Debug script to test project statistics directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.project_store import ProjectStoreService
from app.core.config import settings

def test_project_statistics():
    """Test project statistics directly"""
    
    print("Testing project statistics...")
    
    try:
        # Check if projects directory exists
        projects_dir = settings.paths.projects_dir
        print(f"Projects directory: {projects_dir}")
        print(f"Directory exists: {os.path.exists(projects_dir)}")
        
        if os.path.exists(projects_dir):
            project_files = [f for f in os.listdir(projects_dir) if f.endswith(('.yaml', '.yml'))]
            print(f"Project files found: {len(project_files)}")
            print(f"Files: {project_files}")
        
        # Test project store service
        ps = ProjectStoreService()
        projects = ps.get_all_projects()
        print(f"Projects loaded: {len(projects)}")
        
        # Test statistics
        stats = ps.get_project_statistics()
        print(f"Statistics: {stats}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_project_statistics() 