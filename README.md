```markdown
# 📄 Offline Resume Parser & Candidate Ranking System

Parse PDF resumes using **offline AI models (Ollama)** and rank candidates based on a given job description — **no cloud, no data leakage**.

---

## 🧠 What This Project Does

- 📂 Upload PDF resumes  
- 🤖 Uses an **offline AI model** to understand resumes  
- 🧾 Extracts structured data:
  - Skills
  - Education
  - Experience
- 📊 Ranks candidates based on job description relevance
- 🌐 Clean and simple web interface

---

## 🖥️ System Requirements

- Windows / macOS / Linux
- **Python 3.8 or higher**
- **8 GB RAM recommended**
- Internet required **only once** to download dependencies and AI model

---

## 🧩 Tech Stack Used

- **Python** – backend logic
- **FastAPI** – backend API framework
- **Ollama** – runs AI models locally (offline)
- **Llama 3.2** – resume parsing & ranking
- **HTML / CSS / JavaScript** – frontend UI

---

---

## 🛠️ Step-by-Step Setup

---

### 1️⃣ Install Python

1. Download Python from:  
   👉 https://www.python.org/downloads/
2. During installation:
   - ✅ **Check** “Add Python to PATH”
3. Verify installation:
   ```bash
   python --version
````

You should see something like:

```
Python 3.10.x
```

---

### 2️⃣ Install Ollama (Offline AI Engine)

1. Download Ollama from:
   👉 [https://ollama.com](https://ollama.com)
2. Install it normally
3. Verify installation:

   ```bash
   ollama --version
   ```

---

### 3️⃣ Download or Clone the Project

Clone the repository:

```bash
git clone <your-repository-url>
```

OR download ZIP and extract it.

Navigate to the backend folder:

```bash
cd backend
```

---

### 4️⃣ Create a Virtual Environment (IMPORTANT)

This prevents dependency conflicts.

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**macOS / Linux**

```bash
source venv/bin/activate
```

You should now see `(venv)` in the terminal.

---

### 5️⃣ Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

### 6️⃣ Download the AI Model (One-Time Only)

```bash
ollama pull llama3.2:latest
```

This downloads the model locally so it can run **offline**.

---

### 7️⃣ Create `.env` Configuration File

Inside the `backend/` folder, create a file named `.env` and paste **exactly this**:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
MAX_FILE_SIZE=10485760
DEBUG=True
PORT=8000

RUN_ANALYSIS=False
ANALYSIS_MODEL=llama3.2:latest
ANALYSIS_TEMPERATURE=0.1
```

---

### 8️⃣ Create Required Folder & Files

#### Create uploads folder:

```bash
mkdir uploads
```

#### Ensure every folder inside `backend/app/` has an empty `__init__.py` file

Example:

```
backend/app/api/__init__.py
backend/app/core/__init__.py
backend/app/model/__init__.py
```

---

### 9️⃣ Start the Backend Server

Make sure:

* `(venv)` is active
* You are inside `backend/`

Run:

```bash
uvicorn app.main:app --reload
```

If successful, you will see:

```
Uvicorn running on http://127.0.0.1:8000
```

⚠️ **Do NOT close this terminal while using the app**

---

## 🌐 Running the Frontend

1. Open this file in your browser:

```
frontend/index.html
```

2. Inside the app:

   1. Upload a PDF resume
   2. Wait for parsing to finish
   3. Paste job description
   4. View ranked candidates

---

## ❗ Common Errors & Fixes

### ❌ `ollama not found`

* Restart system after installing Ollama
* Ensure Ollama is added to PATH

---

### ❌ `ModuleNotFoundError`

* Virtual environment not activated

```bash
venv\Scripts\activate
```

---

### ❌ Frontend not working

* Backend server must be running
* Check terminal logs for errors

---

## 🔐 Privacy & Offline Guarantee

* ✅ No cloud APIs used
* ✅ Resumes never leave your system
* ✅ AI runs fully offline

---

## 🚀 Who Is This Project For?

* Students learning AI / LLMs
* Recruiters needing offline resume screening
* HR-tech applications
* Privacy-focused AI projects


