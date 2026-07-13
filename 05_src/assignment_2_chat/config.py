import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


HERE = Path(__file__).parent
SRC_DIR = HERE.parent 
CHROMA_DIR = str(HERE / "chroma_db")
DATA_CSV = str(HERE / "livable_cities.csv")
COLLECTION_NAME = "cities"


# Load environment from the 05_src folders as done previously
load_dotenv(SRC_DIR / ".env")
load_dotenv(SRC_DIR / ".secrets")

USE_GATEWAY = os.getenv("USE_GATEWAY", "FALSE").upper() == "TRUE"
MODEL = os.getenv("MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
GATEWAY_URL = "https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1"


def _local_get_client(use_gateway: bool = USE_GATEWAY) -> OpenAI:

    if use_gateway:
        return OpenAI(
            base_url=GATEWAY_URL,
            api_key="any value",
            default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY")},
        )
    return OpenAI()


try:
    # Preferred: use the course-provided helper if 05_src is on the path.
    import sys
    sys.path.append(str(SRC_DIR))
    from utils.clients import get_client  # type: ignore
except Exception:
    get_client = _local_get_client


# A single shared client for the whole app.
client = get_client()


def get_embedding(text: str, model: str = EMBEDDING_MODEL):
    """Embed a single string, following the lab helper (04_5_vectordb)."""
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding