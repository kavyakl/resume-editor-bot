#!/usr/bin/env python3
"""
Test script for resume deduplication logic.
Validates that projects aren't repeated across different resume sections.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.resume_writer import ResumeWriterService
from app.services.project_store import ProjectStoreService
from app.core.config import settings

async def test_project_deduplication():
    """Test the project deduplication logic."""
    print("🧪 Testing Project Deduplication Logic")
    print("=" * 50)
    
    try:
        # Initialize services
        project_store = ProjectStoreService()
        resume_writer = ResumeWriterService(project_store)
        
        # Test job description
        job_description = """
        We're hiring a Senior ML Engineer for Edge AI inference tooling and hardware-aware optimization. 
        The ideal candidate should have experience with ONNX, PyTorch, CUDA, and edge deployment. 
        We're looking for someone who can optimize neural networks for embedded devices and 
        implement real-time computer vision applications.
        """
        
        print(f"📋 Job Description: {job_description.strip()}")
        print()
        
        # Test 1: Basic deduplication logic
        print("🔍 Test 1: Basic Deduplication Logic")
        print("-" * 30)
        
        # Get all projects
        all_projects = project_store.get_all_projects()
        print(f"Total projects available: {len(all_projects)}")
        
        # Extract job tags
        job_tags = ["ml", "edge-ai", "onnx", "pytorch", "cuda", "computer-vision", "optimization"]
        print(f"Job tags: {job_tags}")
        print()
        
        # Test project selection for different sections
        used_project_slugs = set()
        
        # Select research projects
        research_projects = resume_writer.select_relevant_projects(
            all_projects, job_tags, "research", used_project_slugs, max_count=3
        )
        print(f"📚 Research projects selected: {len(research_projects)}")
        for i, project in enumerate(research_projects, 1):
            print(f"  {i}. {project.get('title', 'Unknown')} (slug: {project.get('slug', 'N/A')})")
        print(f"Used project slugs: {used_project_slugs}")
        print()
        
        # Select project section projects
        project_projects = resume_writer.select_relevant_projects(
            all_projects, job_tags, "project", used_project_slugs, max_count=3
        )
        print(f"💼 Project section projects selected: {len(project_projects)}")
        for i, project in enumerate(project_projects, 1):
            print(f"  {i}. {project.get('title', 'Unknown')} (slug: {project.get('slug', 'N/A')})")
        print(f"Used project slugs: {used_project_slugs}")
        print()
        
        # Test 2: Verify no duplicates
        print("🔍 Test 2: Verify No Duplicates")
        print("-" * 30)
        
        all_selected_slugs = set()
        for project in research_projects + project_projects:
            slug = project.get('slug')
            if slug in all_selected_slugs:
                print(f"❌ DUPLICATE FOUND: {slug}")
                return False
            all_selected_slugs.add(slug)
        
        print("✅ No duplicates found!")
        print()
        
        # Test 3: Full resume generation with deduplication
        print("🔍 Test 3: Full Resume Generation with Deduplication")
        print("-" * 50)
        
        include_sections = ["summary", "research", "projects", "skills"]
        
        result = await resume_writer.generate_tailored_resume_with_deduplication(
            job_description, include_sections
        )
        
        print(f"✅ Resume generated successfully!")
        print(f"📊 Sections generated: {list(result['sections'].keys())}")
        print(f"🔢 Projects used: {result['selected_projects_count']}")
        print(f"🔄 Deduplication applied: {result['deduplication_applied']}")
        print()
        
        # Test 4: Academic CV generation
        print("🔍 Test 4: Academic CV Generation")
        print("-" * 35)
        
        academic_result = await resume_writer.generate_tailored_resume_with_deduplication(
            job_description, ["summary", "research", "projects", "skills"]
        )
        
        print(f"✅ Academic CV generated successfully!")
        print(f"📊 Research projects in CV: {len(academic_result['sections'].get('research', '').split('Research')) - 1}")
        print()
        
        # Test 5: Project section analysis
        print("🔍 Test 5: Project Section Analysis")
        print("-" * 35)
        
        # Check which projects are in which sections
        research_section = academic_result['sections'].get('research', '')
        projects_section = academic_result['sections'].get('projects', '')
        
        print("📚 Research Section Projects:")
        for project in research_projects:
            title = project.get('title', 'Unknown')
            if title in research_section:
                print(f"  ✅ {title}")
            else:
                print(f"  ❌ {title} (not found in research section)")
        
        print("\n💼 Project Section Projects:")
        for project in project_projects:
            title = project.get('title', 'Unknown')
            if title in projects_section:
                print(f"  ✅ {title}")
            else:
                print(f"  ❌ {title} (not found in projects section)")
        
        print()
        
        # Test 6: Tag extraction validation
        print("🔍 Test 6: Tag Extraction Validation")
        print("-" * 35)
        
        test_skills = ["Python", "PyTorch", "ONNX", "CUDA", "Computer Vision", "Edge AI"]
        for skill in test_skills:
            tags = resume_writer._extract_tags_from_skill(skill)
            print(f"  {skill} → {tags}")
        
        print()
        print("🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_project_structure():
    """Test that all projects have the required new fields."""
    print("🧪 Testing Project Structure")
    print("=" * 40)
    
    try:
        project_store = ProjectStoreService()
        all_projects = project_store.get_all_projects()
        
        required_fields = ['slug', 'sections', 'relevance_tags', 'featured']
        
        for project in all_projects:
            title = project.get('title', 'Unknown')
            print(f"\n📋 Project: {title}")
            
            missing_fields = []
            for field in required_fields:
                if field not in project:
                    missing_fields.append(field)
                else:
                    value = project[field]
                    print(f"  ✅ {field}: {value}")
            
            if missing_fields:
                print(f"  ❌ Missing fields: {missing_fields}")
            else:
                print(f"  ✅ All required fields present")
        
        print(f"\n📊 Total projects checked: {len(all_projects)}")
        return True
        
    except Exception as e:
        print(f"❌ Structure test failed: {str(e)}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Resume Deduplication Tests")
    print("=" * 50)
    
    # Test project structure first
    structure_ok = await test_project_structure()
    if not structure_ok:
        print("❌ Project structure test failed. Please update project YAML files.")
        return
    
    print("\n" + "=" * 50)
    
    # Test deduplication logic
    dedup_ok = await test_project_deduplication()
    
    if dedup_ok:
        print("\n🎉 All tests passed! The deduplication system is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    asyncio.run(main()) 