RAG_PROMPT_TEMPLATE = """你是一个专业的垂直领域知识库问答助手。
请严格根据【知识库内容】回答用户问题。
如果知识库内容不足以回答，请明确说明“知识库中未找到足够相关信息”，不要编造。

【知识库内容】
{context}

【用户问题】
{query}
"""


def build_prompt(query: str, context: str) -> str:
    return RAG_PROMPT_TEMPLATE.format(context=context, query=query)
