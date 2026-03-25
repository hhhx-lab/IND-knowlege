import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba

class TfidfRepository:
    def __init__(self, db_dir: str = "./simple_db"):
        self.db_dir = db_dir
        self.db_file = os.path.join(db_dir, "db.pkl")
        os.makedirs(db_dir, exist_ok=True)
        
        self.documents = []
        self.metadatas = []
        # TfidfVectorizer will use jieba tokenization to properly chunk and embed Chinese text
        self.vectorizer = TfidfVectorizer(tokenizer=jieba.lcut, token_pattern=None)
        self.tfidf_matrix = None
        
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "rb") as f:
                    data = pickle.load(f)
                    self.documents = data.get("documents", [])
                    self.metadatas = data.get("metadatas", [])
                
                if self.documents:
                    self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
            except Exception as e:
                print(f"Failed to load DB: {e}")

    def add_documents(self, ids: list[str], documents: list[str], metadatas: list[dict]):
        print(f"Adding {len(documents)} documents to TF-IDF Repo...")
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        # Fit vectorizer on all current docs
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
        
        with open(self.db_file, "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "metadatas": self.metadatas
            }, f)

    def search(self, query: str, top_k: int = 3):
        if self.tfidf_matrix is None or len(self.documents) == 0:
            return {"documents": [[]], "metadatas": [[]]}
            
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Guard against zero similarity documents
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        docs = []
        metas = []
        for i in top_indices:
            if similarities[i] > 0.01:  # Only return somewhat relevant documents
                docs.append(self.documents[i])
                metas.append(self.metadatas[i])
                
        return {
            "documents": [docs],
            "metadatas": [metas]
        }
