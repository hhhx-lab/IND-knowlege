from fastapi import APIRouter, HTTPException, Query
from schema.chat_schema import ChatRequest, ChatResponse, IndexRequest
from service.rag_service import RagService

router = APIRouter()
rag_service = RagService()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        result = rag_service.chat(request.query, request.top_k)
        return ChatResponse(answer=result["answer"], sources=result["sources"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index")
async def index_endpoint(request: IndexRequest):
    try:
        chunks_count = rag_service.index_markdown_directory(request.markdown_dir)
        return {"message": f"Successfully indexed {chunks_count} chunks.", "chunks": chunks_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph/global")
async def get_global_graph(threshold: float = Query(0.15, ge=0.0, le=1.0)):
    try:
        return rag_service.get_global_graph_data(threshold)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph/knowledge")
async def get_knowledge_graph():
    try:
        return rag_service.get_knowledge_graph_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file/details")
async def get_file_details(filename: str):
    try:
        return rag_service.get_markdown_tree(filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
