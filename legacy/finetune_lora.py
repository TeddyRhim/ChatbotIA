from typing import Any


import os
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, default_data_collator
from datasets import load_dataset, Dataset
from peft import LoraConfig, get_peft_model

# utilisation du hdd D par manque de place/performance sur le ssd C:
os.environ["HF_HOME"] = r"D:\huggingface_cache"
# gpt2 = mauvais modèle à utiliser pour mon fonctionnement.
model_name = "gpt2"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["c_attn", "c_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

print("Application de LoRA au modèle…")
model = get_peft_model(model, lora_config)


dataset = load_dataset("json", data_files={"train": "data/knowledge/knowledge_dataset.json"})

def tokenize_function(examples):

    full_texts = [p + " " + r for p, r in zip(examples["prompt"], examples["response"])]
    tokens = tokenizer(full_texts, truncation=True, padding="max_length", max_length=512)
    tokens["labels"] = tokens["input_ids"].copy()  # labels = input_ids pour causal LM
    return tokens

tokenized_datasets = dataset.map(tokenize_function, batched=True)

training_args = TrainingArguments(
    output_dir="data/lora_finetuned",
    per_device_train_batch_size=1,
    num_train_epochs=1,
    save_strategy="epoch",
    logging_steps=50,
    fp16=False,
    remove_unused_columns=False
)


trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    tokenizer=tokenizer,
    data_collator=default_data_collator
)

trainer.train()

model.save_pretrained("data/lora_finetuned")
tokenizer.save_pretrained("data/lora_finetuned")

print("Fine-tuning terminé et modèle sauvegardé")