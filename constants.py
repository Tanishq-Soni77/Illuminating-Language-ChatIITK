import os
from langchain_community.document_loaders import CSVLoader, PyPDFLoader, TextLoader
from chromadb.config import Settings
from loaders import DocLoader, DocxLoader, ExcelLoader, HTMLLoader

ROOT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

SOURCE_DIRECTORY = f"{ROOT_DIRECTORY}/New_Database"
PERSIST_DIRECTORY = f"{ROOT_DIRECTORY}/chroma_db"

DOCUMENT_MAP = {
    ".txt": TextLoader,
    ".csv": CSVLoader,
    ".py": TextLoader,
    ".pdf": PyPDFLoader,
    ".md": TextLoader,
    ".xlsx": ExcelLoader,
    ".xls": ExcelLoader,
    ".html": HTMLLoader,
    ".docx": DocxLoader,
    ".doc": DocLoader,
}

TEXT_LOADERS = (TextLoader, CSVLoader)

EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"

CHROMA_SETTINGS = Settings(anonymized_telemetry=False, is_persistent=True)

MODELS = {
    "Llama 3 8B Instruct": ("meta-llama/Meta-Llama-3-8B-Instruct", "llama3"),
    "Llama 2 7B Chat": ("meta-llama/Llama-2-7b-chat-hf", "llama"),
    "Mistral 7B Instruct v0.2": ("mistralai/Mistral-7B-Instruct-v0.2", "mistral"),
}
