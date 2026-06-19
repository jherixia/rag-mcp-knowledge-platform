# OpenWebUI 接入说明

OpenWebUI 是一个常用的大模型聊天前端，可以连接 Ollama，也可以连接 OpenAI-compatible API。

如果后端实现了 `/v1/models` 和 `/v1/chat/completions`，OpenWebUI 就可以把这个后端当作 OpenAI 风格模型服务来使用。

常见配置：

- Base URL：后端的 OpenAI-compatible 地址，例如 `http://localhost:8000/v1`。
- API Key：如果后端不校验，可以填写任意字符串，例如 `mock-key`。
- Model：模型名称，例如 `rag-mcp-knowledge-platform`。

当用户在 OpenWebUI 输入问题时，OpenWebUI 会把消息发送到 `/v1/chat/completions`。后端可以从 messages 中取最后一条 user 消息，执行 RAG 检索，再调用 mock、API 或 Ollama 模型生成回答。
