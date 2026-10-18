import torch
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline


MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"


def load_model(model_id=MODEL_ID):
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, quantization_config=bnb_config, device_map="auto"
    )
    return model, tokenizer


def build_llm(model_id=MODEL_ID):
    model, tokenizer = load_model(model_id)
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=512,
        do_sample=True,
        temperature=0.4,
        return_full_text=False,
    )
    return HuggingFacePipeline(pipeline=pipe)


if __name__ == "__main__":
    model, tokenizer = load_model()
    print(torch.cuda.memory_allocated() / 1024**3, "GiB allocated on GPU")
