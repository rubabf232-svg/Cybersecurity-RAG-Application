import os
import re
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


KNOWLEDGE_DIR = Path("knowledge")


class RAGEngine:

    def __init__(self, knowledge_dir=KNOWLEDGE_DIR):
        self.knowledge_dir = Path(knowledge_dir)

        self.documents = []
        self.chunks = []
        self.vectorizer = None
        self.matrix = None

        self.load_knowledge()

    def clean_text(self, text):
        text = text.replace("\x00", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def read_file(self, path):

        if path.suffix.lower() == ".txt":

            return path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

        if path.suffix.lower() == ".pdf":

            if PdfReader is None:
                return ""

            reader = PdfReader(str(path))

            pages = []

            for page in reader.pages:
                text = page.extract_text() or ""
                pages.append(text)

            return "\n".join(pages)

        return ""

    def chunk_text(self, text, chunk_size=900, overlap=150):

        text = self.clean_text(text)

        if not text:
            return []

        chunks = []

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk.strip())

            if end >= len(text):
                break

            start = end - overlap

        return chunks

    def load_knowledge(self):

        self.documents = []
        self.chunks = []

        if not self.knowledge_dir.exists():
            self.knowledge_dir.mkdir(parents=True)

        for path in self.knowledge_dir.iterdir():

            if path.suffix.lower() not in [".txt", ".pdf"]:
                continue

            text = self.read_file(path)

            if not text.strip():
                continue

            self.documents.append({
                "name": path.name,
                "text": text
            })

            document_chunks = self.chunk_text(text)

            for index, chunk in enumerate(document_chunks):

                self.chunks.append({
                    "source": path.name,
                    "chunk_id": index + 1,
                    "text": chunk
                })

        self.build_index()

    def build_index(self):

        if not self.chunks:
            self.vectorizer = None
            self.matrix = None
            return

        texts = [
            item["text"]
            for item in self.chunks
        ]

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=10000
        )

        self.matrix = self.vectorizer.fit_transform(texts)

    def retrieve(self, query, top_k=4):

        if (
            not query.strip()
            or self.vectorizer is None
            or self.matrix is None
        ):
            return []

        query_vector = self.vectorizer.transform([query])

        similarities = cosine_similarity(
            query_vector,
            self.matrix
        )[0]

        ranked_indices = np.argsort(
            similarities
        )[::-1]

        results = []

        for index in ranked_indices[:top_k]:

            score = float(similarities[index])

            if score <= 0:
                continue

            result = self.chunks[index].copy()

            result["score"] = round(score * 100, 2)

            results.append(result)

        return results

    def generate_answer(self, query, results):

        if not results:

            return (
                "I couldn't find relevant information "
                "in the cybersecurity knowledge base."
            )

        best_score = results[0]["score"]

        if best_score < 5:

            return (
                "I couldn't find sufficiently relevant "
                "information in the knowledge base."
            )

        answer = (
            "Based on the retrieved cybersecurity "
            "information:\n\n"
        )

        answer += results[0]["text"]

        return answer

    def ask(self, query, top_k=4):

        results = self.retrieve(
            query,
            top_k=top_k
        )

        answer = self.generate_answer(
            query,
            results
        )

        return {
            "answer": answer,
            "results": results
        }