#!/usr/bin/env python3
"""
Script to create a concise resume matching the Kalyanam_resume.docx template format.
"""

import requests
import argparse
import time
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

def parse_and_add_text(p, text):
    """Parses text with simple **bold** markup and adds it to a paragraph."""
    parts = text.split('**')
    is_bold = False
    for part in parts:
        if part:
            set_run_font(p.add_run(part), bold=is_bold)
        is_bold = not is_bold

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
    contact_p.add_run("Tampa, FL · +1-813-609-9796 · kavyakalyanamk@gmail.com")
    contact_p.add_run("\n")
    contact_p.add_run("linkedin.com/in/lakshmikavya-kalyanam-a88633131 · github.com/kavyakl")
    contact_p.add_run("\n")
    set_run_font(contact_p.add_run("US Work Authorization | Open to Relocation"), italic=True)
    # Removed add_horizontal_line(doc) here for cleaner header

    # --- Objective (Dynamic) ---
    add_section_heading(doc, "Objective")
    objective_text = (
        "PhD Candidate and Research Engineer specializing in Embedded AI, Computer Vision, and GenAI Systems. "
        "Actively seeking a full-time research or engineering position in Computer Vision, GenAI, or Embedded AI."
    )
    doc.add_paragraph(objective_text)
    # Add a horizontal line above Technical Skills for separation
    add_horizontal_line(doc)
    # --- Technical Skills (Grouped, Bolded) ---
    add_section_heading(doc, "Technical Skills")
    skills_lines = [
        ("Languages", "Python, C++17, Embedded C, Shell, CUDA, VHDL"),
        ("Frameworks", "PyTorch, TensorFlow, TFLite, ONNX, HuggingFace, FastAI"),
        ("Optimization", "Pruning (structured/unstructured), Quantization, RigL, XAI"),
        ("Computer Vision", "CNNs, BNNs, ViTs, image-text modeling"),
        ("GenAI & RAG", "FAISS, ElasticSearch, LangChain, RAG pipelines, LLM fine-tuning, OpenAI APIs"),
        ("Embedded Systems", "Arduino, NodeMCU, PYNQ-Z1, Virtex-7, Edge Impulse"),
        ("Compiler-Aware Deployment", "ONNX graph rewrites, IR transforms, MLIR-inspired optimization"),
        ("Tooling", "Vivado, HSPICE, Virtuoso, Git, Jupyter, MATLAB, Linux CLI, pytest"),
        ("Profiling & Inference", "Latency/power profiling, QAT, firmware integration, CI/CD")
    ]
    for category, skills in skills_lines:
        p = doc.add_paragraph()
        set_run_font(p.add_run(f"{category}: "), bold=True)
        p.add_run(skills)
    
    add_horizontal_line(doc)
    
    # --- Research Experience (Chronological, Process-Oriented) ---
    add_section_heading(doc, "Research Experience")
    research_roles = [
        {
            "role": "PhD Researcher",
            "institution": "University of South Florida",
            "dates": "2019–Present",
            "bullets": [
                "Built end-to-end optimization pipeline for DNN pruning, quantization, and deployment on ARM MCUs and FPGAs.",
                "Simulated ONNX graph rewrites to mimic IR compiler passes for sparse model deployment.",
                "Deployed real-time inference on Arduino MKR1000, NodeMCU, and PYNQ-Z1 with quantized/pruned models."
            ]
        }
    ]
    for role in research_roles:
        p = doc.add_paragraph()
        set_run_font(p.add_run(f"{role['role']}, {role['institution']} ({role['dates']})"), bold=True)
        for bullet in role["bullets"]:
            doc.add_paragraph(bullet, style="List Bullet")
    add_horizontal_line(doc)

    # --- Applied Research Highlights (Thematic, Impact-Oriented) ---
    add_section_heading(doc, "Applied Research Highlights")
    highlights = [
        ("Activation-Aware MLP Pruning", "Achieved 82% sparsity and 37% hardware savings with <1.5% accuracy loss by designing activation-aware pruning strategies for MLPs."),
        ("Real-Time Edge Deployment", "Enabled sub-200 ms inference and 60% memory reduction by deploying optimized DNNs on Arduino MKR1000 and NodeMCU."),
        ("RigL-Based Sparse CNN Training", "Achieved 91.5% weight sparsity and 4× FLOP reduction on VGG-11 with 90.53% accuracy on CIFAR-10 using dynamic sparsity scheduling."),
        ("Vision Transformers for Embedded CV", "Outperformed CNNs on Fashion-MNIST and CIFAR-10 in generalization and robustness by designing ViTs for low-data regimes."),
        ("RAG Pipelines for Literature Summarization", "Improved factuality and review coverage by 80% by building FAISS + LLM-powered RAG pipelines to summarize 500+ scientific papers."),
        ("ONNX Compiler Pass Simulation", "Enabled compile-time-aware model optimization by implementing graph-level transformations (pruning, quantization) simulating compiler IR behavior.")
    ]
    for title, desc in highlights:
        p = doc.add_paragraph()
        set_run_font(p.add_run(f"{title} – "), bold=True)
        p.add_run(desc)
    add_horizontal_line(doc)

    # --- Projects Section (One-liner + GitHub) ---
    add_section_heading(doc, "Projects")
    projects = [
        {
            "name": "LitBot – AI Literature Survey Assistant",
            "summary": "Semantic search + summarization assistant using GPT + FAISS. Cut paper review time by 80%.",
            "github": "github.com/kavyakl/litnet"
        },
        {
            "name": "Distributed Real-Time Object Detection Framework",
            "summary": "BNN-based image classifier for distributed IoT edge nodes. Real-time detection at low frame rates.",
            "github": None
        },
        {
            "name": "RAG-Based Neural Network Pruning Analysis Tool",
            "summary": "GenAI assistant for analyzing DNN pruning results. Performs insight generation, clustering, and performance comparison across model variants.",
            "github": "github.com/kavyakl/RAG-Based-Neural-Network-Optimization"
        }
    ]
    for proj in projects:
        p = doc.add_paragraph()
        set_run_font(p.add_run(proj["name"]), bold=True)
        doc.add_paragraph(proj["summary"])
        if proj.get("github"):
            doc.add_paragraph(f"🔗 {proj['github']}")
    add_horizontal_line(doc)

    # --- Education ---
    add_section_heading(doc, "Education")
    
    p = doc.add_paragraph()
    set_run_font(p.add_run("Ph.D., Computer Science"), bold=True)
    p.add_run(" — ")
    set_run_font(p.add_run("University of South Florida"), italic=True)
    p.add_run(" (Expected 2025)")
    doc.add_paragraph("Focus: Neural network compression, dynamic sparsity, embedded ML deployment", style='List Bullet')
    doc.add_paragraph("Publications & IP: 6 peer-reviewed publications, 3 patents filed, 2 Best Paper Awards.", style='List Bullet')

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
    
    # --- Publications, Patents & Recognition ---
    add_section_heading(doc, "Publications & Patents")
    pub_list = [
        "6 Peer-Reviewed Publications (full list available upon request)",
        "3 Patents Filed on Compiler-Aware Pruning and Quantization for Embedded DNNs"
    ]
    for pub in pub_list:
        doc.add_paragraph(pub, style="List Bullet")

    # --- Awards & Honors ---
    add_section_heading(doc, "Awards & Honors")
    awards = [
        'Best Paper Award, IEEE iSES 2023 — "Unstructured Pruning for Multi-Layer Perceptrons with Tanh Activation"',
        'Best Paper Award, IEEE iSES 2020 — "Distributed Real-Time Object Detection at Low Frame Rates with IoT Edge Nodes"',
        'Judge, USF Virtual Graduate Research Symposium — 2022, 2023'
    ]
    for award in awards:
        doc.add_paragraph(award, style='List Bullet')

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
        print("Waiting for server to start...")
        time.sleep(3) # Give the server a moment to start
        print("Requesting tailored content for resume sections...")
        response = requests.post(
            "http://localhost:8000/api/generate-deduplicated-resume",
            json={
                "job_description": args.job_description,
                "include_sections": ["summary", "skills", "research"],
                "max_projects_per_section": 4
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