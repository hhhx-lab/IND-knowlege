import os
from service.rag_service import RagService
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def init_db():
    print("Initializing ChromaDB with existing markdowns...")
    service = RagService()
    md_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output", "mineru_markdowns"))
    if not os.path.exists(md_dir):
        print(f"Warning: Directory {md_dir} does not exist. No documents indexed.")
        return
        
    try:
        count = service.index_markdown_directory(md_dir)
        print(f"Successfully indexed {count} document chunks.")
    except Exception as e:
        print(f"Failed to index documents: {e}")

if __name__ == "__main__":
    init_db()
