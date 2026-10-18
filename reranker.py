from typing import Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.retrievers import BaseRetriever
from sentence_transformers import CrossEncoder

RERANKER_NAME = "BAAI/bge-reranker-base"


def load_reranker():
    # CPU on purpose: the 8B language model already needs most of the GPU memory.
    return CrossEncoder(RERANKER_NAME, device="cpu", max_length=512)


class RerankedRetriever(BaseRetriever):
    """Fetch a wide set of candidate passages, then keep the ones a stronger
    model scores as the best match for the question."""

    store: Any
    reranker: Any
    fetch_k: int = 30
    top_k: int = 6

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ):
        seen, candidates = set(), []
        for doc in self.store.similarity_search(query, k=self.fetch_k):
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                candidates.append(doc)
        scores = self.reranker.predict([(query, d.page_content) for d in candidates])
        ranked = sorted(zip(scores, candidates), key=lambda pair: pair[0], reverse=True)
        return [doc for _, doc in ranked[: self.top_k]]
