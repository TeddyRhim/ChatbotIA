from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# 1. Chargement du modèle (CPU uniquement)
model_name = "mistralai/Mistral-7B-Instruct-v0.2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="cpu")

# 2. Création du pipeline de génération
chatbot = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=200,
    temperature=0.7,
)

# 3. Exemple de prompt
prompt = "Que sait-on du village de Bale ?"

# 4. Génération
response = chatbot(prompt)[0]["generated_text"]

print("🧠 Réponse du modèle :")
print(response)