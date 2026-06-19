from app.core.config import get_settings
from app.db.session import init_db
from app.llm.factory import get_llm_client
from app.rag.prompt import build_prompt
from app.rag.vector_store import chunk_count, search


class RAGChain:
    def answer(self, query: str, top_k: int | None = None) -> dict:
        init_db()
        settings = get_settings()
        if chunk_count() == 0:
            return {
                "answer": "知识库为空，请先上传文档并构建知识库。",
                "sources": [],
            }

        sources = search(query, top_k or settings.default_top_k)
        if not sources:
            return {
                "answer": "知识库中未找到相关信息",
                "sources": [],
            }

        context = "\n\n".join(
            f"[{index + 1}] 文件：{source.filename}\n{source.text}"
            for index, source in enumerate(sources)
        )
        prompt = build_prompt(query, context)
        try:
            answer = get_llm_client().generate(prompt, context=context, query=query)
        except Exception as exc:
            answer = f"模型调用失败：{exc}"
        references = []
        for source in sources:
            if source.filename not in references:
                references.append(source.filename)
        if references and "参考来源：" not in answer:
            refs = "\n".join(f"{index + 1}. {filename}" for index, filename in enumerate(references))
            answer = f"{answer}\n\n参考来源：\n{refs}"
        return {"answer": answer, "sources": [source.model_dump() for source in sources]}
