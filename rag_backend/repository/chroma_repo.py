import os
import chromadb
from chromadb.utils import embedding_functions

class ChromaRepository:
    def __init__(self, db_dir: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=db_dir)
        
        api_key = os.getenv("OPENVIKING_LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        api_base = os.getenv("OPENVIKING_LLM_API_BASE", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
        
        if api_key:
            self.emb_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key,
                api_base=api_base,
                model_name="text-embedding-ada-002"
            )
        else:
            self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
            
        self.collection = self.client.get_or_create_collection(
            name="ind_knowledge", 
            embedding_function=self.emb_fn
        )

    def add_documents(self, ids: list[str], documents: list[str], metadatas: list[dict]):
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )

    def search(self, query: str, top_k: int = 3):
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        return results
