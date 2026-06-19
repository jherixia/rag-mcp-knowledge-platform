# LangChain 学习笔记

LangChain 是一个用于构建大模型应用的开发框架。它常用于连接文档加载器、文本切分器、Embedding 模型、向量数据库、Retriever、Prompt 模板和 LLM。

在 RAG 流程中，LangChain 的典型组件包括：

- Document Loader：读取 PDF、Word、Markdown、TXT 等文档。
- Text Splitter：把长文档切分成较短的 chunk。
- Embedding：把文本转换成向量表示。
- Vector Store：保存文本 chunk 和向量。
- Retriever：根据用户问题检索相关 chunk。
- Prompt：把检索内容和用户问题组织成模型输入。
- LLM Chain：调用大模型并返回最终回答。

RAG 和普通大模型问答的区别在于，RAG 会先检索外部知识库，再把检索内容作为上下文提供给模型，因此更适合企业知识库、私有文档问答和可追溯回答场景。
