from transformers import AutoTokenizer, AutoModel
import torch

# Initialize LLM model
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")


def generate_embedding(text: str):
    """
    Generates embeddings for the given text using a pre-trained transformer model.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).numpy().tolist()
