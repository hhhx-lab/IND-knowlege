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
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

class RagService:
    def __init__(self):
        self.repo = TfidfRepository()
        self.analyzer = TextAnalyzer()
        self.sim_analyzer = SimilarityAnalyzer(self.analyzer)
        
        self.api_key = os.getenv("OPENVIKING_LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        self.api_base = os.getenv("OPENVIKING_LLM_API_BASE", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)
        
        # Neo4j 连接
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # 默认知识库目录：指向项目根目录下的 output/mineru_markdowns
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.kb_dir = os.path.join(self.root_dir, "output", "mineru_markdowns")
        self.schema_path = os.path.join(self.root_dir, "ontology", "ind_schema.json")
        self.triples_path = os.path.join(self.root_dir, "ontology", "extracted_triples.json")

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

    def get_knowledge_graph_data(self):
        """
        从 Neo4j 数据库加载 TBox (Class) 和 ABox (Entity/Relation) 并返回前端图谱格式。
        """
        nodes = []
        links = []
        node_id_map = {}

        try:
            with self.neo4j_driver.session() as session:
                # 1. 载入 Class 节点 (TBox)
                class_results = session.run("MATCH (c:Class) RETURN c.id AS id, c.description AS description")
                for record in class_results:
                    n_id = record["id"]
                    nodes.append({
                        "id": n_id,
                        "label": n_id,
                        "type": "Class",
                        "group": 0,
                        "description": record["description"]
                    })
                    node_id_map[n_id] = "Class"

                # 2. 载入 Entity 节点 (ABox)
                entity_results = session.run("MATCH (e:Entity) RETURN e.id AS id")
                for record in entity_results:
                    n_id = record["id"]
                    if n_id not in node_id_map:
                        nodes.append({
                            "id": n_id,
                            "label": n_id,
                            "type": "Instance",
                            "group": 2
                        })
                        node_id_map[n_id] = "Instance"

                # 3. 载入所有关系
                rel_results = session.run("""
                    MATCH (s)-[r]->(o) 
                    RETURN s.id AS source, o.id AS target, type(r) AS p, 
                           r.original_predicate AS original_p,
                           r.source_context AS context,
                           r.source_location AS location,
                           r.source_md AS source_md
                """)
                for record in rel_results:
                    links.append({
                        "source": record["source"],
                        "target": record["target"],
                        "label": record["original_p"] or record["p"],
                        "value": 1,
                        "source_context": record["context"],
                        "source_location": record["location"],
                        "source_md": record["source_md"]
                    })
        except Exception as e:
            logger.error(f"Error loading from Neo4j: {e}")
            # 如果数据库失败，降级逻辑可以保留之前的 JSON 加载，但这里由于已经决定上 Neo4j，优先报错并记录

        return {"nodes": nodes, "links": links}

    def search_graph_context(self, query: str, limit: int = 10):
        """
        根据问题关键词，从 Neo4j 搜索相关的多跳关系事实 (GraphRAG).
        """
        keywords = self.analyzer.get_keywords(query, top_k=5)
        graph_facts = []
        
        try:
            with self.neo4j_driver.session() as session:
                for kw_tuple in keywords:
                    kw = kw_tuple[0]
                    # 1. 直接关系查询
                    cypher_direct = """
                    MATCH (s:Entity)-[r]->(o)
                    WHERE s.id CONTAINS $kw OR o.id CONTAINS $kw
                    RETURN s.id AS s, type(r) AS p, o.id AS o, r.original_predicate AS op, r.source_md AS src
                    LIMIT $limit
                    """
                    res_direct = session.run(cypher_direct, kw=kw, limit=limit)
                    for record in res_direct:
                        p_label = record["op"] or record["p"]
                        fact = f"事实: ({record['s']}) --[{p_label}]--> ({record['o']}) [来源: {record['src']}]"
                        graph_facts.append(fact)

                    # 2. 潜在多跳路径查询 (重要实体之间的关联)
                    cypher_path = """
                    MATCH (s:Entity), (o:Entity)
                    WHERE s.id CONTAINS $kw AND s.id <> o.id
                    MATCH p_path = shortestPath((s)-[*1..2]->(o))
                    RETURN p_path
                    LIMIT 2
                    """
                    res_path = session.run(cypher_path, kw=kw)
                    for record in res_path:
                        path_nodes = [node["id"] for node in record["p_path"].nodes]
                        path_rels = [type(rel) for rel in record["p_path"].relationships]
                        path_str = " -> ".join([f"({path_nodes[i]}) -[{path_rels[i]}]->" for i in range(len(path_rels))]) + f" ({path_nodes[-1]})"
                        graph_facts.append(f"关联路径: {path_str}")

        except Exception as e:
            logger.error(f"Graph search error: {e}")
            
        return list(set(graph_facts))

    def chat(self, query: str, top_k: int = 3):
        # 1. 向量搜索 (Vector/TF-IDF)
        search_results = self.repo.search(query, top_k=top_k)
        
        # 2. 图谱检索 (GraphRAG)
        graph_context = self.search_graph_context(query)
        graph_context_str = "\n".join(graph_context) if graph_context else "无相关知识图谱事实。"
        
        contexts = []
        sources = set()
        
        if search_results and search_results['documents'] and len(search_results['documents']) > 0:
            docs = search_results['documents'][0]
            metas = search_results['metadatas'][0]
            for doc, meta in zip(docs, metas):
                contexts.append(doc)
                sources.add(meta.get("source", "Unknown"))
                
        context_str = "\n\n---\n\n".join(contexts)
        
        prompt = f"""你是一个专业的药学知识库助手。请基于以下参考资料和知识图谱事实，专业、准确地回答用户的问题。
你的回答应该优先考虑知识图谱中的结构化事实，并结合文档片段进行细节补充。

### 1. 知识图谱关联事实 (Structured Graph Facts):
{graph_context_str}

### 2. 参考文档原文分块 (Supporting Document Fragments):
{context_str}

### 用户当前问题：
{query}

请以专业、严谨的口吻回答，如果涉及实体间的关系，请明确引用图谱事实。
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
