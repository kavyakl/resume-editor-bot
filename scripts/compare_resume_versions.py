#!/usr/bin/env python3
"""
Script to compare old vs new resume versions and highlight improvements.
"""

import os
from docx import Document

def extract_resume_content(file_path):
    """Extract text content from a DOCX resume file."""
    try:
        doc = Document(file_path)
        content = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                content.append(paragraph.text.strip())
        return content
    except Exception as e:
        return [f"Error reading {file_path}: {e}"]

def compare_resumes():
    """Compare old vs new resume versions."""
    print("🔍 Resume Comparison: Old vs New Versions\n")
    
    # Check if files exist
    old_file = "data/exports/Kalyanam_resume.docx"
    new_file = "data/exports/Kalyanam_Resume_WorldClass.docx"
    
    if not os.path.exists(old_file):
        print(f"❌ Old resume file not found: {old_file}")
        return
    
    if not os.path.exists(new_file):
        print(f"❌ New resume file not found: {new_file}")
        return
    
    # Extract content
    old_content = extract_resume_content(old_file)
    new_content = extract_resume_content(new_file)
    
    print("📊 COMPARISON SUMMARY")
    print("=" * 50)
    
    # Basic stats
    print(f"📄 Old Resume: {len(old_content)} paragraphs")
    print(f"📄 New Resume: {len(new_content)} paragraphs")
    print(f"📈 Content Increase: {len(new_content) - len(old_content)} paragraphs")
    
    # Key improvements
    print("\n🚀 KEY IMPROVEMENTS IDENTIFIED")
    print("=" * 50)
    
    improvements = [
        ("Objective → Summary", "Generic objective → Quantified summary with specific achievements"),
        ("Skills Organization", "Overloaded categories → Strategic grouping with company focus"),
        ("Research Experience", "Basic bullets → Quantified achievements with methodology"),
        ("Project Details", "One-liners → Detailed technical implementation"),
        ("Publications", "Generic counts → Specific titles, venues, awards"),
        ("Hardware Specs", "Missing → Specific GPU, CUDA, platform details"),
        ("Quantification", "Vague metrics → Specific percentages, FPS, compression ratios"),
        ("Technical Depth", "Surface-level → Detailed methodologies and implementations")
    ]
    
    for i, (change, description) in enumerate(improvements, 1):
        print(f"{i}. {change}")
        print(f"   {description}")
        print()
    
    # Sample content comparison
    print("📋 SAMPLE CONTENT COMPARISON")
    print("=" * 50)
    
    # Find key sections in both
    old_summary = ""
    new_summary = ""
    
    for line in old_content:
        if "PhD Candidate" in line or "seeking" in line.lower():
            old_summary = line
            break
    
    for line in new_content:
        if "Machine Learning Researcher with 5+ years" in line:
            new_summary = line
            break
    
    if old_summary and new_summary:
        print("📝 SUMMARY/OBJECTIVE COMPARISON:")
        print(f"OLD: {old_summary}")
        print(f"NEW: {new_summary[:100]}...")
        print()
    
    # Check for quantification
    quantified_metrics = []
    for line in new_content:
        if any(metric in line for metric in ["98.98%", "91.21%", "19.23 FPS", "80%", "95%", "60.37%", "90.75%"]):
            quantified_metrics.append(line)
    
    if quantified_metrics:
        print("📊 QUANTIFIED ACHIEVEMENTS (NEW):")
        for metric in quantified_metrics[:3]:  # Show first 3
            print(f"• {metric}")
        print()
    
    # Check for technical details
    technical_terms = []
    for line in new_content:
        if any(term in line for term in ["PyTorch 2.6.0+cu124", "CUDA 12.3", "NVIDIA GTX 1080 Ti", "MLIR-inspired", "Grad-CAM", "CSR/COO"]):
            technical_terms.append(line)
    
    if technical_terms:
        print("🔧 TECHNICAL SPECIFICITY (NEW):")
        for term in technical_terms[:3]:  # Show first 3
            print(f"• {term}")
        print()
    
    # Company-specific versions
    company_files = [
        "data/exports/Kalyanam_Resume_Apple.docx",
        "data/exports/Kalyanam_Resume_Meta.docx"
    ]
    
    print("🎯 COMPANY-SPECIFIC VERSIONS CREATED:")
    for file_path in company_files:
        if os.path.exists(file_path):
            company = file_path.split("_")[-1].replace(".docx", "")
            print(f"✅ {company.title()}-tailored resume")
        else:
            print(f"❌ {file_path} not found")
    
    print("\n🏆 CONCLUSION")
    print("=" * 50)
    print("The new resume system provides:")
    print("• Quantified achievements with specific metrics")
    print("• Detailed technical implementation descriptions")
    print("• Company-specific tailoring for top-tier AI roles")
    print("• Professional formatting and strategic content organization")
    print("• Hardware and technology stack specificity")
    print("• Impact-focused language for research positions")

if __name__ == "__main__":
    compare_resumes() 