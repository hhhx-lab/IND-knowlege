# IND Pharmaceutical Registration Knowledge Graph (IND-knowlege)

本项目是一个专门针对药学注册申报资料（IND/NDA）设计的交互式知识图谱与智能问答系统。它能够自动从复杂的 PDF/Word 文档中提取结构化信息，生成智能摘要，并可视化文档间的语义关联。

## 核心功能

- **自动化文档处理**：集成 MinerU 高精度提取引擎，支持 PDF、Word、Docx 等多种格式。
- **智能化摘要生成**：利用 LLM (Grok/OpenAI) 对长篇药学文档进行关键点提炼。
- **动态知识图谱**：
  - **全景拓扑**：基于 TF-IDF 与 AI 语义相似度展示文档间的全景关联。
  - **单文档导图**：自动解析 Markdown 标题结构，生成文档大纲思维导图。
- **专业 RAG 问答**：基于 ChromaDB 向量数据库，支持对整套申报资料进行语义检索与专业问答。

## 系统架构

- **前端**：React + TypeScript + Vite + Tailwind CSS + react-force-graph
- **后端**：FastAPI + Python 3.10+
- **数据引擎**：MinerU (提取) + ChromaDB (向量索引) + Jieba (中文分词)
- **大模型**：OpenAI / Grok 系列模型

## 快速启动

### 1. 环境准备

确保已安装 Python 3.10+ 和 Node.js。

```bash
# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd rag_frontend
npm install
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件，配置以下内容：

```env
OPENAI_API_KEY=your_api_key
MINERU_API_KEY=your_mineru_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 3. 数据处理流水线

按顺序执行以下步骤以构建知识库：

#### 第一步：文档提取与图谱构建
解析指定文件夹下的所有文档，生成 Markdown 全文、智能摘要及 HTML 离线图谱。
```bash
python main.py --dir "正大天晴注册案例_整套完整资料" --output "output"
```

#### 第二步：向量数据库初始化
将处理后的文档片段同步到后端检索引擎。
```bash
cd rag_backend
python init_db.py
```

### 4. 启动服务

```bash
# 启动后端 (默认端口 8000)
cd rag_backend
python main.py

# 启动前端 (默认端口 5176)
cd rag_frontend
npm run dev -- --port 5176
```

访问地址：[http://localhost:5176/](http://localhost:5176/)

## 输入与输出说明

### 输入 (Input)
- **存放路径**：`正大天晴注册案例_整套完整资料/`
- **文件格式**：PDF, DOC, DOCX, MD。

### 输出 (Output)
- **结构化文档**：`output/mineru_markdowns/*.md` (由 MinerU 提取的结构化纯文本)。
- **智能摘要**：`output/mineru_markdowns/*.summary.md` (LLM 生成的学术概要)。
- **分析报告**：`output/graph_*.html` (针对单个文档生成的交互式导图)。
- **可视化结果**：前端展示的全局关系拓扑图。

## 技术规范
- 遵循 `camelCase` (变量) / `PascalCase` (组件) 命名约定。
- 后端采用 `api/service/repository` 三层架构。
- 详情请参阅 `docs/` 目录下的设计文档（如有）。
