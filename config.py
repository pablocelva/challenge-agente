import os
from dotenv import load_dotenv

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
LLM_MODEL = "command-a-03-2025"
EMBEDDING_MODEL = "embed-v4.0"