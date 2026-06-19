# 基于 RAG 与 MCP 的垂直领域智能知识库问答平台

这是一个 mock-first 的 RAG 知识库问答项目。默认 `LLM_PROVIDER=mock`，没有 API Key、没有 Ollama、没有 GPU 也能跑通文档上传、知识库构建、RAG 问答和 OpenWebUI 接入。第二阶段已支持真实 OpenAI-compatible API 模式和 Ollama 本地模型模式。

## 项目概览

本项目实现一个可本地运行的垂直领域 RAG 知识库问答平台，支持文档上传、知识库构建、向量检索、RAG 问答、OpenWebUI 接入和 MCP 工具调用。默认使用 mock 模式，保证没有 API Key、没有 Ollama、没有 GPU 的环境也能跑通完整流程；也可以切换到 OpenAI-compatible API 或 Ollama 本地模型。

- 单元测试：`10 passed`
- 默认运行模式：mock
- 检索后端：sentence-transformers + Chroma，支持 lightweight/local 兜底
- 前端接入：OpenWebUI / OpenAI-compatible API
- 工具服务：MCP HTTP fallback Server
- 部署方式：本地命令或 Docker Compose

相关文档：

- [接口文档](docs/接口文档.md)
- [MCP Server 文档](mcp_server/README.md)

## 第一阶段：mock 模式启动

安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

启动后端：

```bash
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000
```

如果当前机器没有 `pip`，但项目目录里已有 `.pyuser` 依赖，可以使用：

```bash
PYTHONPATH=/home/jp/code/agent/.pyuser/lib/python3.12/site-packages:backend \
/home/jp/code/agent/.pyuser/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问：

- 健康检查：http://localhost:8000/health
- API 文档：http://localhost:8000/docs
- 模型列表：http://localhost:8000/v1/models

构建示例知识库：

```bash
PYTHONPATH=backend python3 scripts/build_sample_kb.py
```

## 第二阶段：API 模式启动

复制 `.env.example` 为 `.env`，并修改：

```env
LLM_PROVIDER=api
API_MODEL_BASE_URL=https://api.deepseek.com/v1
API_MODEL_API_KEY=your_api_key_here
API_MODEL_NAME=deepseek-chat
```

然后启动：

```bash
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API 模式使用 OpenAI Chat Completions 格式，兼容 DeepSeek、OpenAI-compatible、通义千问兼容接口等。API Key 只从环境变量或 `.env` 读取，不写死在代码里。

## Ollama 模式启动

先安装并运行 Ollama：

```bash
ollama pull qwen2.5:7b
ollama serve
```

本机直接访问 Ollama 时，`.env` 使用：

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

如果 backend 在 docker-compose 内部访问 Ollama，使用：

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:7b
```

Ollama 未启动或模型不存在时，接口会返回清晰的模型调用失败信息。

## OpenWebUI 接入方法

OpenWebUI 里添加 OpenAI-compatible 连接：

- API Key: `mock-key`
- Model: `rag-mcp-knowledge-platform`

Base URL 按部署方式选择：

1. 后端和 OpenWebUI 都在 docker-compose 中：

```text
http://backend:8000/v1
```

2. 后端在本机启动，OpenWebUI 在 Docker 中：

```text
http://host.docker.internal:8000/v1
```

3. 后端和 OpenWebUI 都本机启动：

```text
http://localhost:8000/v1
```

Docker Compose 启动：

```bash
docker compose up --build
```

服务端口：

- backend: http://localhost:8000
- OpenWebUI: http://localhost:3000
- Ollama: http://localhost:11434

## curl 测试命令

上传文档：

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@data/samples/ai_intern_job_requirements.txt"
```

构建知识库：

```bash
curl -X POST "http://localhost:8000/api/knowledge/build" \
  -H "Content-Type: application/json" \
  -d '{"doc_ids": []}'
```

RAG 问答：

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "根据人工智能实习生岗位要求，我需要掌握哪些技术栈？", "top_k": 5}'
```

OpenAI-compatible 调用：

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model": "rag-mcp-knowledge-platform", "messages": [{"role": "user", "content": "RAG 和普通大模型问答有什么区别？"}]}'
```

## 自动测试脚本

先确保后端已启动，并且已经构建知识库：

```bash
PYTHONPATH=backend python3 scripts/build_sample_kb.py
python3 scripts/test_api.py
```

如果后端不是默认地址：

```bash
python3 scripts/test_api.py http://localhost:8000
```

## 第三阶段：真实 Embedding 检索

项目已支持 Hugging Face `sentence-transformers` 和 Chroma 向量数据库。默认配置：

```env
VECTOR_STORE_TYPE=chroma
VECTOR_DB_DIR=data/vector_db
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5
CHUNK_SIZE=800
CHUNK_OVERLAP=120
TOP_K=5
```

首次运行真实 embedding 时会自动从 Hugging Face 下载模型，默认使用 CPU，不要求 GPU。向量库数据会持久化保存在：

```text
data/vector_db/
```

如果网络不稳定或模型下载较慢，可以切换备用模型：

```env
EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

如果只想在离线环境验证流程，可以临时使用轻量兜底：

```env
EMBEDDING_BACKEND=lightweight
VECTOR_STORE_TYPE=local
```

主路径仍然是 `sentence-transformers + Chroma`。

## 知识库管理

构建知识库：

```bash
curl -X POST "http://localhost:8000/api/knowledge/build" \
  -H "Content-Type: application/json" \
  -d '{"doc_ids": []}'
```

重建指定文档：

```bash
curl -X POST "http://localhost:8000/api/knowledge/rebuild" \
  -H "Content-Type: application/json" \
  -d '{"doc_ids": ["your_doc_id"]}'
```

删除文档及其 chunks：

```bash
curl -X DELETE "http://localhost:8000/api/documents/your_doc_id"
```

清空知识库但保留原始上传文档：

```bash
curl -X DELETE "http://localhost:8000/api/knowledge/clear"
```

重复构建同一文档时，系统会先删除该文档旧 chunks 和旧向量，再写入新 chunks，避免向量冗余。

## MCP 工具调用能力

第四阶段新增 MCP HTTP fallback 工具服务，目录在 `mcp_server/`。当前提供：

- 知识库统计：`get_kb_stats`
- 项目文件读取：`read_project_file`
- SQLite 笔记查询：`query_notes`
- 知识库检索工具：`search_kb`

初始化数据库和 notes 示例数据：

```bash
PYTHONPATH=backend python3 scripts/init_db.py
```

启动 MCP HTTP fallback 服务：

```bash
PYTHONPATH=backend uvicorn mcp_server.server:app --host 0.0.0.0 --port 9000
```

测试 MCP 工具：

```bash
python3 scripts/test_mcp_tools.py
```

Docker Compose 会同时启动 `mcp-server`，HTTP 端口为 `9000`。

## 项目 Demo 流程

1. 启动后端：`PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. 构建示例知识库：`PYTHONPATH=backend python3 scripts/build_sample_kb.py`
3. 打开 OpenWebUI：http://localhost:3000
4. 提问：`根据人工智能实习生岗位要求，我需要掌握哪些技术栈？`
5. 查看回答中的 `sources`
6. 启动 MCP Server：`PYTHONPATH=backend uvicorn mcp_server.server:app --host 0.0.0.0 --port 9000`
7. 调用 `get_kb_stats` 和 `search_kb` 工具

## Demo 验证项

建议按以下内容验证项目运行状态：

1. 后端 `/health` 返回正常；
2. 文档上传成功；
3. 知识库构建返回 `chunk_count`；
4. `/api/chat` 返回 `answer` 和 `sources`；
5. OpenWebUI 中选择 `rag-mcp-knowledge-platform` 并完成问答；
6. `data/vector_db/` 中生成 Chroma 持久化文件；
7. MCP 工具调用返回正常；
8. Docker Compose 服务正常运行。

## 常见问题排查

- `No module named pip`：系统没有 pip。可以安装 `python3-pip`，或使用项目内 `.pyuser` 里的依赖启动。
- `/api/chat` 返回“知识库为空”：先上传文档并调用 `/api/knowledge/build`，或运行 `scripts/build_sample_kb.py`。
- API 模式返回“缺少配置”：检查 `.env` 中是否设置 `API_MODEL_BASE_URL`、`API_MODEL_API_KEY`、`API_MODEL_NAME`。
- Ollama 模式失败：确认执行过 `ollama pull qwen2.5:7b`，并且 `ollama serve` 正在运行。
- OpenWebUI 连不上后端：检查 Base URL 是否符合部署场景；Docker 内访问本机后端通常用 `http://host.docker.internal:8000/v1`。
- `stream=true`：当前阶段支持基础 SSE 输出，主要目标是保证 OpenWebUI 不报错。
- embedding 模型下载慢：改用 `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`，或临时设置 `EMBEDDING_BACKEND=lightweight`。
- Chroma 数据清空：调用 `DELETE /api/knowledge/clear`，或停止服务后删除 `data/vector_db/`。
- 重复构建文档：现在会先删除该文档旧 chunks，再写入新 chunks，不会重复堆积同一个文档的向量。
