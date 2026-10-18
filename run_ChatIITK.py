import sys

from langchain_classic.chains import RetrievalQA

from load_models import build_llm
from prompt_template_utils import get_prompt_template
from utils import open_vector_store


def build_qa(model_type="llama3", use_history=False):
    prompt, memory = get_prompt_template(promptTemplate_type=model_type, history=use_history)
    chain_type_kwargs = {"prompt": prompt}
    if use_history:
        chain_type_kwargs["memory"] = memory
    return RetrievalQA.from_chain_type(
        llm=build_llm(),
        chain_type="stuff",
        retriever=open_vector_store().as_retriever(),
        return_source_documents=True,
        chain_type_kwargs=chain_type_kwargs,
    )


def main(use_history=True, show_sources=True, model_type="llama3"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    qa = build_qa(model_type=model_type, use_history=use_history)
    while True:
        query = input("\nEnter a query: ")
        if query == "exit":
            break
        res = qa.invoke({"query": query})
        print("\n> Answer:")
        print(res["result"])
        if show_sources:
            print("--- SOURCE DOCUMENTS ---")
            for doc in res["source_documents"]:
                print("\n> " + doc.metadata["source"] + ":")
                print(doc.page_content)
            print("--- SOURCE DOCUMENTS ---")


if __name__ == "__main__":
    main()
