import hashlib
import math
import re
from collections import Counter
from functools import lru_cache

from app.core.config import get_settings


TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


class EmbeddingModel:
    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model_name
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers 未安装，无法使用真实 embedding。"
                "请执行 pip install -r requirements.txt，或设置 EMBEDDING_BACKEND=lightweight 使用轻量兜底。"
            ) from exc

        try:
            self.model = SentenceTransformer(self.model_name, device="cpu")
        except Exception as exc:
            raise RuntimeError(
                f"Embedding 模型加载失败：{self.model_name}。"
                "首次运行会从 Hugging Face 下载模型；如果下载较慢，可改用 "
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2，"
                "或临时设置 EMBEDDING_BACKEND=lightweight。"
            ) from exc

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [vector.tolist() for vector in vectors]

    def embed_query(self, query: str) -> list[float]:
        return self.embed_documents([query])[0]


class LightweightEmbeddingModel:
    """Deterministic fallback for tests or offline demos; not a semantic model."""

    dimensions = 384

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._embed(query)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            index = int(digest[:8], 16) % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


@lru_cache
def get_embedding_model():
    settings = get_settings()
    if settings.embedding_backend in {"lightweight", "mock", "fallback"}:
        return LightweightEmbeddingModel()
    return EmbeddingModel(settings.embedding_model_name)


def tokenize(text: str) -> list[str]:
    raw_tokens = TOKEN_RE.findall(text.lower())
    tokens: list[str] = []
    for token in raw_tokens:
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            tokens.extend(_char_ngrams(token))
        else:
            tokens.append(token)
    return tokens


def embed_text(text: str) -> dict[str, float]:
    counts = Counter(tokenize(text))
    norm = math.sqrt(sum(value * value for value in counts.values()))
    if norm == 0:
        return {}
    return {key: value / norm for key, value in counts.items()}


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def vector_cosine(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _char_ngrams(text: str) -> list[str]:
    chars = list(text)
    if len(chars) <= 2:
        return chars
    grams = chars[:]
    grams.extend("".join(chars[index : index + 2]) for index in range(len(chars) - 1))
    return grams
