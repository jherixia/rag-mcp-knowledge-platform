# MCP Server

本目录提供项目的 MCP 工具调用服务。当前实现为 HTTP-based MCP-like fallback 服务，工具函数与 MCP 语义保持一致；如果后续接入官方 `mcp` Python SDK，可以复用 `mcp_server/tools.py` 中的工具函数。

## 作用

MCP Server 用于把外部工具能力暴露给智能体或客户端。本项目通过 MCP 工具提供知识库统计、项目文件读取、SQLite 笔记查询和知识库检索能力。

## 支持工具

- `get_kb_stats`：读取 SQLite 和配置，返回文档数、chunk 数、向量库类型、embedding backend 和模型名。
- `read_project_file`：安全读取项目内 `.md`、`.txt`、`.json` 文件，禁止路径穿越。
- `query_notes`：按 title、content、tags 模糊查询 SQLite `notes` 表。
- `search_kb`：复用现有 RAG vector_store 检索能力，返回 Top-K chunk。

## 启动

先确保依赖已安装，并初始化数据库：

```bash
PYTHONPATH=backend python3 scripts/init_db.py
```

启动 HTTP fallback MCP-like 服务：

```bash
PYTHONPATH=backend uvicorn mcp_server.server:app --host 0.0.0.0 --port 9000
```

如果使用项目内 `.pyuser` 依赖：

```bash
PYTHONPATH=/home/jp/code/agent/.pyuser/lib/python3.12/site-packages:backend \
/home/jp/code/agent/.pyuser/bin/uvicorn mcp_server.server:app --host 0.0.0.0 --port 9000
```

## 测试工具

get_kb_stats：

```bash
curl http://localhost:9000/tools/get_kb_stats
```

read_project_file：

```bash
curl -X POST http://localhost:9000/tools/read_project_file \
  -H "Content-Type: application/json" \
  -d '{"path": "README.md"}'
```

query_notes：

```bash
curl -X POST http://localhost:9000/tools/query_notes \
  -H "Content-Type: application/json" \
  -d '{"keyword": "RAG"}'
```

search_kb：

```bash
curl -X POST http://localhost:9000/tools/search_kb \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG 和普通大模型问答有什么区别？", "top_k": 5}'
```

也可以运行：

```bash
python3 scripts/test_mcp_tools.py
```

## 简历价值

MCP 工具模块说明项目不只是一个普通 RAG 问答接口，还具备把知识库统计、文件读取、数据库查询和检索能力封装为工具的能力，能够体现智能体工具调用、外部系统连接和工程化扩展意识。
