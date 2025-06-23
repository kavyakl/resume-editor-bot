#!/usr/bin/env python3
"""
Test script for the project-based resume generation system.
Run this to verify all components are working correctly.
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our services
from app.services.project_store import ProjectStoreService
from app.services.project_parser import ProjectParserService
from app.core.job_parser import JobParserService
from app.services.relevance_ranker import RelevanceRankerService
from app.services.resume_writer import ResumeWriterService

async def test_project_store():
    """Test project store functionality."""
    print("🔍 Testing Project Store...")
    
    try:
        store = ProjectStoreService()
        
        # Load all projects
        projects = store.load_all_projects()
        print(f"✅ Loaded {len(projects)} projects")
        
        # Get statistics
        stats = store.get_project_statistics()
        print(f"✅ Project statistics: {stats['total_projects']} total projects")
        print(f"   Most common technologies: {stats['most_common_technologies']}")
        
        # Search projects
        search_results = store.search_projects("machine learning", limit=3)
        print(f"✅ Search results: {len(search_results)} projects found for 'machine learning'")
        
        return True
        
    except Exception as e:
        print(f"❌ Project store test failed: {str(e)}")
        return False

async def test_project_parser():
    """Test project parser functionality."""
    print("\n🔍 Testing Project Parser...")
    
    try:
        parser = ProjectParserService()
        
        # Test parsing a project dump
        sample_dump = """
        I worked on a computer vision project for autonomous vehicles. 
        Used Python, OpenCV, and TensorFlow to develop object detection models. 
        Achieved 90% accuracy on pedestrian detection and reduced false positives by 30%. 
        The system was deployed on NVIDIA Jetson devices and processed real-time video streams.
        """
        
        project_data = await parser.parse_project_dump(sample_dump, "Autonomous Vehicle CV")
        print(f"✅ Parsed project: {project_data.get('title', 'Unknown')}")
        print(f"   Technologies: {project_data.get('technologies', [])}")
        print(f"   Results: {project_data.get('results', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Project parser test failed: {str(e)}")
        return False

async def test_job_parser():
    """Test job parser functionality."""
    print("\n🔍 Testing Job Parser...")
    
    try:
        parser = JobParserService()
        
        # Test parsing a job description
        sample_job = """
        We are looking for a Machine Learning Engineer to join our team.
        Required skills: Python, TensorFlow, PyTorch, AWS, Docker
        Preferred skills: ONNX, Edge deployment, MLOps
        Experience with model optimization and deployment is required.
        """
        
        job_data = await parser.parse_job_description(sample_job)
        print(f"✅ Parsed job: {job_data.get('job_title', 'Unknown')}")
        print(f"   Required skills: {job_data.get('required_skills', [])}")
        print(f"   Preferred skills: {job_data.get('preferred_skills', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Job parser test failed: {str(e)}")
        return False

async def test_relevance_ranker():
    """Test relevance ranker functionality."""
    print("\n🔍 Testing Relevance Ranker...")
    
    try:
        ranker = RelevanceRankerService()
        
        # Create vector store
        await ranker.create_project_vector_store()
        print("✅ Created project vector store")
        
        # Test ranking projects
        sample_job = "Machine Learning Engineer position requiring Python, TensorFlow, and model optimization experience."
        ranked_projects = await ranker.rank_projects_for_job(sample_job, top_k=3)
        print(f"✅ Ranked {len(ranked_projects)} projects")
        
        if ranked_projects:
            top_project = ranked_projects[0]
            print(f"   Top project: {top_project.get('title', 'Unknown')}")
            print(f"   Relevance score: {top_project.get('relevance_score', 0):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Relevance ranker test failed: {str(e)}")
        return False

async def test_resume_writer():
    """Test resume writer functionality."""
    print("\n🔍 Testing Resume Writer...")
    
    try:
        writer = ResumeWriterService()
        
        # Test generating a resume section
        sample_job = "Machine Learning Engineer position focusing on model optimization and edge deployment."
        
        # Get ranked projects first
        ranker = RelevanceRankerService()
        await ranker.create_project_vector_store()
        ranked_projects = await ranker.rank_projects_for_job(sample_job, top_k=5)
        
        # Generate experience section
        experience_section = await writer.generate_resume_section(
            "Experience", ranked_projects, sample_job, "experience"
        )
        print("✅ Generated experience section")
        print(f"   Length: {len(experience_section)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Resume writer test failed: {str(e)}")
        return False

async def test_end_to_end():
    """Test the complete end-to-end workflow."""
    print("\n🔍 Testing End-to-End Workflow...")
    
    try:
        # Sample job description
        job_description = """
        Senior Machine Learning Engineer
        We are seeking a talented ML Engineer to join our AI team.
        Required: Python, TensorFlow, PyTorch, AWS, Docker, model optimization
        Preferred: ONNX, edge deployment, MLOps, Kubernetes
        Experience with computer vision and real-time systems is a plus.
        """
        
        # Generate complete tailored resume
        writer = ResumeWriterService()
        resume = await writer.generate_tailored_resume(
            job_description,
            candidate_skills=["Python", "TensorFlow", "PyTorch", "AWS", "Docker"],
            include_sections=["summary", "experience", "skills"]
        )
        
        print("✅ Generated complete tailored resume")
        print(f"   Sections: {list(resume['sections'].keys())}")
        print(f"   Ranked projects: {len(resume['ranked_projects'])}")
        
        # Show a sample section
        if "summary" in resume["sections"]:
            summary = resume["sections"]["summary"]
            print(f"   Summary preview: {summary[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ End-to-end test failed: {str(e)}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Project-Based Resume Generation System Tests\n")
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable is not set!")
        print("Please set your OpenAI API key in the .env file")
        return
    
    tests = [
        test_project_store,
        test_project_parser,
        test_job_parser,
        test_relevance_ranker,
        test_resume_writer,
        test_end_to_end
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
            results.append(False)
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Results Summary")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! The system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("\n📝 Next Steps:")
    print("1. Start the FastAPI server: uvicorn main:app --reload")
    print("2. Visit http://localhost:8000/docs for API documentation")
    print("3. Use the new project-based endpoints to generate tailored resumes")

if __name__ == "__main__":
    asyncio.run(main()) 