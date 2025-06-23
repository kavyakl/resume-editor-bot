#!/usr/bin/env python3
"""
Script to create a concise resume matching the Kalyanam_resume.docx template format.
"""

import requests
import argparse
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_horizontal_line(doc):
    """Adds a full-width horizontal line with minimal spacing."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(2)
    p_pr = p._p.get_or_add_pPr()
    p_bdr = OxmlElement('w:pBdr')
    p_pr.append(p_bdr)
    bdr_bottom = OxmlElement('w:bottom')
    bdr_bottom.set(qn('w:val'), 'single')
    bdr_bottom.set(qn('w:sz'), '4')
    bdr_bottom.set(qn('w:space'), '1')
    bdr_bottom.set(qn('w:color'), 'auto')
    p_bdr.append(bdr_bottom)

def add_section_heading(doc, text):
    """Helper to add a styled heading using a normal paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    set_run_font(p.add_run(text), bold=True, size_pt=11)

def set_run_font(run, bold=False, italic=False, size_pt=10.5):
    """Helper to set font properties on a run."""
    run.font.name = 'Times New Roman'
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic

def build_resume(generated_data):
    """Builds the final resume DOCX from a template and generated content."""
    doc = Document()
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(10.5)
    style.paragraph_format.line_spacing = 1.0
    style.paragraph_format.space_before = Pt(0)
    style.paragraph_format.space_after = Pt(1)

    # --- Header ---
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(0)
    set_run_font(p.add_run("Lakshmi Kavya Kalyanam"), bold=True, size_pt=16)
    
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(title_p.add_run("PhD in Deep Learning | Embedded ML | GenAI Systems | Edge AI"), bold=True, size_pt=11)

    contact_p = doc.add_paragraph()
    contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_p.add_run("Tampa, FL · +1-813-609-9796 · kavyakalyanamk@gmail.com\n")
    contact_p.add_run("linkedin.com/in/lakshmikavya-kalyanam-a88633131 · github.com/your-github-profile") # Placeholder GitHub
    add_horizontal_line(doc)

    # --- Objective ---
    add_section_heading(doc, "Objective")
    p = doc.add_paragraph(
        "PhD in Computer Science with expertise in deep neural network optimization, GenAI, and embedded AI deployment. Seeking applied ML/LLM roles focused on scalable GenAI systems, efficient model inference, and real-world deployment."
    )
    p.paragraph_format.space_after = Pt(0)
    add_horizontal_line(doc)

    # --- Technical Skills (Dynamic) ---
    add_section_heading(doc, "Technical Skills")
    skills_text = generated_data.get("sections", {}).get("skills", "")
    for line in skills_text.split('\n'):
        line = line.strip()
        if ':' in line:
            category, skill_list = line.split(':', 1)
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            set_run_font(p.add_run(f"{category.strip()}: "), bold=True)
            p.add_run(skill_list.strip())
    add_horizontal_line(doc)
    
    # --- Research Experience (Dynamic) ---
    add_section_heading(doc, "Research Experience")
    p = doc.add_paragraph()
    set_run_font(p.add_run("PhD Researcher"), bold=True)
    p.add_run(", University of South Florida — ")
    set_run_font(p.add_run("Tampa, FL"), italic=True)
    p.paragraph_format.space_after = Pt(0)
    doc.add_paragraph("2019 – Present", style='Normal').paragraph_format.space_after = Pt(2)
    
    experience_highlights = generated_data.get("sections", {}).get("research_experience", "")
    for line in experience_highlights.split('\n'):
        # Clean up the line from AI artifacts
        line = line.strip().lstrip('*-• ').strip() # General bullets
        if line and line[0].isdigit() and (line[1] == '.' or line[1] == ')'):
             line = line[2:].lstrip() # Numbered lists like "1." or "1)"
        line = line.strip('"') # Double quotes

        if not line:
            continue
        p = doc.add_paragraph(style='List Bullet')
        parts = line.split('**')
        is_bold = False
        for part in parts:
            if part:
                set_run_font(p.add_run(part), bold=is_bold)
            is_bold = not is_bold
    add_horizontal_line(doc)

    # --- Education ---
    add_section_heading(doc, "Education")
    
    p = doc.add_paragraph()
    set_run_font(p.add_run("Ph.D., Computer Science"), bold=True)
    p.add_run(" — ")
    set_run_font(p.add_run("University of South Florida"), italic=True)
    p.add_run(" (Expected 2025)")
    doc.add_paragraph("Focus: Neural network compression, dynamic sparsity, embedded ML deployment", style='List Bullet')

    p = doc.add_paragraph()
    set_run_font(p.add_run("M.S., Computer Science"), bold=True)
    p.add_run(" — ")
    set_run_font(p.add_run("University of South Florida"), italic=True)
    p.add_run(" (2020)")
    doc.add_paragraph("Thesis: Real-time object detection using BNNs on PYNQ-Z1 (19.23 FPS)", style='List Bullet')

    p = doc.add_paragraph()
    set_run_font(p.add_run("B.Tech., Electronics & Communication Engineering"), bold=True)
    p.add_run(" — ")
    set_run_font(p.add_run("GITAM University"), italic=True)
    p.add_run(" (2017)")
    add_horizontal_line(doc)
    
    # --- Patents ---
    add_section_heading(doc, "Patents")
    patents = [
        ("Layer-Wise Filter Thresholding Based CNN Pruning for Efficient IoT Edge Implementations", 
         "US Provisional Application No. 63/552,084 | Filed: Feb 9, 2024 | USF Ref: 24T085US"),
        ("Unstructured Pruning for Multi-Layer Perceptrons with Tanh Activation",
         "Invention ID: USF23/00331 | USF Tech ID: 24T063"),
        ("Range-Based Hardware Optimization of Multi-Layer Perceptrons with ReLUs",
         "USF Tech Ref: 23T078US | Q&B Ref: 173738.02709")
    ]
    for title, detail_text in patents:
        p = doc.add_paragraph(style='List Bullet')
        set_run_font(p.add_run(title), bold=True)
        p.add_run(f": {detail_text}")

    # --- Save ---
    output_path = "data/exports/Kalyanam_Resume_Final.docx"
    doc.save(output_path)
    return output_path

def main():
    """Main function to generate the final resume."""
    parser = argparse.ArgumentParser(description="Generate a tailored resume.")
    parser.add_argument(
        "job_description",
        type=str,
        nargs='?',
        default="An applied ML/LLM role with a focus on scalable GenAI systems, model optimization, and deployment on edge devices.",
        help="The job description to tailor the resume to."
    )
    args = parser.parse_args()

    try:
        print("Requesting tailored content for resume sections...")
        response = requests.post(
            "http://localhost:8000/api/generate-tailored-resume",
            json={
                "job_description": args.job_description,
                "include_sections": ["skills", "research_experience"]
            }
        )
        response.raise_for_status()
        generated_data = response.json()
        
        print("Building final resume document...")
        output_file = build_resume(generated_data)
        print(f"\n✅ Success! Final resume created at: {output_file}")
    
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP Error: {http_err}")
        print(f"Response body: {response.text}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main() 