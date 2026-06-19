# GitHub 展示指南

## 推荐仓库名

```text
rag-mcp-knowledge-platform
```

## 推荐一句话简介

```text
基于 FastAPI、Hugging Face Embedding、Chroma、OpenWebUI 和 MCP 的垂直领域 RAG 知识库问答平台。
```

## README 首屏建议

GitHub README 首屏需要让面试官快速看到项目价值，建议突出：

- RAG 知识库问答；
- sentence-transformers + Chroma；
- OpenWebUI 接入；
- mock/API/Ollama 三种模型模式；
- MCP 工具调用；
- Docker Compose 一键启动；
- 测试通过。

## 推荐 Repository Topics

```text
rag
fastapi
openwebui
chroma
sentence-transformers
mcp
ollama
openai-compatible
knowledge-base
llm
```

## 上传前检查

确认不要提交以下运行产物：

- `.pyuser/`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `data/raw_docs/` 中的上传副本；
- `data/sqlite/`
- `data/vector_db/`
- `data/verify_*.db`

这些已经写入 `.gitignore`。

## 推荐截图

1. FastAPI `/docs` 页面；
2. `/health` 返回成功；
3. 文档上传接口成功；
4. 知识库构建成功，显示 `chunk_count`；
5. `/api/chat` 返回 answer 和 sources；
6. OpenWebUI 问答界面；
7. `data/vector_db/` Chroma 持久化目录；
8. MCP 工具调用结果；
9. Docker Compose 服务运行截图；
10. pytest `10 passed` 截图。

## 推荐提交顺序

```bash
git add .
git commit -m "Build RAG MCP knowledge platform"
git branch -M main
git remote add origin <your_repo_url>
git push -u origin main
```

如果仓库已经存在 remote，只需要：

```bash
git add .
git commit -m "Finalize RAG MCP knowledge platform"
git push
```

## GitHub 项目描述模板

```text
This project implements a vertical-domain RAG knowledge base platform with FastAPI, Hugging Face sentence-transformers, Chroma, OpenWebUI-compatible APIs, Ollama/API/mock LLM providers, and MCP-style tool calling.
```

## 面试官最可能关注的点

- 为什么默认 mock，而不是一开始接真实模型；
- RAG 的完整链路是否自己实现；
- embedding 和向量库如何接入；
- OpenWebUI 如何通过 OpenAI-compatible API 调用；
- MCP 工具和普通 RAG 问答有什么区别；
- 如何避免重复构建导致向量冗余；
- 项目如何部署和测试。
