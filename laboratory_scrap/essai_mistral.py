from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Nom du modèle sur Hugging Face
model_name = "EleutherAI/gpt-neo-2.7B"

# Charger le tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Charger le modèle avec l'optimisation de la mémoire
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")

def generate_text(prompt, max_length=200):
    # Tokeniser l'entrée
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

    # Générer une réponse
    output = model.generate(**inputs, max_length=max_length)

    # Décoder la sortie et l'afficher
    return tokenizer.decode(output[0], skip_special_tokens=True)

# Exemple d'utilisation
prompt = "Explique le fonctionnement d'un modèle de langage."
response = generate_text(prompt)
print(response)