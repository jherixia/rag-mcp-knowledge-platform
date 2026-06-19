# 平台说明

本平台基于 FastAPI 提供后端接口，支持上传 TXT、Markdown、PDF 和 Word 文档。系统会把文档切分为多个 chunk，并保存到本地 SQLite 数据库中。

OpenWebUI 可以通过 OpenAI-compatible API 接入本平台。模型列表接口是 `/v1/models`，聊天接口是 `/v1/chat/completions`。

默认 mock 模式不需要 Ollama、本地模型、vLLM 或外部 API Key，适合快速验证上传文档、构建知识库和 RAG 问答流程。
