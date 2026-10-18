from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from constants import CHROMA_SETTINGS, EMBEDDING_MODEL_NAME, PERSIST_DIRECTORY

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class QueryPrefixEmbeddings(HuggingFaceEmbeddings):
    """BGE models are trained to see this instruction in front of a search query
    (and nothing in front of the stored passages)."""

    def embed_query(self, text):
        return super().embed_query(QUERY_PREFIX + text)


def get_embeddings(device_type="cuda"):
    return QueryPrefixEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": device_type},
        encode_kwargs={"normalize_embeddings": True},
    )


def open_vector_store(persist_directory=PERSIST_DIRECTORY):
    return Chroma(
        persist_directory=persist_directory,
        embedding_function=get_embeddings(),
        client_settings=CHROMA_SETTINGS,
    )
