!pip install faiss-cpu sentence-transformers transformers langchain torch langchain_community # installs all libraries we want to use
# pip is pythons installer for the environment here on Google Colab

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain.vectorstores import FAISS
from langchain.schema import Document
from transformers import AutoModelForCausalLM, AutoTokenizer # we are importing what we need for performance

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# example documents
docs = [
    Document(page_content = "Albert Einstein developed the theory of relativity."),
    Document(page_content = "Quantum mechanics explains the behavior of particles at very small scales."),
    Document(page_content = "The capital of France is Paris"),
]

# convert documents to vector embeddings, because we want to analyze the text in this format for easier understanding
doc_texts = [doc.page_content for doc in docs]
doc_embeddings = embedding_model.encode(doc_texts, convert_to_numpy = True)

# create FAISS index. FAISS is a library that enables efficient similarity search using vectors and searches for most similar vectors within the index
dimension = doc_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(doc_embeddings)

query = "Who developed the theory of relativity?"
query_embedding = embedding_model.encode([query], convert_to_numpy = True)

# searching for closest document in vector space
D, I = index.search(query_embedding, k = 1)
retrieved_doc = docs[I[0][0]]
print("Retrieved Context: ", retrieved_doc.page_content)

# load a model locally
device = "cuda"
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-3B", device_map = "auto")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B")

prompt = f"""
Use the following retrieved document to answer the query:

Context: {retrieved_doc.page_content}
Query: {query}
Answer:
"""

messages = [{"role": "user", "content": prompt}]

text = tokenizer.apply_chat_template(messages, tokenize = False, add_generation_prompt = True)

model_inputs = tokenizer([text], return_tensors = "pt").to(device)

generated_ids = model.generate(model_inputs.input_ids, max_new_tokens = 512, do_sample = True)

generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]

response = tokenizer.batch_decode(generated_ids, skip_special_tokens = True)[0]

print("LLM Response:", response)
