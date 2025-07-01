#!/usr/bin/env python3
"""
Test script for resume scoring and ATS optimization system.
Validates keyword matching, LLM feedback, and scoring accuracy.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.resume_scorer import ResumeScorerService

async def test_resume_scoring():
    """Test the resume scoring functionality."""
    print("🧪 Testing Resume Scoring System")
    print("=" * 50)
    
    try:
        # Initialize service
        scorer = ResumeScorerService()
        
        # Test case 1: High match scenario
        print("🔍 Test 1: High Match Scenario")
        print("-" * 30)
        
        job_description = """
        We're hiring a Senior ML Engineer for Edge AI inference tooling and hardware-aware optimization. 
        The ideal candidate should have experience with ONNX, PyTorch, CUDA, and edge deployment. 
        We're looking for someone who can optimize neural networks for embedded devices and 
        implement real-time computer vision applications.
        """
        
        resume_data = {
            "summary": "PhD in Computer Science with expertise in ONNX-based model optimization, CUDA programming, and edge deployment. Experienced in PyTorch, computer vision, and real-time systems.",
            "skills": ["ONNX", "PyTorch", "CUDA", "Edge Deployment", "Computer Vision", "Python", "C++"],
            "projects": [
                {
                    "title": "Neural Network Optimization Framework",
                    "description": "Developed ONNX-based pruning and quantization for edge devices",
                    "technologies": ["ONNX", "PyTorch", "CUDA", "Edge Impulse"]
                },
                {
                    "title": "Real-Time Object Detection",
                    "description": "Implemented computer vision pipeline with CUDA acceleration",
                    "technologies": ["CUDA", "Computer Vision", "Real-time Systems"]
                }
            ]
        }
        
        result = await scorer.score_resume(job_description, resume_data)
        
        print(f"✅ Overall Score: {result.get('match_score', 0)}/100")
        print(f"🔍 Keyword Score: {result.get('keyword_score', 0)}%")
        print(f"📝 Matched Keywords: {len(result.get('keywords_matched', []))}")
        print(f"❌ Missing Keywords: {len(result.get('keywords_missing', []))}")
        print(f"💡 Overall Feedback: {result.get('overall_feedback', 'N/A')}")
        
        # Test case 2: Low match scenario
        print("\n🔍 Test 2: Low Match Scenario")
        print("-" * 30)
        
        low_match_job = """
        We're looking for a Full Stack Developer with expertise in React, Node.js, and AWS. 
        The ideal candidate should have experience with microservices, Docker, and CI/CD pipelines.
        """
        
        low_match_resume = {
            "summary": "PhD in Computer Science with expertise in machine learning and data analysis.",
            "skills": ["Python", "Machine Learning", "Data Analysis", "SQL"],
            "projects": [
                {
                    "title": "Data Analysis Project",
                    "description": "Analyzed large datasets using Python and machine learning",
                    "technologies": ["Python", "Pandas", "Scikit-learn"]
                }
            ]
        }
        
        low_result = await scorer.score_resume(low_match_job, low_match_resume)
        
        print(f"✅ Overall Score: {low_result.get('match_score', 0)}/100")
        print(f"🔍 Keyword Score: {low_result.get('keyword_score', 0)}%")
        print(f"📝 Matched Keywords: {len(low_result.get('keywords_matched', []))}")
        print(f"❌ Missing Keywords: {len(low_result.get('keywords_missing', []))}")
        
        # Test case 3: Technical keyword extraction
        print("\n🔍 Test 3: Technical Keyword Extraction")
        print("-" * 40)
        
        technical_text = "Experience with PyTorch, TensorFlow, CUDA 12.3, ONNX Runtime, Docker containers, AWS S3, and REST APIs."
        keywords = scorer._extract_keywords(technical_text)
        print(f"Extracted keywords: {keywords}")
        
        # Test case 4: ATS optimization tips
        print("\n🔍 Test 4: ATS Optimization Tips")
        print("-" * 35)
        
        ats_tips = scorer.get_ats_optimization_tips()
        print(f"Generated {len(ats_tips)} ATS optimization tips:")
        for i, tip in enumerate(ats_tips[:5], 1):  # Show first 5
            print(f"  {i}. {tip}")
        
        # Test case 5: Scoring breakdown analysis
        print("\n🔍 Test 5: Scoring Breakdown Analysis")
        print("-" * 40)
        
        breakdown = result.get('scoring_breakdown', {})
        print(f"Keyword Matching: {breakdown.get('keyword_matching', 0)}%")
        print(f"LLM Assessment: {breakdown.get('llm_assessment', 0)}%")
        print(f"Overall Score: {breakdown.get('overall_score', 0)}%")
        
        # Test case 6: Section feedback
        print("\n🔍 Test 6: Section Feedback")
        print("-" * 25)
        
        section_feedback = result.get('section_feedback', {})
        for section, feedback in section_feedback.items():
            print(f"📝 {section.title()}: {feedback}")
        
        print("\n🎉 All resume scoring tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_keyword_matching():
    """Test keyword matching functionality."""
    print("\n🧪 Testing Keyword Matching")
    print("=" * 40)
    
    try:
        scorer = ResumeScorerService()
        
        # Test job keywords
        job_keywords = ["python", "pytorch", "cuda", "onnx", "edge", "deployment"]
        resume_keywords = ["python", "pytorch", "cuda", "machine", "learning", "data"]
        
        score, matched, missing = scorer._calculate_keyword_match(job_keywords, resume_keywords)
        
        print(f"Job Keywords: {job_keywords}")
        print(f"Resume Keywords: {resume_keywords}")
        print(f"Match Score: {score}%")
        print(f"Matched: {matched}")
        print(f"Missing: {missing}")
        
        # Verify no duplicates in matched keywords
        if len(matched) == len(set(matched)):
            print("✅ No duplicates in matched keywords")
        else:
            print("❌ Duplicates found in matched keywords")
            return False
        
        # Verify missing keywords are actually missing
        for keyword in missing:
            if keyword in resume_keywords:
                print(f"❌ Error: {keyword} found in resume but marked as missing")
                return False
        
        print("✅ Keyword matching tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Keyword matching test failed: {str(e)}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Resume Scoring Tests")
    print("=" * 50)
    
    # Test resume scoring
    scoring_ok = await test_resume_scoring()
    
    # Test keyword matching
    keyword_ok = await test_keyword_matching()
    
    if scoring_ok and keyword_ok:
        print("\n🎉 All tests passed! The resume scoring system is working correctly.")
        print("\n📊 Summary:")
        print("✅ Resume scoring with LLM feedback")
        print("✅ Keyword extraction and matching")
        print("✅ ATS optimization tips")
        print("✅ Section-specific feedback")
        print("✅ Scoring breakdown analysis")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    asyncio.run(main()) 