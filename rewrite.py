from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from dotenv import load_dotenv
import os

load_dotenv()
hf_token = os.getenv("HF_TOKEN")

model_id = "google/flan-t5-base"
tokenizer = AutoTokenizer.from_pretrained(model_id, use_auth_token=hf_token)
model = AutoModelForSeq2SeqLM.from_pretrained(model_id, use_auth_token=hf_token)

rewrite_pipeline = pipeline("text2text-generation", model=model, tokenizer=tokenizer)

def rewrite_text(text, tone="Neutral", creativity=0.7, max_tokens=256):
    prompt = f"Rewrite this in a {tone.lower()} tone: {text}"
    result = rewrite_pipeline(prompt, max_new_tokens=max_tokens, temperature=creativity)[0]["generated_text"]
    return result
