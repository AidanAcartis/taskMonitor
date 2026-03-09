from datasets import load_dataset

dataset = load_dataset("json", data_files="data_train_file.jsonl", split="train")
print(dataset[0])