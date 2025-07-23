# Resume Editor Bot

A modular, YAML-driven resume generation and analysis system for AI researchers and engineers. Supports both API-based and local script workflows, with dynamic project, publication, and patent integration.

## 🚀 Key Features
- **World-class resume generation** (local script or API)
- **YAML-driven data**: Projects, publications, and patents are structured and easy to update
- **Factual, quantified project claims**
- **Dynamic patent and publication loading**
- **ATS-friendly, recruiter-ready formatting**
- **Streamlit UI for interactive editing**
- **API for advanced automation and integration**

---

## 🗂️ Project Structure
```
resume_editor/
├── app/                  # FastAPI backend
│   ├── api/              # API routes
│   ├── core/             # Core logic
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   └── utils/            # Utilities
├── config/               # Config files
├── data/
│   ├── projects/         # Project YAMLs
│   ├── publications.yaml # Publications YAML
│   ├── patents.yaml      # Patents YAML
│   └── exports/          # Resume DOCX output
├── scripts/
│   ├── create_concise_resume.py   # Local resume generator
│   ├── compare_resume_versions.py # Resume comparison tool
├── tests/
│   └── ui/streamlit_app.py        # Streamlit UI
├── README.md
└── requirements.txt
```

---

## 🛠️ Setup
1. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

---

## 📄 YAML Data Model

### Example: Project YAML
```yaml
title: "LitBot: AI Literature Survey Assistant"
description: "Designed and built LitBot, a custom GPT + FAISS-powered literature assistant for neural network sparsity research. Integrated semantic chunking, extractive summarization, and citation linking across 200+ papers."
technologies:
  - OpenAI GPT models
  - FAISS
results: "Integrated semantic chunking, extractive summarization, and citation linking across 200+ papers."
github_url: "https://github.com/kavyakl/litnet"
featured: true
```

### Example: Publication YAML (in publications.yaml)
```yaml
- title: "Unstructured Pruning for Multi-Layer Perceptrons with Tanh Activation"
  authors: "L. K. Kalyanam, S. Katkoori"
  venue: "IEEE iSES"
  year: 2023
  doi: "10.1109/iSES58672.2023.00025"
  award: "Best Paper Award"
```

### Example: Patent YAML (in patents.yaml)
```yaml
- title: "Layer-Wise Filter Thresholding Based CNN Pruning for Efficient IoT Edge Implementations"
  inventors: ["Srinivas Katkoori", "Lakshmi Kavya Kalyanam"]
  application_number: "63/552,084"
  filing_date: "2024-02-09"
  usf_ref: "24T085US"
  description: "Provisional patent for a thresholding-based CNN pruning method for efficient IoT edge deployment."
- title: "Unstructured Pruning for Multi-Layer Perceptrons with Tanh Activation"
  inventors: ["Srinivas Katkoori", "Lakshmi Kavya Kalyanam"]
  invention_id: "USF23/00331"
  tech_id: "24T063"
  description: "Patent for unstructured pruning techniques for MLPs with tanh activation."
- title: "Range-Based Hardware Optimization of Multi-Layer Perceptrons with ReLUs"
  inventors: ["Srinivas Katkoori", "Lakshmi Kavya Kalyanam"]
  usf_ref: "23T078US"
  qnb_ref: "173738.02709"
  description: "Patent for range-based hardware optimization of MLPs with ReLU activation."
```

---

## 🖥️ Local Resume Generation
Generate a world-class resume directly from your YAML data:
```bash
python scripts/create_concise_resume.py --max-projects 6
```
- Output: `data/exports/Kalyanam_Resume_WorldClass.docx`
- All content (projects, publications, patents) is loaded dynamically from YAML.
- Use `--max-projects` to control how many projects are shown.

---

## 🌐 API Usage
Start the FastAPI backend:
```bash
uvicorn main:app --reload
```
- API docs: http://localhost:8000/docs
- Supports endpoints for project management, resume generation, job analysis, and more.

---

## 🎨 Streamlit UI
Run the interactive UI:
```bash
streamlit run tests/ui/streamlit_app.py
```

---

## 🧪 Testing
Run the test suite:
```bash
python tests/test_project_system.py
```

---

## 📈 Key Benefits
- **Factual, quantified, and recruiter-ready resumes**
- **Easy to update**: Just edit your YAML files (projects, publications, patents)
- **Supports both local and API workflows**
- **Patent and publication integration from YAML**
- **Modern, modular, and extensible**

---

## License
MIT 
