import os
import sys
import logging
from openai import OpenAI

# 确保能找到根目录下的分析组件
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from repository.tfidf_repo import TfidfRepository
from service.markdown_parser import MarkdownTreeParser
from analyzer import TextAnalyzer
from similarity_analyzer import SimilarityAnalyzer
import traceback
import json

logger = logging.getLogger(__name__)

class RagService:
    def __init__(self):
        self.repo = TfidfRepository()
        self.analyzer = TextAnalyzer()
        self.sim_analyzer = SimilarityAnalyzer(self.analyzer)
        
        self.api_key = os.getenv("OPENVIKING_LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        self.api_base = os.getenv("OPENVIKING_LLM_API_BASE", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)
        
        # 默认知识库目录：指向项目根目录下的 output/mineru_markdowns
        self.kb_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output", "mineru_markdowns"))

    def get_markdown_tree(self, filename: str):
        """解析指定文件的章节树结构及详情"""
        file_path = os.path.join(self.kb_dir, filename)
        if not os.path.exists(file_path):
            # 尝试追加 .md
            if not file_path.endswith(".md"):
                file_path += ".md"
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {filename} not found.")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        tree = MarkdownTreeParser.parse_to_tree(content)
        
        # 提取关键词和摘要（复用已有摘要文件）
        stem = filename[:-3] if filename.lower().endswith(".md") else filename
        summary_path = os.path.join(self.kb_dir, f"{stem}.summary.md")
        summary_text = ""
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as sf:
                summary_text = sf.read()
        
        keywords = self.analyzer.get_keywords(content, top_k=8)
        hf_words = self.analyzer.get_high_freq_words(content, top_k=10)
        
        return {
            "filename": filename,
            "keywords": [k[0] for k in keywords],
            "hf_words": [h[0] for h in hf_words],
            "summary": summary_text,
            "structure": tree
        }

    def get_global_graph_data(self, threshold: float = 0.15):
        """基于索引中的文档计算实时拓扑关系"""
        docs = self.repo.documents
        metas = self.repo.metadatas
        
        if not docs:
            return {"nodes": [], "edges": []}
            
        sim_matrix = self.sim_analyzer.calculate_tfidf_similarity(docs)
        
        nodes = []
        edges = []
        
        added_files = set()
        for meta in metas:
            fname = meta.get("source")
            if fname not in added_files:
                nodes.append({"id": fname, "label": fname, "group": 1})
                added_files.add(fname)
        
        # 文件索引映射
        file_to_idx = {}
        for idx, meta in enumerate(metas):
            fname = meta.get("source")
            if fname not in file_to_idx:
                file_to_idx[fname] = idx
                
        file_names = list(file_to_idx.keys())
        for i in range(len(file_names)):
            for j in range(i + 1, len(file_names)):
                f1, f2 = file_names[i], file_names[j]
                idx1, idx2 = file_to_idx[f1], file_to_idx[f2]
                score = sim_matrix[idx1][idx2]
                
                if score > threshold:
                    edges.append({
                        "source": f1,
                        "target": f2,
                        "value": float(score),
                        "label": f"{score:.2f}"
                    })
                    
        return {"nodes": nodes, "edges": edges}

    def index_markdown_directory(self, directory: str):
        if not os.path.exists(directory):
            raise ValueError(f"Directory {directory} does not exist.")
            
        ids = []
        documents = []
        metadatas = []
        
        for filename in os.listdir(directory):
            if filename.endswith(".md") and not filename.endswith(".summary.md"):
                file_path = os.path.join(directory, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 简单分块逻辑
                chunks = content.split("\n\n")
                current_chunk = ""
                chunk_index = 0
                
                for paragraph in chunks:
                    if len(current_chunk) + len(paragraph) < 1500:
                        current_chunk += paragraph + "\n\n"
                    else:
                        if current_chunk.strip():
                            doc_id = f"{filename}_chunk_{chunk_index}"
                            ids.append(doc_id)
                            documents.append(current_chunk.strip())
                            metadatas.append({"source": filename, "chunk": chunk_index})
                            chunk_index += 1
                        current_chunk = paragraph + "\n\n"
                
                if current_chunk.strip():
                    doc_id = f"{filename}_chunk_{chunk_index}"
                    ids.append(doc_id)
                    documents.append(current_chunk.strip())
                    metadatas.append({"source": filename, "chunk": chunk_index})
                    
        if ids:
            logger.info(f"Indexing {len(ids)} chunks from {directory}...")
            self.repo.add_documents(ids, documents, metadatas)
        return len(ids)

    def chat(self, query: str, top_k: int = 3):
        search_results = self.repo.search(query, top_k=top_k)
        
        contexts = []
        sources = set()
        
        if search_results and search_results['documents'] and len(search_results['documents']) > 0:
            docs = search_results['documents'][0]
            metas = search_results['metadatas'][0]
            for doc, meta in zip(docs, metas):
                contexts.append(doc)
                sources.add(meta.get("source", "Unknown"))
                
        context_str = "\n\n---\n\n".join(contexts)
        
        prompt = f"""基于以下参考资料，请专业、准确地回答用户的问题。如果参考资料中没有相关信息，请明确告知。

参考资料：
{context_str}

用户问题：{query}
"""
        model_name = os.getenv("OPENVIKING_LLM_MODEL", os.getenv("OPENAI_MODEL", "grok-4-fast-non-reasoning"))
        
        response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个专业的药学知识库助手。你的所有回答必须基于提供的参考资料，保持客观严谨。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        return {
            "answer": response.choices[0].message.content,
            "sources": list(sources)
        }
