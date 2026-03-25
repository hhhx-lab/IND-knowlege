from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    query: str
    top_k: int = 3

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

class IndexRequest(BaseModel):
    markdown_dir: str = "../output_TQB2858_8.4_refined/mineru_markdowns"
