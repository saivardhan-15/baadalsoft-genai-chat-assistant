import os
import json
import numpy as np
from google import genai
#import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")

# Create Gemini client
client = genai.Client(api_key=api_key)


class RAGSystem:
    def __init__(self, docs_path):
        self.docs_path = docs_path
        self.chunks = []
        self.embeddings = []
        self.initialize()

    def initialize(self):
        try:
            with open(self.docs_path, "r") as f:
                documents = json.load(f)

            # Create chunks from docs
            for doc in documents:
                title = doc.get("title", "Untitled")
                content = doc.get("content", "")

                chunk_text = f"Title: {title}\nContent: {content}"
                self.chunks.append(chunk_text)

            print(f"Loaded {len(self.chunks)} chunks from {self.docs_path}")

            if api_key:
                print("Generating embeddings with Gemini...")
                self._generate_embeddings()
            else:
                print("WARNING: GEMINI_API_KEY not found")

        except Exception as e:
            print(f"Error initializing RAG system: {e}")

    def _generate_embeddings(self):
        for chunk in self.chunks:
            embedding = self.get_embedding(chunk)
            self.embeddings.append(embedding)

        self.embeddings = np.array(self.embeddings)
        print("Embeddings generated successfully.")

    def get_embedding(self, text):
        try:
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text
            )

            return response.embeddings[0].values

        except Exception as e:
            print(f"Embedding error: {e}")
            return np.zeros(768)

    def retrieve(self, query, top_k=3, similarity_threshold=0.25):

        if len(self.embeddings) == 0:
            return [], "No embeddings available"

        try:
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=query
            )

            query_embedding = np.array(response.embeddings[0].values)

        except Exception as e:
            return [], f"Query embedding failed: {e}"

        # Cosine similarity
        dot_product = np.dot(self.embeddings, query_embedding)

        norm_product = (
            np.linalg.norm(self.embeddings, axis=1) *
            np.linalg.norm(query_embedding)
        )

        similarities = dot_product / (norm_product + 1e-10)

        # Top matches
        top_indices = np.argsort(similarities)[::-1][:top_k]

        retrieved = []

        for idx in top_indices:
            score = similarities[idx]

            if score >= similarity_threshold:
                retrieved.append({
                    "chunk": self.chunks[idx],
                    "score": float(score)
                })

        return retrieved, None


# Create singleton instance
rag_system = RAGSystem("docs.json")


# Simple test (optional)
if __name__ == "__main__":
    query = "What is AI?"

    results, error = rag_system.retrieve(query)

    if error:
        print(error)
    else:
        print("\nTop Retrieved Chunks:\n")
        for r in results:
            print("Score:", r["score"])
            print(r["chunk"])
            print("-" * 40)