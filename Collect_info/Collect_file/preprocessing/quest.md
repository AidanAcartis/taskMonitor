Tener compte de ceci, avant le code se presente comme ceci '
my_dataset = "/content/drive/MyDrive/file_desc_data/file_description.jsonl"

dataset = load_dataset(
    "json",
    data_files=my_dataset,
    split={
        "train": "train[:85%]",
        "validation": "train[85%:95%]",
        "test": "train[95%:]"
    }
)

dataset
', result 'Generating train split: 
 2008/0 [00:00<00:00, 41271.15 examples/s]
DatasetDict({
    train: Dataset({
        features: ['id', 'filename', 'file_desc'],
        num_rows: 1707
    })
    validation: Dataset({
        features: ['id', 'filename', 'file_desc'],
        num_rows: 201
    })
    test: Dataset({
        features: ['id', 'filename', 'file_desc'],
        num_rows: 100
    })
})', mais apres ce pre-processing :"
# Linear layer to project external embedding into Flan-T5 space
hidden_size = config.d_model  # dimension interne de flan-t5-small
proj_layer = nn.Linear(embedding_dim, hidden_size)
proj_layer = proj_layer.eval()

# Tokenization function
def tokenize_function(example):
    filename = example["filename"]
    file_desc = example["file_desc"]

    # --- External embedding ---
    filename_embedding = torch.tensor(lex_model.encode(filename))  # (384,)
    filename_proj = proj_layer(filename_embedding.float())  # (512,)

    # --- Prompt ---
    prompt = f"""
    Given the following filename, generate a short description of what the file is likely about.

    Filename: {filename}

    Description:
    """

    # --- Tokenization ---
    tokenized_inputs = tokenizer(prompt, padding="max_length", truncation=True)
    tokenized_labels = tokenizer(file_desc, padding="max_length", truncation=True)

    # --- Store ---
    tokenized_inputs["labels"] = tokenized_labels["input_ids"]
    tokenized_inputs["lexical_embeds"] = filename_proj.detach().numpy()  # sera injecté dans le modèle

    return tokenized_inputs

tokenized_datasets = dataset.map(tokenize_function, batched=False)
tokenized_datasets = tokenized_datasets.remove_columns(['id', 'filename', 'file_desc'])

print(f"Training: {tokenized_datasets['train'].shape}")
print(f"Validation: {tokenized_datasets['validation'].shape}")
print(f"Test: {tokenized_datasets['test'].shape}")

print(tokenized_datasets)", result :"Map: 100%
 1707/1707 [00:39<00:00, 38.63 examples/s]
Map: 100%
 201/201 [00:03<00:00, 52.62 examples/s]
Map: 100%
 100/100 [00:02<00:00, 54.25 examples/s]
Training: (1707, 4)
Validation: (201, 4)
Test: (100, 4)
DatasetDict({
    train: Dataset({
        features: ['input_ids', 'attention_mask', 'labels', 'lexical_embeds'],
        num_rows: 1707
    })
    validation: Dataset({
        features: ['input_ids', 'attention_mask', 'labels', 'lexical_embeds'],
        num_rows: 201
    })
    test: Dataset({
        features: ['input_ids', 'attention_mask', 'labels', 'lexical_embeds'],
        num_rows: 100
    })
})". Et moi je veux prouver si lexical_embeds est vraiment un vecteur de semantique global du filename qui capture le sens combine de tous ces sequences ou pas du tout.