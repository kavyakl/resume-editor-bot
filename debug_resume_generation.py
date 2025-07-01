#!/usr/bin/env python3
"""
Debug script to test resume generation API endpoint
"""

import requests
import json
import time

def test_resume_generation():
    """Test the resume generation endpoint directly"""
    
    # Test data
    test_data = {
        "job_description": "We are looking for a Machine Learning Engineer with experience in Python, PyTorch, and ONNX optimization. The ideal candidate should have experience with edge AI deployment and model optimization techniques.",
        "include_sections": ["summary", "experience"],
        "max_projects_per_section": 4
    }
    
    print("Testing resume generation API...")
    print(f"Request data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Test the endpoint
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/api/generate-deduplicated-resume",
            json=test_data,
            timeout=60  # 60 second timeout
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Resume generated successfully")
            print(f"Generated sections: {list(result.get('sections', {}).keys())}")
            print(f"Deduplication applied: {result.get('deduplication_applied', False)}")
            print(f"Projects used: {result.get('selected_projects_count', 0)}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: Request took too long")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to server")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def test_project_statistics():
    """Test the project statistics endpoint"""
    
    print("\nTesting project statistics API...")
    
    try:
        response = requests.get(
            "http://localhost:8000/api/projects/statistics",
            timeout=10
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Project statistics retrieved")
            print(f"Total projects: {result.get('total_projects', 0)}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("=== Resume Generation Debug Test ===\n")
    
    # Test project statistics first
    test_project_statistics()
    
    # Test resume generation
    test_resume_generation()
    
    print("\n=== Debug Test Complete ===") 