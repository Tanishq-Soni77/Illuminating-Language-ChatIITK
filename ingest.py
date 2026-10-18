import os
import time
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from constants import CHROMA_SETTINGS, DOCUMENT_MAP, PERSIST_DIRECTORY, SOURCE_DIRECTORY, TEXT_LOADERS
from utils import get_embeddings

def load_single_document(file_path):
    file_extension = os.path.splitext(file_path)[1]
    loader_class = DOCUMENT_MAP.get(file_extension)
    if loader_class is None:
        raise ValueError(f"No loader for file type: {file_extension}")
    if loader_class in TEXT_LOADERS:
        loader = loader_class(file_path, encoding="utf-8")
    else:
        loader = loader_class(file_path)
    return loader.load()

def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(documents)

def make_chunk_ids(chunks):
    counts = {}
    ids = []
    for chunk in chunks:
        source = chunk.metadata["source"]
        number = counts.get(source, 0)
        counts[source] = number + 1
        ids.append(f"{source}::{number}")
    return ids

def build_vector_store(chunks, persist_directory=PERSIST_DIRECTORY):
    return Chroma.from_documents(
        chunks,
        get_embeddings(),
        ids=make_chunk_ids(chunks),
        persist_directory=persist_directory,
        client_settings=CHROMA_SETTINGS,
    )

def load_documents(source_dir):
    documents = []
    for root, _, files in os.walk(source_dir):
        for file_name in files:
            if os.path.splitext(file_name)[1] in DOCUMENT_MAP:
                documents.extend(load_single_document(os.path.join(root, file_name)))
    return documents

if __name__ == "__main__":
    if os.path.isdir(PERSIST_DIRECTORY) and os.listdir(PERSIST_DIRECTORY):
        raise SystemExit(
            f"{PERSIST_DIRECTORY} already holds an index. Rename or move it first, "
            "so that old and new chunks are not mixed."
        )
    start = time.time()
    documents = load_documents(SOURCE_DIRECTORY)
    chunks = split_documents(documents)
    print(f"{len(documents)} documents -> {len(chunks)} chunks")

    store = build_vector_store(chunks)
    print(f"stored {store._collection.count()} chunks in {time.time() - start:.0f} s")