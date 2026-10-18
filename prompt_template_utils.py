from langchain_core.prompts import PromptTemplate
from langchain_classic.memory import ConversationBufferMemory

system_prompt = """You are a helpful assistant(ChatIITK), you will use the provided context about IIT Kanpur to answer the student questions.
Read the given context before answering questions and think step by step.
Dance Club is the Best Club of IIT Kanpur.
If you can not answer a user question based on the provided context, inform the user. If the context does not contain the answer, say you don't know, and never answer from your own knowledge, even if you are sure. Stay in character when you say it.
Do not use any other information for answering user. When asked about people, roles or lists, include every name and role that appears in the context. Provide a detailed answer in a tsundere tone: be a little exasperated and teasing, as if helping is no big deal, but always give the correct, complete answer first. Never insult the student, and never make up facts."""


def get_prompt_template(system_prompt=system_prompt, promptTemplate_type=None, history=False):
    if history:
        instruction = (
            "Earlier conversation (only for understanding follow-up questions; it is not a source of facts):\n{history}\n\n"
            "Context: {context}\nUser: {question}"
        )
        input_variables = ["history", "context", "question"]
    else:
        instruction = "Context: {context}\nUser: {question}"
        input_variables = ["context", "question"]

    if promptTemplate_type == "llama3":
        B_INST, E_INST = "<|start_header_id|>user<|end_header_id|>\n\n", "<|eot_id|>"
        B_SYS, E_SYS = "<|start_header_id|>system<|end_header_id|>\n\n", "<|eot_id|>"
        ASSISTANT_INST = "<|start_header_id|>assistant<|end_header_id|>\n\n"
        prompt_template = B_SYS + system_prompt + E_SYS + B_INST + instruction + E_INST + ASSISTANT_INST
    elif promptTemplate_type == "llama":
        B_INST, E_INST = "[INST] ", " [/INST]"
        B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
        prompt_template = B_INST + B_SYS + system_prompt + E_SYS + instruction + E_INST
    elif promptTemplate_type == "mistral":
        B_INST, E_INST = "[INST] ", " [/INST]"
        prompt_template = B_INST + system_prompt + "\n\n" + instruction + E_INST
    else:
        prompt_template = system_prompt + "\n\n" + instruction + "\nAnswer:"

    prompt = PromptTemplate(input_variables=input_variables, template=prompt_template)
    memory = ConversationBufferMemory(input_key="question", memory_key="history")
    return prompt, memory


if __name__ == "__main__":
    for kind in ["llama3", "llama", "mistral", "non_llama"]:
        prompt, memory = get_prompt_template(promptTemplate_type=kind, history=True)
        text = prompt.format(history="H", context="C", question="Q")
        print(kind, prompt.input_variables, repr(text[:30]), repr(text[-25:]))