from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# modèle à changer
BASE_MODEL = "gpt2"
LORA_DIR = "data/lora_finetuned"

print("Chargement du modèle de base…")
model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

print("Application du LoRA…")
model = PeftModel.from_pretrained(model, LORA_DIR)

prompt = "Quelles sont les MISSIONS & CONTRATS connus ? :"
inputs = tokenizer(prompt, return_tensors="pt")
output = model.generate(**inputs, max_new_tokens=100)

print(tokenizer.decode(output[0], skip_special_tokens=True))
