# Resume Parser

Parse PDF resumes using Ollama LLM models offline and ranks the candidates with score based on the job description.

## Features
- Upload PDF resumes
- Extract structured data (experience, education, skills, etc.)
- Offline processing with Ollama
- Give rankings of the candidates best suited according to the job description based on 3 agents
- Clean web interface

## Setup

### Prerequisites
- Python 3.8+
- install ollama and ensure it has been added to your path variables 

### Installation
1. Create a virtual env and navigate to the backend folder of this project in your terminal

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Pull Ollama model:
```bash
ollama pull llama3.2:latest
```

4. Create `.env` file in `backend/` directory:
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
MAX_FILE_SIZE=10485760
DEBUG=True
PORT=8000

RUN_ANALYSIS=False
ANALYSIS_MODEL=llama3.2:latest
ANALYSIS_TEMPERATURE=0.1
```

5. Ensure you have created empty __init__.py files in every folder of the apps folder inside backend and create a folder named "uploads" in the backend folder

6. Run the backend:
```bash
uvicorn app.main:app --reload
```

7. Open `frontend/index.html` in your browser

## Usage

1. Upload a PDF resume
2. Wait for parsing to complete
3. Upload job description as text
4. View the ranking

## Tech Stack

- **Backend**: FastAPI, Python
- **LLM**: Ollama (Qwen 2.5 / Llama 3.2)
- **PDF Processing**: pdfplumber, PyPDF2
- **Frontend**: Vanilla HTML/CSS/JavaScript
