# Resume Editor Bot

An intelligent resume editing assistant powered by RAG (Retrieval-Augmented Generation) that helps users create, optimize, and tailor their resumes using LLMs. Now enhanced with **project-based resume generation** for job-specific tailoring.

## 🚀 New Features: Project-Based Resume Generation

The system now supports **structured project data** for intelligent resume tailoring:

- **📝 Project Dump Parsing**: Convert natural language project descriptions into structured YAML format
- **🎯 Smart Project Ranking**: AI-powered relevance ranking of projects for specific job descriptions
- **✍️ Tailored Resume Generation**: Generate job-specific resume sections based on ranked projects
- **🔍 Advanced Job Analysis**: Extract skills, requirements, and focus areas from job descriptions
- **📊 Project Analytics**: Statistics and insights about your project portfolio

## Core Features

- Dynamic Resume Drafting
- Contextual Suggestions
- Job Description Matching
- Bullet Point Optimization
- Version Control & Comparison
- Real-time Feedback
- **NEW**: Project-based resume tailoring
- **NEW**: Intelligent project ranking
- **NEW**: Structured project management

## Project Structure

```
resume_editor/
├── app/
│   ├── api/            # FastAPI routes
│   ├── core/           # Core business logic
│   │   ├── config.py   # Configuration
│   │   ├── job_parser.py # Job description parsing
│   │   └── prompts.py  # Prompt templates
│   ├── models/         # Data models
│   ├── services/       # Business services
│   │   ├── project_parser.py      # NEW: Parse project dumps
│   │   ├── project_store.py       # NEW: Manage project data
│   │   ├── relevance_ranker.py    # NEW: Rank projects by relevance
│   │   ├── resume_writer.py       # NEW: Generate tailored resumes
│   │   ├── rag_service.py         # Vector search
│   │   ├── job_analysis_service.py # Job analysis
│   │   ├── export_service.py      # Export functionality
│   │   └── resume_parser_service.py # Resume parsing
│   └── utils/          # Utility functions
├── config/             # Configuration files
├── data/              # Data storage
│   ├── embeddings/    # Vector embeddings
│   ├── projects/      # NEW: Structured project files (YAML)
│   ├── resumes/       # Resume storage
│   └── exports/       # Final resume variants
├── tests/             # Test files
├── main.py           # Application entry point
├── streamlit_app.py  # Streamlit UI
└── test_project_system.py # NEW: Test script
```

## 🛠️ Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and other configurations
```

4. Test the system:
```bash
python test_project_system.py
```

5. Run the application:
```bash
uvicorn main:app --reload
```

## 📚 API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### New Project-Based Endpoints

#### Project Management
- `POST /api/project-dump` - Parse natural language project descriptions
- `GET /api/projects` - Get all stored projects
- `GET /api/projects/{project_title}` - Get specific project
- `GET /api/projects/search/{query}` - Search projects
- `GET /api/projects/technology/{technology}` - Filter by technology
- `GET /api/projects/statistics` - Get project analytics

#### Job Analysis
- `POST /api/parse-job` - Parse job descriptions into structured format
- `POST /api/rank-projects` - Rank projects by job relevance
- `POST /api/project-recommendations` - Get comprehensive recommendations

#### Resume Generation
- `POST /api/generate-resume-section` - Generate specific resume sections
- `POST /api/generate-tailored-resume` - Generate complete tailored resume
- `POST /api/optimize-resume-section` - Optimize existing sections
- `POST /api/generate-cover-letter-intro` - Generate cover letter introductions

## 🎯 Usage Examples

### 1. Add a Project
```bash
curl -X POST "http://localhost:8000/api/project-dump" \
  -H "Content-Type: application/json" \
  -d '{
    "dump_text": "",
    "project_title": "Real-Time Analytics Dashboard"
  }'
```

### 2. Generate Tailored Resume
```bash
curl -X POST "http://localhost:8000/api/generate-tailored-resume" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We are looking for a Machine Learning Engineer with experience in Python, TensorFlow, and AWS deployment.",
    "candidate_skills": ["Python", "TensorFlow", "AWS", "Docker"],
    "include_sections": ["summary", "experience", "skills"]
  }'
```

### 3. Get Project Recommendations
```bash
curl -X POST "http://localhost:8000/api/project-recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior ML Engineer position focusing on computer vision and edge deployment."
  }'
```

## 📊 Project Data Format

Projects are stored in structured YAML format:

```yaml
title: "Machine Learning Model Optimization"
description: "Developed and optimized ML models for edge deployment"
role: "Lead ML Engineer"
technologies:
  - "Python"
  - "TensorFlow"
  - "ONNX"
  - "Docker"
methods: "Implemented model pruning and quantization techniques"
results: "Reduced model size by 75% while maintaining 95% accuracy"
impact: "Enabled real-time inference on edge devices"
duration: "6 months"
team_size: "4"
challenges: "Balancing accuracy with size constraints"
```

## 🔧 Testing

Run the comprehensive test suite:

```bash
python test_project_system.py
```

This will test:
- Project parsing and storage
- Job description analysis
- Project relevance ranking
- Resume section generation
- End-to-end workflow

## 🎨 Streamlit UI

The existing Streamlit interface has been enhanced to support the new project-based features:

```bash
streamlit run streamlit_app.py
```

## 📈 Key Benefits

1. **🎯 Job-Specific Tailoring**: Automatically rank and select the most relevant projects for each job
2. **📝 Structured Data**: Convert messy project descriptions into organized, searchable data
3. **🤖 AI-Powered Insights**: Get intelligent recommendations for resume optimization
4. **⚡ Fast Generation**: Generate tailored resumes in seconds
5. **📊 Portfolio Analytics**: Understand your project strengths and technology usage

## 🔮 Future Enhancements

- PDF project import
- Cover letter generation
- Resume scoring and feedback
- Multi-language support
- Integration with job boards
- Advanced analytics dashboard

## License

MIT 