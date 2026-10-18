# ChatIITK

A retrieval-augmented chatbot that answers questions about IIT Kanpur, using only the documents it has been indexed on. Every answer lists the passages it came from.

Rebuild of the *Lluminating Language* project of the Brain and Cognitive Science Club (May to July 2024).

## How it works

1. `ingest.py` reads the files in `New_Database`, splits them into passages and stores them in a Chroma vector database (`chroma_db`).
2. For each question, the closest passages are fetched and a cross-encoder (`reranker.py`) keeps the best ones.
3. A 4-bit quantised Llama 3 8B Instruct (`load_models.py`) answers from those passages. Llama 2 and Mistral can be selected too, each with its own prompt template (`prompt_template_utils.py`).
4. The conversation is kept with `ConversationBufferMemory`, and the page shows the source passages under every answer.

Supported file types: `.txt`, `.md`, `.py`, `.pdf`, `.csv`, `.xls`, `.xlsx`, `.html`, `.docx`, `.doc` (`.doc` needs LibreOffice installed).

## Setup

Tested with Python 3.11 on Windows with an NVIDIA GPU of 8 GB (Llama 3 in 4-bit uses about 5.7 GiB). For GPU use, install PyTorch first from [pytorch.org](https://pytorch.org/get-started/locally/) for your CUDA version.

```
pip install -r requirements.txt
hf auth login             # the Llama models are gated; request access on Hugging Face first
python ingest.py           # builds chroma_db from New_Database (once)
streamlit run ChatIITK_UI.py
```

`python run_ChatIITK.py` starts a terminal version instead. `ingest.py` stops if `chroma_db` already exists; delete the folder to rebuild.

## Files

| File | Purpose |
|---|---|
| `ChatIITK_UI.py`, `styles.css` | Streamlit page |
| `run_ChatIITK.py` | Terminal version |
| `ingest.py` | Reads, splits and indexes the documents |
| `load_models.py` | Loads the language model in 4-bit |
| `prompt_template_utils.py` | System prompt and templates for Llama 3, Llama 2, Mistral and a fallback |
| `reranker.py` | Re-orders the retrieved passages |
| `loaders.py` | Readers for `.xlsx`, `.html`, `.docx` and `.doc` |
| `utils.py` | Embedding model and access to the vector database |
| `constants.py` | Paths, model names and the file-type map |
| `Web_Scraping/` | Selenium scrapers for IIT Kanpur websites |
| `Report/` | The project report (PDF) |

## Data

- `New_Database/` holds the documents the chatbot reads. Everything in it is indexed, so add only data files.
- `Old_Database/` holds the data of the original 2024 project, unchanged.

Some file names in `New_Database` are long. On Windows, run `git config --global core.longpaths true` before cloning.
