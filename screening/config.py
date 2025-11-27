# screening/config.py

import os
from pathlib import Path

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = "llama3.2:latest"
OLLAMA_TIMEOUT = 120

# Paths - UPDATED
BASE_DIR = Path(__file__).parent.parent  # Goes up to project root
RESUME_DIR = BASE_DIR / "data" / "parsed_resumes"  # Now points to correct location

# Agent Weights
WEIGHTS = {
    "technical": 0.40,
    "career": 0.35,
    "fit": 0.25
}

# Scoring Parameters
MIN_SCORE = 0
MAX_SCORE = 100

# Processing Configuration
PARALLEL_AGENTS = True
BATCH_SIZE = 1

# Output Configuration
SHOW_BREAKDOWN = False